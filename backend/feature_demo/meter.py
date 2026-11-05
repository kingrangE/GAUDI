"""Reserve before provider I/O; missing/ambiguous usage is charged pessimistically."""

import asyncio
import json

from fastapi import HTTPException
from sqlalchemy import select

from app.core.config import get_settings
from feature_demo.execution import execution
from feature_demo.limits import enabled, gate, price
from feature_demo.models import DemoAttempt, DemoCall, DemoJob, DemoStep


async def reserve(model: str, messages: list, schema: dict | None, output_limit: int) -> str | None:
    if not enabled():
        return None
    active = execution.get()
    if active is None or not active.job_id:
        raise HTTPException(status_code=403, detail="demo LLM calls require a reserved job")
    cfg = get_settings()
    # UTF-8 bytes conservatively bound the text tokens, including schema and framing allowance.
    bound = len(json.dumps(messages, ensure_ascii=False).encode()) + 1024
    if schema:
        bound += len(json.dumps(schema, ensure_ascii=False).encode())
    if bound > cfg.demo_max_input_tokens:
        raise HTTPException(
            status_code=413, detail="demo input exceeds the configured token allowance"
        )
    input_rate, output_rate = price(model)
    upper = cfg.demo_max_input_tokens * input_rate + output_limit * output_rate
    async with active.sessions() as db:
        budget = await gate(db)
        job = await db.get(DemoJob, active.job_id, populate_existing=True)
        step = await db.scalar(select(DemoStep).where(DemoStep.job_id == active.job_id))
        if job is None or job.status != "running" or job.lease != active.lease or step is None:
            raise HTTPException(status_code=409, detail="demo execution lease is no longer valid")
        attempt = await db.get(DemoAttempt, step.attempt_id, populate_existing=True)
        if attempt.closed or attempt.calls >= attempt.max_calls or attempt.remaining < upper:
            raise HTTPException(status_code=429, detail="demo call allowance exhausted")
        attempt.calls += 1
        attempt.remaining -= upper
        budget.reserved -= upper
        budget.inflight += upper
        call = DemoCall(
            attempt_id=attempt.id,
            job_id=job.id,
            model=model,
            reserved=upper,
            input_rate=input_rate,
            output_rate=output_rate,
        )
        db.add(call)
        await db.commit()
        return call.id


async def settle(call_id: str | None, usage, output_limit: int) -> None:
    if call_id is None:
        return
    active = execution.get()
    async with active.sessions() as db:
        budget = await gate(db)
        call = await db.get(DemoCall, call_id, populate_existing=True)
        if call.state != "inflight":
            return
        attempt = await db.get(DemoAttempt, call.attempt_id, populate_existing=True)
        incoming = getattr(usage, "prompt_tokens", None)
        outgoing = getattr(usage, "completion_tokens", None)
        valid = (
            isinstance(incoming, int)
            and isinstance(outgoing, int)
            and (
                0 <= incoming <= get_settings().demo_max_input_tokens
                and 0 <= outgoing <= output_limit
            )
        )
        rates = call.input_rate, call.output_rate
        charged = (
            min(call.reserved, incoming * rates[0] + outgoing * rates[1])
            if valid
            else call.reserved
        )
        refund = call.reserved - charged
        budget.inflight -= call.reserved
        budget.spent += charged
        budget.reserved += refund
        attempt.remaining += refund
        attempt.spent += charged
        call.charged, call.state = charged, "settled" if valid else "unknown"
        if valid:
            call.input_tokens, call.output_tokens = incoming, outgoing
        await db.commit()


def sync(coroutine):
    active = execution.get()
    if active is None:
        # Only used for the protected sync provider path.
        coroutine.close()
        raise HTTPException(status_code=403, detail="demo LLM calls require a reserved job")
    return asyncio.run_coroutine_threadsafe(coroutine, active.loop).result()


async def close_inflight(db, job_id):
    """After local work ends, ambiguous calls retain their entire reserved exposure."""
    budget = await gate(db)
    for call in await db.scalars(
        select(DemoCall).where(DemoCall.job_id == job_id, DemoCall.state == "inflight")
    ):
        call.charged, call.state = call.reserved, "unknown"
        budget.inflight -= call.reserved
        budget.spent += call.reserved
        attempt = await db.get(DemoAttempt, call.attempt_id, populate_existing=True)
        attempt.spent += call.reserved
