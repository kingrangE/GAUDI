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
    migration = migration[migration.index("DO $$"):migration.index("COMMIT;")]
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                await connection.run_sync(Base.metadata.create_all)
                await connection.execute(text(
                    "ALTER TABLE coding_test_problems ALTER COLUMN created_at "
                    "TYPE timestamp USING created_at AT TIME ZONE 'UTC'"
                ))
                await connection.execute(text(
                    "INSERT INTO coding_test_problems "
                    "(id, title, description_md, function_name, starter_code, difficulty, "
                    "reference_solution, comparison, created_at) VALUES "
                    "('legacy', '', '', '', '', '', '', 'exact', '2026-10-29 12:09:13')"
                ))
                # A different session timezone must not shift legacy UTC timestamps.
                await connection.execute(text("SET LOCAL TIME ZONE 'Asia/Seoul'"))
                await connection.execute(text(migration))
                await connection.execute(text(migration))
                stamp = await connection.scalar(text(
                    "SELECT created_at FROM coding_test_problems WHERE id = 'legacy'"
                ))
                assert stamp.isoformat() == "2026-10-29T12:09:13+00:00"
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
