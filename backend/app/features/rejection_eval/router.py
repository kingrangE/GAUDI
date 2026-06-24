"""HTTP routes for the rejection-ability evaluation feature."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.features.rejection_eval import service
from app.features.rejection_eval.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    GenerateRequest,
    GenerateResponse,
    ResultResponse,
    SubmitRequest,
    SubmitResponse,
)

router = APIRouter(prefix="/api/rejection-eval", tags=["rejection-eval"])


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    req: CreateSessionRequest, db: AsyncSession = Depends(get_session)
) -> CreateSessionResponse:
    return await service.create_session(db, req.candidate_name)


@router.post(
    "/sessions/{session_id}/topics/{topic_index}/generate",
    response_model=GenerateResponse,
)
async def generate(
    session_id: str,
    topic_index: int,
    req: GenerateRequest,
    db: AsyncSession = Depends(get_session),
) -> GenerateResponse:
    return await service.generate_for_topic(db, session_id, topic_index, req.prompt)


@router.post(
    "/sessions/{session_id}/topics/{topic_index}/submit",
    response_model=SubmitResponse,
)
async def submit(
    session_id: str,
    topic_index: int,
    req: SubmitRequest,
    db: AsyncSession = Depends(get_session),
) -> SubmitResponse:
    return await service.submit_for_topic(db, session_id, topic_index, req)


@router.post("/sessions/{session_id}/score", response_model=ResultResponse)
async def score(
    session_id: str, db: AsyncSession = Depends(get_session)
) -> ResultResponse:
    return await service.score_session(db, session_id)


@router.get("/sessions/{session_id}/result", response_model=ResultResponse)
async def result(
    session_id: str, db: AsyncSession = Depends(get_session)
) -> ResultResponse:
    return await service.get_result(db, session_id)
