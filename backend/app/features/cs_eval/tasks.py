"""Grading dispatch seam (mirrors coding_test).

`grading_mode` selects how grading runs without changing the service or API:
- "inline": run in-process (default; tests and no-broker setups).
- "rq": enqueue to an RQ worker via Redis (durable, async).

Either way the session row carries the lifecycle `status`, so the client polls
for the result the same way.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.features.cs_eval import grading


async def enqueue_grading(db: AsyncSession, session_id: str) -> None:
    if get_settings().grading_mode == "rq":
        # Imported lazily so the inline path never needs redis/rq installed-and-up.
        from app.queue import get_queue

        get_queue().enqueue("app.features.cs_eval.worker.grade_session", session_id)
        return
    await grading.grade_session(db, session_id)
