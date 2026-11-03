from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from feature_demo.models import DemoSession
from feature_demo.session import COOKIE_NAME, check_origin, find_session, token_hash

router = APIRouter(prefix="/api/demo", tags=["demo"])


class SessionInfo(BaseModel):
    session_id: str
    expires_at: datetime


@router.post("/session", response_model=SessionInfo)
async def open_session(
    request: Request, response: Response, db: AsyncSession = Depends(get_session)
) -> SessionInfo:
    settings = get_settings()
    if not settings.demo_enabled:
        raise HTTPException(status_code=404, detail="demo mode disabled")
    check_origin(request)
    visitor = await find_session(request, db)
    token = request.cookies.get(COOKIE_NAME)
    if visitor is None:
        token = token_urlsafe(32)
        visitor = DemoSession(token_hash=token_hash(token))
        db.add(visitor)
    visitor.expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.demo_session_seconds
    )
    await db.commit()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.demo_session_seconds,
        httponly=True,
        secure=settings.demo_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return SessionInfo(session_id=visitor.id, expires_at=visitor.expires_at)


@router.get("/session", response_model=SessionInfo)
async def read_session(
    request: Request, response: Response, db: AsyncSession = Depends(get_session)
) -> SessionInfo:
    if not get_settings().demo_enabled:
        raise HTTPException(status_code=404, detail="demo mode disabled")
    visitor = await find_session(request, db)
    if visitor is None:
        raise HTTPException(status_code=401, detail="demo session missing or expired")
    response.headers["Cache-Control"] = "no-store"
    return SessionInfo(session_id=visitor.id, expires_at=visitor.expires_at)
