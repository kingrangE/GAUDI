from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.features.mock_exam.router import require_admin
from feature_demo.dispatch import dispatch_job, recover_jobs
from feature_demo.jobs import CreateJob, JobState, accept_job, job_state, owned_job
from feature_demo.models import DemoSession
from feature_demo.session import current_demo_session


async def require_visitor(
    request: Request, response: Response, db: AsyncSession = Depends(get_session)
) -> DemoSession:
    visitor = await current_demo_session(request, db)
    if visitor is None:
        raise HTTPException(status_code=404, detail="demo mode disabled")
    response.headers["Cache-Control"] = "no-store"
    return visitor


router = APIRouter(prefix="/api/demo/jobs", tags=["demo-jobs"])


@router.post("", status_code=202, response_model=JobState)
async def create_job(
    body: CreateJob,
    idempotency_key: Annotated[
        str, Header(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    ],
    visitor: DemoSession = Depends(require_visitor),
    db: AsyncSession = Depends(get_session),
) -> dict:
    job = await accept_job(db, visitor.id, idempotency_key, body)
    await dispatch_job(db, job)
    return job_state(job)


@router.post("/recover", dependencies=[Depends(require_admin)])
async def recover(
    db: AsyncSession = Depends(get_session),
    after: str | None = Query(default=None, pattern=r"^[0-9a-f]{32}$"),
) -> dict:
    try:
        return await recover_jobs(db, after)
    except (RedisError, OSError) as exc:
        raise HTTPException(status_code=503, detail="job broker unavailable") from exc


@router.get("/{job_id}", response_model=JobState)
async def read_job(
    job_id: str,
    visitor: DemoSession = Depends(require_visitor),
    db: AsyncSession = Depends(get_session),
) -> dict:
    return job_state(await owned_job(db, job_id, visitor.id))


@router.get("/{job_id}/result")
async def read_result(
    job_id: str,
    visitor: DemoSession = Depends(require_visitor),
    db: AsyncSession = Depends(get_session),
) -> dict:
    job = await owned_job(db, job_id, visitor.id)
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="job result not ready")
    return job.result
