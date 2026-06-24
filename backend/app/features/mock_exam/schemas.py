"""Pydantic response shapes for the admin read API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AttemptSummary(BaseModel):
    """A mock-exam attempt without its per-feature breakdown."""

    id: str
    candidate_code: str
    candidate_label: str
    status: str
    overall_normalized: float | None
    started_at: datetime
    completed_at: datetime | None
    feature_count: int


class CandidateSummary(BaseModel):
    """One of the three candidates plus their most recent attempt (if any)."""

    code: str
    label: str
    latest_attempt: AttemptSummary | None


class FeatureResultOut(BaseModel):
    feature_key: str
    label: str
    normalized_score: float
    summary: str | None
    raw_result: dict | None


class ExamResultDetail(AttemptSummary):
    """A single attempt with its five feature results."""

    features: list[FeatureResultOut]
