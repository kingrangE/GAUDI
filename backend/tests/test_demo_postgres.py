"""Opt-in PostgreSQL verification in a disposable schema, never application tables."""

import os
from datetime import timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from feature_demo.models import DemoResource, DemoSession


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Set RUN_POSTGRES_TESTS=1")
async def test_postgres_demo_session_owner_renewal_and_expiry(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "demo_enabled", True)
    monkeypatch.setattr(settings, "demo_cookie_secure", False)
    schema = f"test_demo_{uuid4().hex}"
    admin_engine = create_async_engine(settings.database_url)
    engine = create_async_engine(
        settings.database_url, connect_args={"server_settings": {"search_path": schema}}
    )
    original_overrides = app.dependency_overrides.copy()
    try:
        async with admin_engine.begin() as conn:
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)

        async def database():
            async with maker() as db:
                yield db

        app.dependency_overrides[get_session] = database
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            visitor = (await client.post("/api/demo/session")).json()["session_id"]
            created = await client.post("/test-design/sessions", json={"candidate_name": "x"})
            assert created.status_code == 201
            native_id = created.json()["session_id"]
            async with maker() as db:
                owner = await db.get(DemoResource, ("test_design", native_id))
                assert owner.session_id == visitor
                session = await db.get(DemoSession, visitor)
                assert session.created_at.utcoffset().total_seconds() == 0
                assert session.expires_at.utcoffset().total_seconds() == 0
            renewed = await client.post("/api/demo/session")
            assert renewed.json()["session_id"] == visitor
            path = f"/test-design/sessions/{native_id}/result"
            assert (await client.get(path)).status_code == 200
            client.cookies.clear()
            assert (await client.post("/api/demo/session")).status_code == 200
            assert (await client.get(path)).status_code == 404
            async with maker() as db:
                sessions = list(await db.scalars(select(DemoSession)))
                for session in sessions:
                    session.expires_at = session.created_at - timedelta(seconds=1)
                await db.commit()
            assert (await client.get(path)).status_code == 401
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        await engine.dispose()
        async with admin_engine.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin_engine.dispose()
