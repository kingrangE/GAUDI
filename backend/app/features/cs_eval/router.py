"""HTTP routes for the CS deep-evaluation feature."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.features.cs_eval import service
from app.features.cs_eval.schemas import (
    CreateSessionRequest,
    QuestionPublic,
    SessionCreated,
    SessionResult,
)
from feature_demo.models import DemoSession
from feature_demo.routing import DemoRoute
from feature_demo.session import current_demo_session

router = APIRouter(route_class=DemoRoute, prefix="/api/cs-eval", tags=["cs-eval"])


@router.get("/questions", response_model=list[QuestionPublic])
async def list_questions(db: AsyncSession = Depends(get_session)) -> list[QuestionPublic]:
    return await service.list_questions(db)


@router.post(
    "/sessions",
    response_model=SessionCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_session(
    req: CreateSessionRequest, db: AsyncSession = Depends(get_session),
    visitor: DemoSession | None = Depends(current_demo_session),
) -> SessionCreated:
    return await service.create_session(db, req, owner_id=visitor.id if visitor else None)


@router.get("/sessions/{session_id}", response_model=SessionResult)
async def get_session_result(
    session_id: str, db: AsyncSession = Depends(get_session)
) -> SessionResult:
    return await service.get_session(db, session_id)
