"""RQ job target for grading a submission.

RQ jobs are synchronous; this bridges to the async grading service by opening a
fresh DB session and driving it with ``asyncio.run``. A real subprocess runner
is used here (the worker is the production execution path).
"""

import asyncio

from app.db.session import AsyncSessionLocal
from app.features.coding_test import grading
from app.features.coding_test.runner import SubprocessCodeRunner


async def _grade(submission_id: str) -> None:
    runner = SubprocessCodeRunner()
    async with AsyncSessionLocal() as db:
        await grading.grade_submission(db, submission_id, runner)


def grade_submission(submission_id: str) -> None:
    """Entry point referenced by `queue.enqueue(...)`."""
    asyncio.run(_grade(submission_id))
