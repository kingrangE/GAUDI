"""Durable acceptance, idempotency, and owner-scoped job reads."""

import json
from datetime import datetime
from hashlib import sha256
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from feature_context_engineering.models import Submission
from feature_context_engineering.service import create_submission
from feature_demo.models import DemoJob


class ContextInput(Submission):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1, max_length=128)
    claude_md: str = Field(min_length=1, max_length=200000)


class CreateJob(BaseModel):
    model_config = ConfigDict(extra="forbid")
    feature: Literal["context_engineering"]
    action: Literal["evaluate"]
    input: ContextInput


class JobState(BaseModel):
    job_id: str
    feature: str
    action: str
    status: Literal["queued", "running", "completed", "failed"]
    dispatch_status: Literal["pending", "enqueued", "error"]
    phase: str
    completed_units: int = Field(ge=0)
    total_units: int = Field(gt=0)
    progress_percent: int = Field(ge=0, le=100)
    error_code: Literal["evaluation_failed", "session_expired", "worker_interrupted"] | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


async def accept_job(db: AsyncSession, owner_id: str, key: str, body: CreateJob) -> DemoJob:
    serialized = json.dumps(body.model_dump(), sort_keys=True, ensure_ascii=False)
    digest = sha256(serialized.encode()).hexdigest()
    query = select(DemoJob).where(DemoJob.session_id == owner_id, DemoJob.idempotency_key == key)
    existing = await db.scalar(query)
    if existing is None:
        try:
            create_submission(body.input.project_id, body.input.claude_md)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        job = DemoJob(
            session_id=owner_id,
            idempotency_key=key,
            input_hash=digest,
            feature=body.feature,
            action=body.action,
            payload=body.input.model_dump(),
        )
        db.add(job)
        try:
            await db.commit()
            return job
        except IntegrityError:
            await db.rollback()
            existing = await db.scalar(query)
            if existing is None:
                raise
    if existing.input_hash != digest:
        raise HTTPException(status_code=409, detail="idempotency key reused with different input")
    return existing


async def owned_job(db: AsyncSession, job_id: str, owner_id: str) -> DemoJob:
    job = await db.scalar(
        select(DemoJob).where(
            DemoJob.id == job_id,
            DemoJob.session_id == owner_id,
        )
    )
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


def job_state(job: DemoJob) -> dict:
    percent = (
        100 if job.status == "completed" else min(99, job.completed_units * 100 // job.total_units)
    )
    return {
        "job_id": job.id,
        "feature": job.feature,
        "action": job.action,
        "status": job.status,
        "dispatch_status": job.dispatch_status,
        "phase": job.phase,
        "completed_units": job.completed_units,
        "total_units": job.total_units,
        "progress_percent": percent,
        "error_code": job.error_code,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }
