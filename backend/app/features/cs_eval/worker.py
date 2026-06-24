"""RQ job entry point for CS-eval grading (used only in `grading_mode=rq`).

The job is synchronous (RQ workers are sync); it opens a fresh DB session and
bridges to the async grading via `asyncio.run`. The shared `backend/worker.py`
RQ worker listens on the same "grading" queue and dispatches by function path,
so no separate worker process is needed.
"""

import asyncio

from app.db.session import AsyncSessionLocal
from app.features.cs_eval import grading


async def _grade(session_id: str) -> None:
    async with AsyncSessionLocal() as db:
        await grading.grade_session(db, session_id)


def grade_session(session_id: str) -> None:
    """Entry point referenced by `queue.enqueue(...)`."""
    asyncio.run(_grade(session_id))
