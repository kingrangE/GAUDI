"""Cookie authentication; candidate names and codes never establish ownership."""

from datetime import datetime, timezone
from hashlib import sha256

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from feature_demo.models import DemoResource, DemoSession

COOKIE_NAME = "gaudi_demo"


def token_hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in get_settings().cors_origin_list:
        raise HTTPException(status_code=403, detail="untrusted demo request origin")


async def find_session(request: Request, db: AsyncSession) -> DemoSession | None:
    token = request.cookies.get(COOKIE_NAME, "")
    if not 32 <= len(token) <= 128:
        return None
    return await db.scalar(
        select(DemoSession).where(
            DemoSession.token_hash == token_hash(token),
            DemoSession.expires_at > datetime.now(timezone.utc),
        )
    )


async def current_demo_session(
    request: Request, db: AsyncSession = Depends(get_session)
) -> DemoSession | None:
    if not get_settings().demo_enabled:
        return None
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        check_origin(request)
    visitor = await find_session(request, db)
    if visitor is None:
        raise HTTPException(status_code=401, detail="demo session missing or expired")
    return visitor


def protect_resources(kind: str):
    """Public material stays readable; every mutation and private ID requires a cookie."""

    async def protect(
        request: Request, response: Response, db: AsyncSession = Depends(get_session)
    ) -> None:
        if not get_settings().demo_enabled:
            return
        resource_id = next(
            (
                request.path_params[k]
                for k in ("session_id", "submission_id", "run_id", "attempt_id")
                if k in request.path_params
            ),
            None,
        )
        if resource_id is None and request.method in {"GET", "HEAD", "OPTIONS"}:
            return
        visitor = await current_demo_session(request, db)
        response.headers["Cache-Control"] = "no-store"
        if resource_id is not None:
            owner = await db.get(DemoResource, (kind, resource_id))
            if owner is None or owner.session_id != visitor.id:
                raise HTTPException(status_code=404, detail="resource not found")

    return protect


def bind_resource(db: AsyncSession, owner_id: str | None, kind: str, resource_id: str) -> None:
    """Persist the native resource and owner in the same creation transaction."""
    if owner_id is not None:
        db.add(DemoResource(kind=kind, resource_id=resource_id, session_id=owner_id))
