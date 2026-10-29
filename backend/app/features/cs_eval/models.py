"""ORM models for the CS deep-evaluation (서술형) feature.

A session bundles a candidate's answers to the fixed CS questions; each answer
is judged independently (response-type + score) and the session carries the two
aggregate reports (요약·분석). The reference answer and rubric live on the
question and are *never* serialized into a candidate-facing response.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CsQuestion(Base):
    __tablename__ = "cs_eval_questions"

    # Human-readable slug PK (e.g. "ds-hashmap") so re-seeding is idempotent.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    # 자료구조 / OS / 네트워크 / DB ...
    domain: Mapped[str] = mapped_column(String(40))
    prompt_md: Mapped[str] = mapped_column(Text)
    # Judge-only grounding — never exposed to the candidate.
    reference_answer: Mapped[str] = mapped_column(Text, default="")
    # {"key_points": [...], "common_pitfalls": [...]}
    rubric: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CsSession(Base):
    __tablename__ = "cs_eval_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    # Lightweight candidate identity — no auth yet.
    candidate_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="grading")

    # Signed raw total (Σ per-question score) and a 0-100 display normalization.
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    normalized_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 요약 리포트(부족 키워드 위주) / 분석 리포트(4~5문장). Filled by grading.
    summary_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    answers: Mapped[list["CsAnswer"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="CsAnswer.ordinal",
    )


class CsAnswer(Base):
    __tablename__ = "cs_eval_answers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("cs_eval_sessions.id"), index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("cs_eval_questions.id"), index=True
    )
    answer_text: Mapped[str] = mapped_column(Text)

    # Judge output (null until graded).
    # correct | partial | honest_unknown | bluff_wrong
    response_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Per-question signed score (-5..+5).
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matched_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    missing_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordinal: Mapped[int] = mapped_column(Integer, default=0)

    session: Mapped["CsSession"] = relationship(back_populates="answers")
