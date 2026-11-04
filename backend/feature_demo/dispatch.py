"""Redis delivery is recoverable; the DB claim prevents duplicate evaluation."""

import asyncio
from datetime import datetime, timezone

from redis.exceptions import RedisError
from rq import Queue
from rq.exceptions import DuplicateJobError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.queue import get_demo_queue
from feature_demo.models import DemoJob


def enqueue(queue: Queue, job_id: str) -> None:
    try:
        queue.enqueue(
            "feature_demo.worker.execute",
            job_id,
            job_id=f"demo-{job_id}",
            unique=True,
            job_timeout=get_settings().demo_job_timeout_seconds,
            result_ttl=86400,
            failure_ttl=86400,
            description=f"demo-{job_id}",
        )
    except DuplicateJobError:
        # Lost Redis acknowledgement or concurrent recovery: retain the existing delivery.
        pass


async def dispatch_job(db: AsyncSession, job: DemoJob) -> None:
    if job.status != "queued":
        return
    try:
        await asyncio.to_thread(enqueue, get_demo_queue(), job.id)
        state = "enqueued"
    except (RedisError, OSError):
        state = "error"
    await db.execute(
        update(DemoJob)
        .where(
            DemoJob.id == job.id,
            DemoJob.status == "queued",
        )
        .values(dispatch_status=state, updated_at=datetime.now(timezone.utc))
    )
    await db.commit()
    await db.refresh(job)


async def recover_jobs(db: AsyncSession, after: str | None = None) -> dict:
    """Explicit admin recovery; never restart a job that may have executed an LLM call."""
    rows = list(
        await db.scalars(
            select(DemoJob)
            .where(DemoJob.status.in_(["queued", "running"]), DemoJob.id > (after or ""))
            .order_by(DemoJob.id)
            .limit(100)
        )
    )
    dispatched = failed = unresolved = 0
    queue = get_demo_queue()
    for job in rows:
        broker_job = await asyncio.to_thread(queue.fetch_job, f"demo-{job.id}")
        status = await asyncio.to_thread(broker_job.get_status) if broker_job else None
        if status in {"failed", "stopped", "canceled", "finished"}:
            result = await db.execute(
                update(DemoJob)
                .where(
                    DemoJob.id == job.id,
                    DemoJob.status == job.status,
                    DemoJob.lease == job.lease,
                )
                .values(
                    status="failed",
                    phase="failed",
                    error_code="worker_interrupted",
                    finished_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
            failed += result.rowcount
        elif job.status == "queued" and broker_job is None:
            await dispatch_job(db, job)
            dispatched += int(job.dispatch_status == "enqueued")
        else:
            unresolved += 1
    return {
        "dispatched": dispatched,
        "failed": failed,
        "unresolved": unresolved,
        "next_cursor": rows[-1].id if len(rows) == 100 else None,
    }
