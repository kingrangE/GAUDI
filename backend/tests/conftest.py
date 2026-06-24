"""Shared test fixtures: in-memory SQLite + an ASGI client with the DB override.

The whole unit suite runs with no Postgres and no OPENAI_API_KEY (matching CI):
the DB is an in-memory SQLite shared across connections via StaticPool, and LLM
calls are mocked per test. The OpenAI client is lazy, so importing the app never
needs a key.
"""

import os

# Isolate the unit suite from a real backend/.env key. The central config now reliably
# reads backend/.env (absolute path), so without this the suite could pick up a real
# OPENAI_API_KEY and fire live API calls / flip integration-test skip guards. setdefault:
# if a developer exports a real key, it wins and the gated integration tests run.
os.environ.setdefault("OPENAI_API_KEY", "")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.features.coding_test.models  # noqa: E402, F401  (register tables on Base)
import app.features.cs_eval.models  # noqa: E402, F401  (register tables on Base)
import app.features.mock_exam.models  # noqa: E402, F401  (register tables on Base)
import app.features.office_prompting.models  # noqa: E402, F401  (register tables on Base)
import app.features.rejection_eval.models  # noqa: E402, F401  (register tables on Base)
from app.db.base import Base  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.features.test_design import models as _test_design_models  # noqa: E402, F401
from app.features.test_design import services  # noqa: E402
from app.features.test_design.schemas import JudgeMatch, JudgeOutput  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def client(engine):
    test_session = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with test_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_judge(monkeypatch):
    """Patch the LLM judge with a deterministic stub: matches the FIRST ground-truth
    flaw (via candidate flaw 0, quality 2), misses the rest, flags any other
    candidate flaws as false positives."""

    async def fake_judge(problem, flaws):
        matches = []
        for i, flaw in enumerate(problem.flaws):
            if i == 0:
                matches.append(
                    JudgeMatch(
                        ground_truth_id=flaw.id,
                        matched=True,
                        candidate_index=0,
                        quality=2,
                    )
                )
            else:
                matches.append(
                    JudgeMatch(
                        ground_truth_id=flaw.id,
                        matched=False,
                        candidate_index=None,
                        quality=0,
                    )
                )
        fp = [j for j in range(len(flaws)) if j != 0]
        return JudgeOutput(matches=matches, false_positive_indices=fp, report="stub report")

    monkeypatch.setattr(services, "judge_submission", fake_judge)
    return fake_judge
