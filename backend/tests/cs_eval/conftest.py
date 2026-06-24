"""Fixtures for CS-eval tests.

`cs_client` serves the endpoints over an in-memory SQLite DB seeded with the
real questions, with the LLM judge swapped for a deterministic keyword-overlap
stub (`scoring.classify`) so endpoint tests stay fully offline. `cs_db` exposes a
seeded sessionmaker for grading/dispatch tests.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.features.cs_eval.models  # noqa: F401  (register tables on Base)
from app.db.base import Base
from app.db.session import get_session
from app.features.cs_eval import grading, scoring
from app.features.cs_eval.judge import AnswerJudgement, SessionReports
from app.features.cs_eval.questions import QUESTIONS
from app.main import app
from app.scripts.seed_cs_questions import _upsert


async def _stub_judge_answer(
    *, domain, prompt_md, reference_answer, rubric, answer_text
) -> AnswerJudgement:
    """Deterministic stand-in for the LLM judge (same classify the LLM refines)."""
    key_points = list((rubric or {}).get("key_points", []))
    response_type, matched, missing, partial = scoring.classify(answer_text, key_points)
    return AnswerJudgement(
        response_type=response_type,
        score=scoring.score_for_type(response_type, partial),
        matched_keywords=matched,
        missing_keywords=missing,
        rationale="stub",
    )


async def _stub_synthesize(*, per_question) -> SessionReports:
    missing = [kw for q in per_question for kw in (q.get("missing_keywords") or [])]
    deduped = list(dict.fromkeys(missing))
    summary = "보완이 필요한 키워드: " + ", ".join(deduped) if deduped else "충분"
    analysis = "stub analysis " + " ".join(q["domain"] for q in per_question)
    return SessionReports(summary_report=summary, analysis_report=analysis)


async def _seed(session_maker) -> None:
    async with session_maker() as db:
        for seed in QUESTIONS:
            await _upsert(db, seed)
        await db.commit()


@pytest_asyncio.fixture
async def cs_client(monkeypatch):
    monkeypatch.setattr(grading, "judge_answer", _stub_judge_answer)
    monkeypatch.setattr(grading, "synthesize_reports", _stub_synthesize)

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    await _seed(session_maker)

    async def override_get_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def cs_db():
    """A seeded in-memory sessionmaker for grading/dispatch tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    await _seed(session_maker)
    yield session_maker
    await engine.dispose()
