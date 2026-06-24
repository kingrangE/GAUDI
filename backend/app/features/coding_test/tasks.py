"""Grading dispatch seam.

`grading_mode` selects how grading runs without changing the service or API:
- "inline": run in-process (default; tests and no-broker setups).
- "rq": enqueue to an RQ worker via Redis (durable, async).

Either way the submission row carries the lifecycle `status`, so the client
polls for the result the same way.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.features.coding_test import grading
from app.features.coding_test.runner import CodeRunner


async def enqueue_grading(
    db: AsyncSession, submission_id: str, runner: CodeRunner
) -> None:
    if get_settings().grading_mode == "rq":
        # Imported lazily so the inline path never needs redis/rq installed-and-up.
        from app.queue import get_queue

        get_queue().enqueue(
            "app.features.coding_test.worker.grade_submission", submission_id
        )
        return
    await grading.grade_submission(db, submission_id, runner)
