"""PostgreSQL must accept the UTC timestamps used by seeds and grading records."""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.features.coding_test.models import Problem, Submission
from app.features.cs_eval.models import CsQuestion, CsSession
from app.scripts import seed_cs_questions, seed_problems


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Set RUN_POSTGRES_TESTS=1 for local PostgreSQL"
)
async def test_postgres_seed_and_grading_timestamps(monkeypatch):
    engine = create_async_engine(get_settings().database_url)
    schema = f"test_timestamps_{uuid4().hex}"
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                await connection.run_sync(Base.metadata.create_all)
                sessions = async_sessionmaker(
                    connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
                )
                monkeypatch.setattr(seed_problems, "AsyncSessionLocal", sessions)
                monkeypatch.setattr(seed_cs_questions, "AsyncSessionLocal", sessions)

                assert await seed_problems.seed_if_empty() == 3
                assert await seed_cs_questions.seed_if_empty() == 4
                assert await seed_problems.seed_if_empty() == 0
                assert await seed_cs_questions.seed_if_empty() == 0

                async with sessions() as db:
                    submission = Submission(problem_id="two-sum", candidate_id="test", code="pass")
                    session = CsSession(candidate_id="test")
                    db.add_all([submission, session])
                    await db.flush()
                    submission.status = session.status = "done"
                    await db.flush()
                    await db.refresh(submission)
                    await db.refresh(session)
                    problem = await db.scalar(select(Problem).limit(1))
                    question = await db.scalar(select(CsQuestion).limit(1))
                    for record in (problem, question, submission, session):
                        assert record.created_at.utcoffset().total_seconds() == 0
                    for record in (submission, session):
                        assert record.updated_at.utcoffset().total_seconds() == 0
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Set RUN_POSTGRES_TESTS=1 for local PostgreSQL"
)
async def test_postgres_timestamp_migration_preserves_utc_and_is_repeatable():
    engine = create_async_engine(get_settings().database_url)
    schema = f"test_timestamps_{uuid4().hex}"
    migration = (
        Path(__file__).parents[1] / "app/scripts/migrate_postgres_timestamps.sql"
    ).read_text()
    # The test owns the transaction; run the same DO block without the CLI BEGIN/COMMIT.
    migration = migration[migration.index("DO $$") : migration.index("COMMIT;")]
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                await connection.run_sync(Base.metadata.create_all)
                await connection.execute(
                    text(
                        "ALTER TABLE coding_test_problems ALTER COLUMN created_at "
                        "TYPE timestamp USING created_at AT TIME ZONE 'UTC'"
                    )
                )
                await connection.execute(
                    text(
                        "INSERT INTO coding_test_problems "
                        "(id, title, description_md, function_name, starter_code, difficulty, "
                        "reference_solution, comparison, created_at) VALUES "
                        "('legacy', '', '', '', '', '', '', 'exact', '2026-10-29 12:09:13')"
                    )
                )
                # A different session timezone must not shift legacy UTC timestamps.
                await connection.execute(text("SET LOCAL TIME ZONE 'Asia/Seoul'"))
                await connection.execute(text(migration))
                await connection.execute(text(migration))
                stamp = await connection.scalar(
                    text("SELECT created_at FROM coding_test_problems WHERE id = 'legacy'")
                )
                assert stamp.isoformat() == "2026-10-29T12:09:13+00:00"
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Set RUN_POSTGRES_TESTS=1")
async def test_postgres_saved_exam_input_and_code_run_roundtrip():
    from app.features.mock_exam.models import ExamAttempt, ExamSubmission
    from feature_dev_prompting.sessions import DevRun

    engine = create_async_engine(get_settings().database_url)
    schema = f"test_exam_{uuid4().hex}"
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                await connection.run_sync(Base.metadata.create_all)
                await connection.run_sync(Base.metadata.create_all)
                maker = async_sessionmaker(
                    connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
                )
                async with maker() as db:
                    attempt = ExamAttempt(candidate_code="AY-7F3K9Q", candidate_label="test")
                    db.add(attempt)
                    await db.flush()
                    saved = ExamSubmission(
                        exam_attempt_id=attempt.id,
                        feature_key="spec_design",
                        payload={"instruction": "보존된 원본"},
                        status="failed",
                    )
                    run = DevRun(
                        exam_attempt_id=attempt.id,
                        problem_id="churn-risk-stream",
                        turns=[{"code": "def solution(): return 1"}],
                    )
                    db.add_all([saved, run])
                    await db.commit()
                    await db.refresh(saved)
                    await db.refresh(run)
                    assert saved.payload["instruction"] == "보존된 원본"
                    assert saved.accepted_at.utcoffset().total_seconds() == 0
                    assert run.updated_at.utcoffset().total_seconds() == 0
                    assert run.turns[0]["code"] == "def solution(): return 1"
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Set RUN_POSTGRES_TESTS=1")
async def test_postgres_concurrent_submit_finish_and_duplicate(monkeypatch):
    import asyncio

    from httpx import ASGITransport, AsyncClient

    from app.db.session import get_session
    from app.features.mock_exam import exam_router
    from app.main import app

    url = get_settings().database_url
    schema = f"test_concurrency_{uuid4().hex}"
    admin_engine = create_async_engine(url)
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    entered, release = asyncio.Event(), asyncio.Event()
    original_overrides = app.dependency_overrides.copy()
    try:
        async with admin_engine.begin() as conn:
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)

        async def database():
            async with maker() as session:
                yield session

        async def slow(*args):
            entered.set()
            await release.wait()
            return {"total": 100}

        app.dependency_overrides[get_session] = database
        app.dependency_overrides[exam_router.get_solver_client] = lambda: object()
        app.dependency_overrides[exam_router.get_context_client] = lambda: None
        monkeypatch.setattr(exam_router, "_score_step", slow)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            started = await client.post(
                "/api/mock-exam/start", json={"candidate_code": "AY-7F3K9Q"}
            )
            root = f"/api/mock-exam/attempts/{started.json()['attempt_id']}"
            submission = asyncio.create_task(
                client.post(root + "/steps/context_engineering/submit", json={"claude_md": "saved"})
            )
            await asyncio.wait_for(entered.wait(), 2)
            try:
                assert (await client.post(root + "/finish")).status_code == 409
                duplicate = await client.post(
                    root + "/steps/context_engineering/submit", json={"claude_md": "saved"}
                )
                assert duplicate.status_code == 409
                assert (await client.get(root)).status_code == 200
            finally:
                release.set()
                assert (await submission).status_code == 200
            assert (await client.post(root + "/finish")).status_code == 200
            late = await client.post(
                root + "/steps/context_engineering/submit", json={"claude_md": "changed"}
            )
            assert late.status_code == 409

            from feature_dev_prompting import sessions as dev_sessions
            from feature_dev_prompting.models import TurnResult

            generated = []

            def dev_turn(problem, turns, prompt, solver):
                generated.append(prompt)
                return TurnResult(
                    turn=len(turns) + 1,
                    prompt=prompt,
                    code="saved",
                    passed_count=0,
                    total=1,
                    solved=False,
                    feedback="",
                    case_results=[],
                )

            monkeypatch.setattr(dev_sessions, "execute_turn", dev_turn)
            other = await client.post("/api/mock-exam/start", json={"candidate_code": "AY-4M8X2P"})
            dev_path = f"/api/mock-exam/attempts/{other.json()['attempt_id']}/dev-run"
            for turn, prompt in [(1, "first"), (1, "first"), (2, "second")]:
                result = await client.post(dev_path, json={"turn": turn, "prompt": prompt})
                assert result.status_code == 200, result.text
            assert generated == ["first", "second"]
    finally:
        release.set()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        await engine.dispose()
        async with admin_engine.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin_engine.dispose()
