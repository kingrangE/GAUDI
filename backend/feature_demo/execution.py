"""Server-only execution context; no HTTP header can grant worker privileges."""

import asyncio
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Execution:
    owner_id: str
    sessions: Any
    accepted_at: datetime
    loop: asyncio.AbstractEventLoop
    progress: Callable[[str, int, int], Awaitable[None]]
    job_id: str = ""
    lease: str = ""


execution: ContextVar[Execution | None] = ContextVar("demo_execution", default=None)


async def advance(phase: str, completed: int, total: int) -> None:
    active = execution.get()
    if active:
        await active.progress(phase, completed, total)


def advance_sync(phase: str, completed: int, total: int) -> None:
    active = execution.get()
    if active:
        asyncio.run_coroutine_threadsafe(
            active.progress(phase, completed, total), active.loop
        ).result()
