"""ORM models for the rejection-ability evaluation feature.

Inherits the shared `Base` so `create_all()` discovers these tables. JSON
columns store the structured blobs (works on both Postgres and SQLite).
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


class RejectionSession(Base):
    __tablename__ = "rejection_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    candidate_name: Mapped[str] = mapped_column(String(120))
    # Loosely typed link to a future auth user; unused for now.
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class RejectionAttempt(Base):
    __tablename__ = "rejection_attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("rejection_sessions.id"), index=True
    )
    topic_index: Mapped[int] = mapped_column(Integer)
    topic_title: Mapped[str] = mapped_column(String(200))
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    # [{id, text, is_flawed, flaw_type, explanation}] — full ground truth.
    generated_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # {"flagged_ids": [...], "reasons": {id: str}}
    selections: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # {"report": str, "items": [...with outcome], "tp"/"fp"/"fn": int}
    judge_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
