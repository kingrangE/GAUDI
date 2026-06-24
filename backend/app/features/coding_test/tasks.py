"""Grading dispatch seam.

PR-A runs grading inline (in-process). PR-B swaps the body for an RQ enqueue
(`get_queue().enqueue(...)`) selected by `settings.grading_mode`, without
changing the service or API. The async-polling contract holds either way: the
submission row carries the lifecycle `status`, and the client polls for it.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.coding_test import grading
from app.features.coding_test.runner import CodeRunner


async def enqueue_grading(
    db: AsyncSession, submission_id: str, runner: CodeRunner
) -> None:
    await grading.grade_submission(db, submission_id, runner)
