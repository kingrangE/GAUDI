"""RQ job target with a per-invocation engine, DB claim, and fenced result writes."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from feature_context_engineering.evaluate import build_report
from feature_context_engineering.models import EvaluationReport
from feature_context_engineering.service import create_submission, get_project
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
    lease = uuid4().hex
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

    async def save_progress(phase: str, completed: int, total: int) -> None:
        if (
            total != 4
            or not 0 <= completed <= total
            or phase
            not in {
                "static_checks",
                "coverage",
                "boundary",
            }
        ):
            raise ValueError("invalid progress event")
        async with maker() as db:
            await db.execute(
                update(DemoJob)
                .where(
                    DemoJob.id == job_id,
                    DemoJob.status == "running",
                    DemoJob.lease == lease,
                    DemoJob.completed_units < completed,
                )
                .values(
                    phase=phase, completed_units=completed, updated_at=datetime.now(timezone.utc)
                )
            )
            await db.commit()

    loop = asyncio.get_running_loop()

    def progress(phase: str, completed: int, total: int) -> None:
        # Only the event loop opens DB sessions; evaluation threads never share an AsyncSession.
        asyncio.run_coroutine_threadsafe(save_progress(phase, completed, total), loop).result()

    try:
        if (feature, action) != ("context_engineering", "evaluate"):
            raise ValueError("unsupported persisted job")
        result = await asyncio.to_thread(evaluate_context, payload, progress)
        report = EvaluationReport.model_validate(result)
        if report.project_id != payload["project_id"] or not report.scored:
            raise ValueError("report does not match the accepted evaluation")
        result = report.model_dump(mode="json")
        values = dict(status="completed", phase="completed", completed_units=4, result=result)
    except Exception:
        # Provider messages can include prompts/keys. Persist only a public error code.
        values = dict(status="failed", phase="failed", error_code="evaluation_failed")
    async with maker() as db:
        await db.execute(
            update(DemoJob)
            .where(
                DemoJob.id == job_id,
                DemoJob.status == "running",
                DemoJob.lease == lease,
            )
            .values(
                **values,
                finished_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()


def execute(job_id: str) -> None:
    async def run():
        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        try:
            await run_job(job_id, async_sessionmaker(engine, expire_on_commit=False))
        finally:
            await engine.dispose()

    asyncio.run(run())
