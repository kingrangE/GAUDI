"""Tests for startup auto-seeding (`seed_if_empty`).

Auto-seed must populate a fresh DB but stay a no-op (non-destructive) once the
problems table is populated — it must never wipe or duplicate on restart.
"""

import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.features.coding_test.models  # noqa: F401  (register tables on Base)
from app.db.base import Base
from app.features.coding_test.models import Problem
from app.features.coding_test.problems import PROBLEMS
from app.scripts import seed_problems


@pytest_asyncio.fixture
async def seed_sessionmaker(monkeypatch):
    """Point `seed_if_empty` at a fresh in-memory DB instead of the real one."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(seed_problems, "AsyncSessionLocal", sessionmaker)
    yield sessionmaker
    await engine.dispose()


async def _problem_count(sessionmaker) -> int:
    async with sessionmaker() as db:
        return await db.scalar(select(func.count()).select_from(Problem))


async def test_seeds_an_empty_db(seed_sessionmaker):
    added = await seed_problems.seed_if_empty()

    assert added == len(PROBLEMS)
    assert await _problem_count(seed_sessionmaker) == len(PROBLEMS)


async def test_is_noop_when_already_populated(seed_sessionmaker):
    assert await seed_problems.seed_if_empty() == len(PROBLEMS)

    # Re-running must not duplicate rows or delete anything.
    assert await seed_problems.seed_if_empty() == 0
    assert await _problem_count(seed_sessionmaker) == len(PROBLEMS)
