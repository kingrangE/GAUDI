"""ORM models for mock-exam (모의고사) results.

Two tables form the cross-feature record the admin console reads:

- `exam_attempts`        — one row per candidate's mock-exam run.
- `exam_feature_results` — one row per (attempt, feature) holding the feature's
  native result blob plus a normalized 0–100 score.

Practice runs never create rows here, so any query rooted at `exam_attempts`
is inherently mock-exam-only. Inherits the shared `Base` so `create_all()`
discovers these tables.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    candidate_code: Mapped[str] = mapped_column(String(40), index=True)
    candidate_label: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    # Mean of the recorded feature scores; filled on finalize.
    overall_normalized: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    feature_results: Mapped[list["ExamFeatureResult"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="ExamFeatureResult.created_at",
    )


class ExamFeatureResult(Base):
    __tablename__ = "exam_feature_results"
    __table_args__ = (
        UniqueConstraint("exam_attempt_id", "feature_key", name="uq_attempt_feature"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    exam_attempt_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("exam_attempts.id"), index=True
    )
    # One of MOCK_EXAM_FEATURES (test_design / dev_prompting / spec_design /
    # rejection_eval / context_engineering).
    feature_key: Mapped[str] = mapped_column(String(40))
    normalized_score: Mapped[float] = mapped_column(Float)
    # The feature's native scoring result, stored verbatim for the detail view.
    raw_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    attempt: Mapped[ExamAttempt] = relationship(back_populates="feature_results")
