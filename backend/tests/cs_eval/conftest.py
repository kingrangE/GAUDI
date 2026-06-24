"""Fixtures for CS-eval endpoint tests.

Provides a client backed by an in-memory SQLite DB seeded with the real
questions. PR-A's judge is the deterministic keyword-overlap stub, so endpoint
tests stay fully offline with no LLM and no monkeypatching needed.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.features.cs_eval.models  # noqa: F401  (register tables on Base)
from app.db.base import Base
from app.db.session import get_session
from app.features.cs_eval.questions import QUESTIONS
from app.main import app
from app.scripts.seed_cs_questions import _upsert


@pytest_asyncio.fixture
async def cs_client():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as db:
        for seed in QUESTIONS:
            await _upsert(db, seed)
        await db.commit()

    async def override_get_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
