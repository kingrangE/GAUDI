"""HTTP routes for the office-prompting evaluation feature."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.features.office_prompting import service
from app.features.office_prompting.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    ResultResponse,
    RunRequest,
    RunResponse,
)

router = APIRouter(prefix="/api/office-prompting", tags=["office-prompting"])


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    req: CreateSessionRequest, db: AsyncSession = Depends(get_session)
) -> CreateSessionResponse:
    return await service.create_session(db, req.candidate_name)


@router.post(
    "/sessions/{session_id}/problems/{problem_index}/run",
    response_model=RunResponse,
)
async def run(
    session_id: str,
    problem_index: int,
    req: RunRequest,
    db: AsyncSession = Depends(get_session),
) -> RunResponse:
    return await service.run_for_problem(db, session_id, problem_index, req)


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
