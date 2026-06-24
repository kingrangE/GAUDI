"""HTTP routes for the test-design evaluation feature."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.features.test_design import services
from app.features.test_design.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    ResultResponse,
    SubmitRequest,
    SubmitResponse,
)

router = APIRouter(prefix="/test-design", tags=["test-design"])


@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_session(
    req: CreateSessionRequest, db: AsyncSession = Depends(get_session)
) -> CreateSessionResponse:
    return await services.create_session(db, req.candidate_name)


@router.post(
    "/sessions/{session_id}/problems/{problem_index}/submit",
    response_model=SubmitResponse,
)
async def submit(
    session_id: str,
    problem_index: int,
    req: SubmitRequest,
    db: AsyncSession = Depends(get_session),
) -> SubmitResponse:
    try:
        await services.submit_problem(db, session_id, problem_index, req.flaws)
    except services.SessionNotFound:
        raise HTTPException(status_code=404, detail="session not found") from None
    except IndexError:
        raise HTTPException(status_code=404, detail="problem not found") from None
    return SubmitResponse(problem_index=problem_index, submitted=True)


@router.get("/sessions/{session_id}/result", response_model=ResultResponse)
async def result(
    session_id: str, db: AsyncSession = Depends(get_session)
) -> ResultResponse:
    try:
        return await services.build_result(db, session_id)
    except services.SessionNotFound:
        raise HTTPException(status_code=404, detail="session not found") from None
