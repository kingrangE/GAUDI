"""Admin read API for mock-exam results (`/api/admin`).

Read-only: lists candidates and mock-exam attempts and serves a single
attempt's breakdown. Practice results are never reachable here because every
query is rooted at `exam_attempts`.

Guarded by an optional shared secret (`X-Admin-Token` vs `ADMIN_TOKEN`); open
when unset so the demo works without configuration.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.features.mock_exam import service
from app.features.mock_exam.schemas import (
    AttemptSummary,
    CandidateSummary,
    ExamResultDetail,
)


async def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Reject requests when ADMIN_TOKEN is configured and the header mismatches."""
    expected = get_settings().admin_token
    if expected and x_admin_token != expected:
        raise HTTPException(status_code=401, detail="invalid admin token")


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/candidates", response_model=list[CandidateSummary])
async def candidates(db: AsyncSession = Depends(get_session)) -> list[CandidateSummary]:
    return await service.list_candidates(db)


@router.get("/exam-results", response_model=list[AttemptSummary])
async def exam_results(db: AsyncSession = Depends(get_session)) -> list[AttemptSummary]:
    return await service.list_exam_results(db)


@router.get("/exam-results/{attempt_id}", response_model=ExamResultDetail)
async def exam_result_detail(
    attempt_id: str, db: AsyncSession = Depends(get_session)
) -> ExamResultDetail:
    detail = await service.get_exam_result(db, attempt_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="exam attempt not found")
    return detail
