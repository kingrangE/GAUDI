"""Fixtures for coding-test endpoint tests.

Provides a client backed by an in-memory SQLite DB seeded with the real
problems, with `service.runner` swapped for a faithful in-process runner so no
subprocess (and no LLM) runs in unit tests.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.features.coding_test.models  # noqa: F401  (register tables on Base)
from app.db.base import Base
from app.db.session import get_session
from app.features.coding_test import service
from app.features.coding_test.problems import PROBLEMS
from app.features.coding_test.runner import ExecResult
from app.main import app
from app.scripts.seed_problems import _upsert


class InProcessRunner:
    """Faithful, fast runner: execs candidate code and calls the function here.

    Same observable contract as SubprocessCodeRunner (returns an ExecResult)
    but in-process — deterministic and quick for endpoint tests.
    """

    def execute(self, code, function_name, args, timeout_s=5.0, mem_limit_mb=256):
        namespace: dict = {}
        try:
            exec(compile(code, "<test>", "exec"), namespace)
        except Exception as exc:  # noqa: BLE001
            return ExecResult(ok=False, error=f"exception: {type(exc).__name__}: {exc}")
        fn = namespace.get(function_name)
        if not callable(fn):
            return ExecResult(ok=False, error="missing_function")
        try:
            return ExecResult(ok=True, value=fn(*args))
        except Exception as exc:  # noqa: BLE001
            return ExecResult(ok=False, error=f"exception: {type(exc).__name__}: {exc}")


@pytest_asyncio.fixture
async def coding_client():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as db:
        for seed in PROBLEMS:
            await _upsert(db, seed)
        await db.commit()

    async def override_get_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    original_runner = service.runner
    service.runner = InProcessRunner()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    service.runner = original_runner
    app.dependency_overrides.clear()
    await engine.dispose()
