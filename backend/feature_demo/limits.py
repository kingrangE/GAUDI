"""Atomic admission and feature attempts. Monetary amounts are integer nano-USD."""

from datetime import datetime, timezone
from decimal import ROUND_CEILING, Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from feature_demo.models import DemoAttempt, DemoBudget, DemoJob, DemoSession, DemoSlot, DemoStep


def enabled() -> bool:
    cfg = get_settings()
    return cfg.demo_enabled and cfg.demo_limits_enabled


def insert(db, model):
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as statement
    elif db.bind.dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as statement
    else:
        raise RuntimeError("unsupported demo policy database")
    return statement(model)


async def gate(db: AsyncSession) -> DemoBudget:
    today = datetime.now(timezone.utc).date().isoformat()
    await db.execute(insert(db, DemoBudget).values(id="global", day=today).on_conflict_do_nothing())
    await db.execute(
        update(DemoBudget).where(DemoBudget.id == "global").values(revision=DemoBudget.revision + 1)
    )
    budget = await db.get(DemoBudget, "global", populate_existing=True)
    if budget.day != today:
        # Carry reservations and in-flight exposure across midnight; only settled spend resets.
        budget.day, budget.spent = today, 0
    return budget


def price(model: str) -> tuple[int, int]:
    rates = get_settings().demo_model_prices.get(model, {})
    try:
        values = [Decimal(rates[key]) for key in ("input", "output")]
        if any(not value.is_finite() or value <= 0 for value in values):
            raise ValueError("invalid price")
        return tuple(
            int((value * 1000).to_integral_value(rounding=ROUND_CEILING)) for value in values
        )
    except (KeyError, ValueError, TypeError, InvalidOperation):
        raise HTTPException(
            status_code=503, detail="demo model prices are not configured"
        ) from None


def call_limit(feature: str) -> int:
    from app.features.cs_eval.questions import QUESTIONS
    from app.features.office_prompting.problems import PROBLEM_COUNT
    from app.features.rejection_eval.topics import TOPIC_COUNT
    from app.features.test_design.problems import PROBLEMS

    cfg = get_settings()
    counts = {
        "context_engineering": 4,
        "spec_design": cfg.spec_samples * 2,
        "dev_prompting": 20,
        "coding_test": 1,
        "cs_eval": len(QUESTIONS) + 1,
        "office_prompting": PROBLEM_COUNT * 3,
        "rejection_eval": TOPIC_COUNT * 3,
        "test_design": len(PROBLEMS),
        "mock_exam": 4 + cfg.spec_samples * 2 + 3 + 1 + 20,
    }
    return counts[feature] * (cfg.demo_job_retry_limit + 1)


def attempt_cost(feature: str) -> int:
    cfg = get_settings()
    models = {cfg.solver_model, cfg.llm_model, cfg.spec_gen_model, cfg.spec_judge_model}
    rates = [price(model) for model in models]
    return call_limit(feature) * (
        cfg.demo_max_input_tokens * max(r[0] for r in rates)
        + cfg.demo_max_output_tokens * max(r[1] for r in rates)
    )


def identity(body, digest: str) -> tuple[str, str] | None:
    feature, action = body.feature, body.action
    raw = body.input.model_dump()
    params, data = raw.get("params", {}), raw.get("body", raw)
    if action == "create_run" or (action == "create_session" and feature != "cs_eval"):
        return None
    if feature == "mock_exam":
        root = params.get("attempt_id", "pending")
        step = f"{action}:{params.get('feature_key', '')}"
        if action == "run_dev_turn":
            step = f"turn:{data['turn']}"
        elif action == "generate_rejection_items":
            step = f"generate:{digest}"
        return root, step
    if feature in {"context_engineering", "spec_design", "cs_eval"} or action == "evaluate":
        return digest, "evaluate"
    root = params.get("session_id") or params.get("run_id") or params.get("problem_id")
    if feature == "coding_test":
        root = root or data["problem_id"]
        return root, "submit" if action == "create_submission" else f"run:{digest}"
    if action == "next_turn":
        return root, f"turn:{data['turn']}"
    index = params.get("problem_index", params.get("topic_index", ""))
    if action in {"generate", "run"}:
        return root, f"{action}:{index}:{digest}"
    return root, f"{action}:{index}"


async def expire_attempts(db, budget):
    now = datetime.now(timezone.utc)
    for attempt in await db.scalars(
        select(DemoAttempt).where(
            DemoAttempt.closed.is_(False),
            DemoAttempt.expires_at <= now,
        )
    ):
        jobs = select(DemoJob.id).where(
            DemoJob.session_id == attempt.session_id, DemoJob.feature == attempt.feature
        )
        busy = await db.scalar(
            select(func.count())
            .select_from(DemoJob)
            .where(DemoJob.id.in_(jobs), DemoJob.status.in_(["queued", "running"]))
        )
        held = await db.scalar(
            select(func.count()).select_from(DemoSlot).where(DemoSlot.job_id.in_(jobs))
        )
        if not busy and not held:
            budget.reserved -= attempt.remaining
            attempt.remaining, attempt.closed = 0, True


async def admit(db, owner_id, body, digest, budget):
    """Caller commits this transaction together with the job and logical step."""
    if body.feature == "dev_prompting" and body.action == "evaluate":
        if len(body.input.body["prompts"]) > 20:
            raise HTTPException(
                status_code=422, detail="demo supports at most 20 development turns"
            )
    await expire_attempts(db, budget)
    chosen = identity(body, digest)
    attempt = step = None
    if chosen is not None:
        root, logical = chosen
        if body.feature == "office_prompting" and body.action == "run":
            from app.features.office_prompting.models import OfficeAttempt

            native = await db.scalar(
                select(OfficeAttempt).where(
                    OfficeAttempt.session_id == root,
                    OfficeAttempt.problem_index == body.input.params["problem_index"],
                )
            )
            run_number = len(native.runs or []) if native else 0
            logical = f"run:{body.input.params['problem_index']}:{run_number}"
        attempt = await db.scalar(
            select(DemoAttempt).where(
                DemoAttempt.session_id == owner_id, DemoAttempt.feature == body.feature
            )
        )
        if attempt is not None and body.action in {"generate", "generate_rejection_items"}:
            prefix = logical.rsplit(":", 1)[0] + ":"
            previous = list(
                await db.scalars(
                    select(DemoStep)
                    .where(DemoStep.attempt_id == attempt.id, DemoStep.key.startswith(prefix))
                    .order_by(DemoStep.key)
                )
            )
            number = len(previous)
            if previous:
                last = await db.get(DemoJob, previous[-1].job_id)
                if last.status != "completed":
                    number -= 1
            logical = f"{prefix}{number}"
        elif attempt is None and body.action in {"generate", "generate_rejection_items"}:
            logical = logical.rsplit(":", 1)[0] + ":0"
        if attempt is not None:
            step = await db.get(DemoStep, (attempt.id, logical))
            if step:
                old = await db.get(DemoJob, step.job_id)
                if step.digest != digest:
                    raise HTTPException(status_code=409, detail="accepted demo input is immutable")
                if old.status != "failed":
                    return old, attempt, step, logical
                if step.retries >= get_settings().demo_job_retry_limit:
                    raise HTTPException(status_code=429, detail="demo retry allowance exhausted")
            if attempt.root != root:
                raise HTTPException(
                    status_code=409, detail="this feature already has a demo attempt"
                )
            if attempt.closed:
                raise HTTPException(
                    status_code=409, detail="this feature demo is already completed"
                )
        else:
            reserved = attempt_cost(body.feature)
            maximum = int(get_settings().demo_daily_budget_usd * 1_000_000_000)
            if maximum <= 0:
                raise HTTPException(status_code=503, detail="demo daily budget is not configured")
            if budget.reserved + budget.inflight + budget.spent + reserved > maximum:
                raise HTTPException(status_code=429, detail="demo daily budget is exhausted")
            visitor = await db.get(DemoSession, owner_id)
            attempt = DemoAttempt(
                session_id=owner_id,
                feature=body.feature,
                root=root,
                remaining=reserved,
                max_calls=call_limit(body.feature),
                expires_at=visitor.expires_at,
            )
            db.add(attempt)
            budget.reserved += reserved
            await db.flush()
        if body.action in {"generate", "generate_rejection_items", "run"} and step is None:
            prefix = logical.rsplit(":", 1)[0] + ":"
            maximum = (
                2
                if body.action in {"generate", "generate_rejection_items"}
                else (get_settings().demo_max_sample_runs if body.feature == "coding_test" else 3)
            )
            count = await db.scalar(
                select(func.count())
                .select_from(DemoStep)
                .where(DemoStep.attempt_id == attempt.id, DemoStep.key.startswith(prefix))
            )
            if count >= maximum:
                raise HTTPException(status_code=429, detail="demo execution allowance exhausted")
    cfg = get_settings()
    queued = await db.scalar(
        select(func.count()).select_from(DemoJob).where(DemoJob.status == "queued")
    )
    owned = await db.scalar(
        select(func.count())
        .select_from(DemoJob)
        .where(DemoJob.session_id == owner_id, DemoJob.status.in_(["queued", "running"]))
    )
    same_feature = await db.scalar(
        select(func.count())
        .select_from(DemoJob)
        .where(
            DemoJob.session_id == owner_id,
            DemoJob.feature == body.feature,
            DemoJob.status.in_(["queued", "running"]),
        )
    )
    if same_feature or queued >= cfg.demo_max_pending_jobs or owned >= cfg.demo_max_session_jobs:
        raise HTTPException(status_code=429, detail="demo queue is full; retry later")
    return None, attempt, step, logical if chosen else None


async def attach(db, job, attempt, step, logical):
    if attempt is None:
        return
    if step:
        step.job_id, step.retries = job.id, step.retries + 1
    else:
        db.add(DemoStep(attempt_id=attempt.id, key=logical, digest=job.input_hash, job_id=job.id))


async def finish_attempt(db, job, result):
    step = await db.scalar(select(DemoStep).where(DemoStep.job_id == job.id))
    if step is None:
        return
    budget = await gate(db)
    attempt = await db.get(DemoAttempt, step.attempt_id, populate_existing=True)
    if job.feature == "mock_exam" and job.action == "start":
        attempt.root = result["body"]["attempt_id"]
    terminal = job.feature in {"context_engineering", "spec_design", "cs_eval"} or (
        job.action in {"score", "finish", "create_submission", "evaluate"}
    )
    if terminal and not attempt.closed:
        budget.reserved -= attempt.remaining
        attempt.remaining, attempt.closed = 0, True
