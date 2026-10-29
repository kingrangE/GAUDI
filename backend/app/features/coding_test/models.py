"""ORM models for the traditional coding-test feature.

Inherits the shared `Base` so `create_all()` discovers these tables. JSON
columns store structured blobs (works on both Postgres and SQLite). Test-case
inputs live in a separate table so a problem's hidden grading inputs are never
serialized into a Problem response.
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


class Problem(Base):
    __tablename__ = "coding_test_problems"

    # Human-readable slug PK (e.g. "two-sum") so re-seeding is idempotent and
    # the frontend can deep-link.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description_md: Mapped[str] = mapped_column(Text)
    function_name: Mapped[str] = mapped_column(String(120))
    starter_code: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")
    # Judge-only grounding — never exposed to the candidate.
    reference_solution: Mapped[str] = mapped_column(Text, default="")
    # {"expected_complexity": str, "key_concepts": [...], "common_pitfalls": [...]}
    rubric: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # How a returned value is compared to the expected value.
    comparison: Mapped[str] = mapped_column(String(20), default="exact")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="TestCase.ordinal",
    )


class TestCase(Base):
    __tablename__ = "coding_test_test_cases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    problem_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("coding_test_problems.id"), index=True
    )
    # "sample" (visible, Run button) | "grading" (hidden, Submit scoring).
    kind: Mapped[str] = mapped_column(String(10))
    # JSON-encoded positional args list passed to the candidate function.
    args_json: Mapped[str] = mapped_column(Text)
    # JSON-encoded expected return value.
    expected_json: Mapped[str] = mapped_column(Text)
    ordinal: Mapped[int] = mapped_column(Integer, default=0)

    problem: Mapped["Problem"] = relationship(back_populates="test_cases")


class Submission(Base):
    __tablename__ = "coding_test_submissions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    problem_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("coding_test_problems.id"), index=True
    )
    # Lightweight candidate identity — no auth yet.
    candidate_id: Mapped[str] = mapped_column(String(64))
    code: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="grading")

    # Deterministic test score (from the runner, not the LLM).
    test_passed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    test_total: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # LLM-judge output (filled in PR-B; null here).
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    analysis_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 0-100, independent of test pass rate — enables tie-breaking (동점자 변별).
    code_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
