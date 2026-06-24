"""Mock-exam record (write) contract + admin read queries.

WRITE side — the contract the (separately built) mock-exam orchestration calls:
    attempt = await create_exam_attempt(db, candidate_code)
    await record_feature_result(db, attempt.id, "test_design", raw_result)
    ... (one per feature) ...
    await finalize_exam_attempt(db, attempt.id)

This is also where the three features that don't persist on their own
(dev-prompting, spec-design, context-engineering) get their results stored, in
the shared `exam_feature_results` table.

READ side — what the admin console fetches: candidate summaries, the attempt
list, and a single attempt's full breakdown. All reads are rooted at
`exam_attempts`, so practice runs are never visible.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.mock_exam.candidates import (
    CANDIDATES,
    candidate_label,
    feature_label,
    is_candidate,
    is_mock_exam_feature,
)
from app.features.mock_exam.models import ExamAttempt, ExamFeatureResult
from app.features.mock_exam.normalize import normalize_score
from app.features.mock_exam.schemas import (
    AttemptSummary,
    CandidateSummary,
    ExamResultDetail,
    FeatureResultOut,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Write contract
# --------------------------------------------------------------------------- #
async def create_exam_attempt(db: AsyncSession, candidate_code: str) -> ExamAttempt:
    """Open a new mock-exam attempt for one of the three fixed candidates."""
    if not is_candidate(candidate_code):
        raise ValueError(f"unknown candidate code: {candidate_code!r}")

    attempt = ExamAttempt(
        candidate_code=candidate_code,
        candidate_label=candidate_label(candidate_code),
        status="in_progress",
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return attempt


async def record_feature_result(
    db: AsyncSession,
    attempt_id: str,
    feature_key: str,
    raw_result: dict,
    summary: str | None = None,
) -> ExamFeatureResult:
    """Store one feature's native result + its normalized 0–100 score.

    Idempotent per (attempt, feature): re-recording overwrites the prior row.
    """
    if not is_mock_exam_feature(feature_key):
        raise ValueError(f"not a mock-exam feature: {feature_key!r}")

    attempt = await db.get(ExamAttempt, attempt_id)
    if attempt is None:
        raise ValueError(f"unknown exam attempt: {attempt_id!r}")

    normalized = normalize_score(feature_key, raw_result)

    existing = await db.scalar(
        select(ExamFeatureResult).where(
            ExamFeatureResult.exam_attempt_id == attempt_id,
            ExamFeatureResult.feature_key == feature_key,
        )
    )
    if existing is not None:
        existing.normalized_score = normalized
        existing.raw_result = raw_result
        existing.summary = summary
        result = existing
    else:
        result = ExamFeatureResult(
            exam_attempt_id=attempt_id,
            feature_key=feature_key,
            normalized_score=normalized,
            raw_result=raw_result,
            summary=summary,
        )
        db.add(result)

    await db.commit()
    await db.refresh(result)
    return result


async def finalize_exam_attempt(db: AsyncSession, attempt_id: str) -> ExamAttempt:
    """Average the recorded feature scores into `overall_normalized` and mark
    the attempt completed."""
    attempt = await db.scalar(
        select(ExamAttempt)
        .where(ExamAttempt.id == attempt_id)
        .options(selectinload(ExamAttempt.feature_results))
    )
    if attempt is None:
        raise ValueError(f"unknown exam attempt: {attempt_id!r}")

    scores = [r.normalized_score for r in attempt.feature_results]
    attempt.overall_normalized = (
        round(sum(scores) / len(scores), 1) if scores else None
    )
    attempt.status = "completed"
    attempt.completed_at = _now()
    await db.commit()
    await db.refresh(attempt)
    return attempt


# --------------------------------------------------------------------------- #
# Read side (admin)
# --------------------------------------------------------------------------- #
def _to_summary(attempt: ExamAttempt) -> AttemptSummary:
    return AttemptSummary(
        id=attempt.id,
        candidate_code=attempt.candidate_code,
        candidate_label=attempt.candidate_label,
        status=attempt.status,
        overall_normalized=attempt.overall_normalized,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        feature_count=len(attempt.feature_results),
    )


async def list_candidates(db: AsyncSession) -> list[CandidateSummary]:
    """The three fixed candidates, each with their most recent attempt."""
    summaries: list[CandidateSummary] = []
    for code, label in CANDIDATES.items():
        attempt = await db.scalar(
            select(ExamAttempt)
            .where(ExamAttempt.candidate_code == code)
            .options(selectinload(ExamAttempt.feature_results))
            .order_by(ExamAttempt.started_at.desc())
            .limit(1)
        )
        summaries.append(
            CandidateSummary(
                code=code,
                label=label,
                latest_attempt=_to_summary(attempt) if attempt else None,
            )
        )
    return summaries


async def list_exam_results(db: AsyncSession) -> list[AttemptSummary]:
    """Every mock-exam attempt, newest first."""
    attempts = (
        await db.scalars(
            select(ExamAttempt)
            .options(selectinload(ExamAttempt.feature_results))
            .order_by(ExamAttempt.started_at.desc())
        )
    ).all()
    return [_to_summary(a) for a in attempts]


async def get_exam_result(db: AsyncSession, attempt_id: str) -> ExamResultDetail | None:
    """One attempt with its per-feature breakdown, or None if not found."""
    attempt = await db.scalar(
        select(ExamAttempt)
        .where(ExamAttempt.id == attempt_id)
        .options(selectinload(ExamAttempt.feature_results))
    )
    if attempt is None:
        return None

    features = [
        FeatureResultOut(
            feature_key=r.feature_key,
            label=feature_label(r.feature_key),
            normalized_score=r.normalized_score,
            summary=r.summary,
            raw_result=r.raw_result,
        )
        for r in attempt.feature_results
    ]
    summary = _to_summary(attempt)
    return ExamResultDetail(**summary.model_dump(), features=features)
