"""Opt-in broker/SQL checks with isolated queue names, files, and PostgreSQL schemas."""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from threading import Event
from uuid import uuid4

import pytest
from redis import Redis
from rq import Queue, SimpleWorker
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from feature_demo.dispatch import enqueue
from feature_demo.jobs import CreateJob, accept_job
from feature_demo.models import DemoJob, DemoSession
from feature_demo.worker import execute, run_job

BODY = CreateJob(
    feature="context_engineering",
    action="evaluate",
    input={
        "project_id": "todo-api",
        "claude_md": "`app/main.py` and `make test`",
    },
)


async def seed(maker):
    async with maker() as db:
        visitor = DemoSession(
            token_hash=uuid4().hex, expires_at=(datetime.now(timezone.utc) + timedelta(hours=2))
        )
        db.add(visitor)
        await db.commit()
        return visitor.id


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Set RUN_POSTGRES_TESTS=1")
async def test_postgres_concurrent_acceptance_and_worker_claim(monkeypatch):
    from feature_demo import worker

    settings = get_settings()
    schema = f"test_demo_jobs_{uuid4().hex}"
    admin = create_async_engine(settings.database_url)
    engine = create_async_engine(
        settings.database_url, connect_args={"server_settings": {"search_path": schema}}
    )
    entered, release = Event(), Event()
    task = None
    try:
        async with admin.begin() as conn:
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)
        owner = await seed(maker)

        async def accept():
            async with maker() as db:
                return (await accept_job(db, owner, "same-key", BODY)).id

        first, second = await asyncio.gather(accept(), accept())
        assert first == second
        calls = []

        def evaluate(payload, progress):
            calls.append(payload)
            progress("static_checks", 2, 4)
            entered.set()
            assert release.wait(10)
            return {"project_id": "todo-api", "scored": True}

        monkeypatch.setattr(worker, "evaluate_context", evaluate)
        task = asyncio.create_task(run_job(first, maker))
        assert await asyncio.to_thread(entered.wait, 10)
        await run_job(first, maker)
        async with maker() as db:
            job = await db.get(DemoJob, first)
            assert job.status == "running" and job.completed_units == 2
        release.set()
        await task
        assert len(calls) == 1
        async with maker() as db:
            jobs = list(await db.scalars(select(DemoJob)))
            assert len(jobs) == 1
            assert jobs[0].status == "completed"
            assert jobs[0].finished_at.utcoffset().total_seconds() == 0
    finally:
        release.set()
        if task:
            await task
        await engine.dispose()
        async with admin.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin.dispose()


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_REDIS_TESTS") != "1", reason="Set RUN_REDIS_TESTS=1")
def test_real_rq_executes_saved_input_once_and_worker_handles_sequential_loops(
    tmp_path, monkeypatch
):
    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", f"sqlite+aiosqlite:///{tmp_path / 'jobs.db'}")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    async def setup():
        engine = create_async_engine(settings.database_url)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            maker = async_sessionmaker(engine, expire_on_commit=False)
            owner = await seed(maker)
            async with maker() as db:
                job = await accept_job(db, owner, "request", BODY)
                return job.id
        finally:
            await engine.dispose()

    native_id = asyncio.run(setup())
    connection = Redis.from_url(settings.redis_url)
    queue = Queue(f"test-demo-{uuid4().hex}", connection=connection)
    try:
        enqueue(queue, native_id)
        enqueue(queue, native_id)
        assert queue.count == 1
        broker_job = queue.fetch_job(f"demo-{native_id}")
        assert broker_job.args == (native_id,)
        SimpleWorker([queue], connection=connection).work(burst=True, logging_level="WARNING")
        assert broker_job.get_status() == "finished"
        # A second asyncio.run uses a new engine, including repeated deliveries after completion.
        execute(native_id)

        async def check():
            engine = create_async_engine(settings.database_url)
            try:
                async with async_sessionmaker(engine)() as db:
                    job = await db.get(DemoJob, native_id)
                    assert job.status == "completed"
                    assert job.result["project_id"] == "todo-api"
                    assert job.result["scored"] is True
            finally:
                await engine.dispose()

        asyncio.run(check())
    finally:
        queue.delete(delete_jobs=True)
        connection.close()
