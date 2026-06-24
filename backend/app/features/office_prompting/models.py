"""ORM models for the office-prompting evaluation.

Inherits the shared ``Base`` so ``create_all()`` discovers these tables. JSON
columns store the run history and per-attempt score blobs (works on both
Postgres and SQLite).
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OfficeSession(Base):
    __tablename__ = "office_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    candidate_name: Mapped[str] = mapped_column(String(120))
    # Loosely typed link to a future auth user; unused for now.
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class OfficeAttempt(Base):
    __tablename__ = "office_attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("office_sessions.id"), index=True
    )
    problem_index: Mapped[int] = mapped_column(Integer)
    problem_title: Mapped[str] = mapped_column(String(200))
    # [{run_number, prompt, predicted_ids}] — full run history (up to MAX_RUNS).
    runs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    last_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Last run's ids — this is what gets scored.
    last_predicted_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # {tp, fp, fn, correct_count, predicted_count, truth_count} — filled at scoring.
    score: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
