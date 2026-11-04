"""RQ job target with a per-invocation engine, DB claim, and fenced result writes."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from feature_context_engineering.evaluate import build_report
from feature_context_engineering.models import EvaluationReport
from feature_context_engineering.service import create_submission, get_project
from feature_demo.execution import Execution, execution
from feature_demo.models import DemoJob, DemoSession
from llm.client import get_llm_client
from llm.config import get_settings as get_llm_settings


def evaluate_context(payload: dict, progress) -> dict:
    submission = create_submission(**payload)
    settings = get_llm_settings()
    client = get_llm_client(settings) if settings.api_key else None
    report = build_report(
        get_project(submission.project_id), submission, client, on_progress=progress
    )
    return EvaluationReport.model_validate(report).model_dump(mode="json")


async def run_job(job_id: str, maker: async_sessionmaker) -> None:
    from feature_demo import limits, slots

    slot = None
    lease = uuid4().hex
    if limits.enabled():
        slot = await slots.acquire(maker, "evaluation", job_id, lease)
    try:
        task = asyncio.create_task(_run_job(job_id, maker, lease))
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            # Shielding alone is insufficient: wait for actual threads and containers to finish.
            await task
            raise
    finally:
        if slot is not None:
            await slots.release(maker, "evaluation", slot, lease)


async def _run_job(job_id: str, maker: async_sessionmaker, lease: str) -> None:
    now = datetime.now(timezone.utc)
    async with maker() as db:
        owner_alive = (
            select(DemoSession.id)
            .where(
                DemoSession.id == DemoJob.session_id,
                DemoSession.expires_at > now,
            )
            .exists()
        )
        claimed = await db.execute(
            update(DemoJob)
            .where(
                DemoJob.id == job_id,
                DemoJob.status == "queued",
                owner_alive,
            )
            .values(
                status="running",
                dispatch_status="enqueued",
                phase="evaluating",
                lease=lease,
                started_at=now,
                updated_at=now,
            )
        )
        await db.commit()
        if not claimed.rowcount:
            await db.execute(
                update(DemoJob)
                .where(
                    DemoJob.id == job_id,
                    DemoJob.status == "queued",
                    ~owner_alive,
                )
                .values(
                    status="failed",
                    phase="failed",
                    error_code="session_expired",
                    finished_at=now,
                    updated_at=now,
                )
            )
            await db.commit()
            return
        job = await db.get(DemoJob, job_id)
        feature, action, payload = job.feature, job.action, job.payload
        owner_id, accepted_at = job.session_id, job.created_at

    async def save_progress(phase: str, completed: int, total: int) -> None:
        if total <= 0 or not 0 <= completed <= total or not phase or len(phase) > 40:
            raise ValueError("invalid progress event")
        async with maker() as db:
            await db.execute(
                update(DemoJob)
                .where(
                    DemoJob.id == job_id,
                    DemoJob.status == "running",
                    DemoJob.lease == lease,
                    DemoJob.completed_units <= completed,
                )
                .values(
                    phase=phase,
                    completed_units=completed,
                    total_units=total,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()

    loop = asyncio.get_running_loop()

    def progress(phase: str, completed: int, total: int) -> None:
        # Only the event loop opens DB sessions; evaluation threads never share an AsyncSession.
        asyncio.run_coroutine_threadsafe(save_progress(phase, completed, total), loop).result()

    token = execution.set(
        Execution(owner_id, maker, accepted_at, loop, save_progress, job_id, lease)
    )
    try:
        if (feature, action) == ("context_engineering", "evaluate"):
            result = await asyncio.to_thread(evaluate_context, payload, progress)
            report = EvaluationReport.model_validate(result)
            if report.project_id != payload["project_id"] or not report.scored:
                raise ValueError("report does not match the accepted evaluation")
            result = report.model_dump(mode="json")
        else:
            result = await execute_native(feature, action, payload)
        values = dict(status="completed", phase="completed", result=result)
    except NativeRejected as exc:
        values = dict(
            status="failed",
            phase="failed",
            error_code="request_rejected",
            result={"status_code": exc.status},
        )
    except HTTPException as exc:
        values = dict(
            status="failed",
            phase="failed",
            error_code="request_rejected",
            result={"status_code": exc.status_code},
        )
    except Exception:
        # Provider messages can include prompts/keys. Persist only a public error code.
        values = dict(status="failed", phase="failed", error_code="evaluation_failed")
    finally:
        execution.reset(token)
    async with maker() as db:
        from feature_demo import limits

        if limits.enabled():
            from feature_demo.meter import close_inflight

            await close_inflight(db, job_id)
        if limits.enabled() and values["status"] == "completed":
            current = await db.get(DemoJob, job_id, populate_existing=True)
            if current.status == "running" and current.lease == lease:
                await limits.finish_attempt(db, current, result)
        await db.execute(
            update(DemoJob)
            .where(
                DemoJob.id == job_id,
                DemoJob.status == "running",
                DemoJob.lease == lease,
            )
            .values(
                **values,
                completed_units=DemoJob.total_units
                if values["status"] == "completed"
                else DemoJob.completed_units,
                finished_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()


class NativeRejected(Exception):
    def __init__(self, status: int):
        self.status = status


async def execute_native(feature: str, action: str, payload: dict) -> dict:
    import httpx

    from app.main import app
    from feature_demo.operations import operation_for

    operation = operation_for(feature, action)
    data = operation.validate(payload)
    path = operation.path.format(**data.params)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://worker.internal"
    ) as client:
        response = await client.post(path, json=data.body)
    if not response.is_success:
        raise NativeRejected(response.status_code)
    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("invalid native evaluation result")
    active = execution.get()
    if feature in {"coding_test", "cs_eval"} and action in {"create_submission", "create_session"}:
        from app.features.coding_test.models import Submission
        from app.features.cs_eval.models import CsSession

        model, key = (
            (Submission, "submission_id") if feature == "coding_test" else (CsSession, "session_id")
        )
        async with active.sessions() as db:
            native = await db.get(model, result[key])
            if native is None or native.status != "graded":
                raise NativeRejected(503)
    return {"http_status": response.status_code, "body": result}


def execute(job_id: str) -> None:
    async def run():
        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        try:
            await run_job(job_id, async_sessionmaker(engine, expire_on_commit=False))
        finally:
            await engine.dispose()

    asyncio.run(run())
