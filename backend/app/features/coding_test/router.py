"""HTTP routes for the traditional coding-test feature."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.features.coding_test import service
from app.features.coding_test.schemas import (
    CreateSubmissionRequest,
    ProblemDetail,
    ProblemSummary,
    RunRequest,
    RunResponse,
    SubmissionCreated,
    SubmissionResult,
)

router = APIRouter(prefix="/api/coding-test", tags=["coding-test"])


@router.get("/problems", response_model=list[ProblemSummary])
async def list_problems(db: AsyncSession = Depends(get_session)) -> list[ProblemSummary]:
    return await service.list_problems(db)


@router.get("/problems/{problem_id}", response_model=ProblemDetail)
async def get_problem(
    problem_id: str, db: AsyncSession = Depends(get_session)
) -> ProblemDetail:
    return await service.get_problem(db, problem_id)


@router.post("/problems/{problem_id}/run", response_model=RunResponse)
async def run(
    problem_id: str, req: RunRequest, db: AsyncSession = Depends(get_session)
) -> RunResponse:
    return await service.run_code(db, problem_id, req.code)


@router.post(
    "/submissions",
    response_model=SubmissionCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_submission(
    req: CreateSubmissionRequest, db: AsyncSession = Depends(get_session)
) -> SubmissionCreated:
    return await service.create_submission(db, req)


@router.get("/submissions/{submission_id}", response_model=SubmissionResult)
async def get_submission(
    submission_id: str, db: AsyncSession = Depends(get_session)
) -> SubmissionResult:
    return await service.get_submission(db, submission_id)
