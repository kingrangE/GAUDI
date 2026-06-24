"""ORM models for the test-design evaluation feature.

Inherits the shared `Base` so `create_all()` discovers these tables. JSON
columns store the structured blobs (works on both Postgres and SQLite).
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TestDesignSession(Base):
    __tablename__ = "test_design_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    candidate_name: Mapped[str] = mapped_column(String(120))
    # Loosely typed link to a future auth user; unused for now (candidate_id stub).
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighted_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class TestDesignSubmission(Base):
    __tablename__ = "test_design_submissions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("test_design_sessions.id"), index=True
    )
    problem_index: Mapped[int] = mapped_column(Integer)
    problem_id: Mapped[str] = mapped_column(String(40))
    # the candidate's free-text flaw descriptions, in submission order.
    candidate_flaws: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # full score_submission() blob: per-flaw verdicts, false_positives, counts, metrics, report.
    judge_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighted_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
