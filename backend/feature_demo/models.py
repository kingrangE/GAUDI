from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DemoSession(Base):
    __tablename__ = "demo_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DemoResource(Base):
    __tablename__ = "demo_resources"

    kind: Mapped[str] = mapped_column(String(40), primary_key=True)
    resource_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("demo_sessions.id"), index=True)


class DemoJob(Base):
    __tablename__ = "demo_jobs"
    __table_args__ = (UniqueConstraint("session_id", "idempotency_key"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    session_id: Mapped[str] = mapped_column(ForeignKey("demo_sessions.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    input_hash: Mapped[str] = mapped_column(String(64))
    feature: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    dispatch_status: Mapped[str] = mapped_column(String(20), default="pending")
    lease: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phase: Mapped[str] = mapped_column(String(40), default="queued")
    completed_units: Mapped[int] = mapped_column(Integer, default=0)
    total_units: Mapped[int] = mapped_column(Integer, default=4)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DemoBudget(Base):
    __tablename__ = "demo_budget"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    day: Mapped[str] = mapped_column(String(10))
    reserved: Mapped[int] = mapped_column(BigInteger, default=0)
    inflight: Mapped[int] = mapped_column(BigInteger, default=0)
    spent: Mapped[int] = mapped_column(BigInteger, default=0)
    revision: Mapped[int] = mapped_column(Integer, default=0)


class DemoAttempt(Base):
    __tablename__ = "demo_attempts"
    __table_args__ = (UniqueConstraint("session_id", "feature"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    session_id: Mapped[str] = mapped_column(ForeignKey("demo_sessions.id"))
    feature: Mapped[str] = mapped_column(String(40))
    root: Mapped[str] = mapped_column(String(128))
    remaining: Mapped[int] = mapped_column(BigInteger, default=0)
    spent: Mapped[int] = mapped_column(BigInteger, default=0)
    calls: Mapped[int] = mapped_column(Integer, default=0)
    max_calls: Mapped[int] = mapped_column(Integer)
    closed: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DemoStep(Base):
    __tablename__ = "demo_steps"
    attempt_id: Mapped[str] = mapped_column(ForeignKey("demo_attempts.id"), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    job_id: Mapped[str] = mapped_column(ForeignKey("demo_jobs.id"), unique=True)
    retries: Mapped[int] = mapped_column(Integer, default=0)


class DemoCall(Base):
    __tablename__ = "demo_calls"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("demo_attempts.id"))
    job_id: Mapped[str] = mapped_column(ForeignKey("demo_jobs.id"), index=True)
    model: Mapped[str] = mapped_column(String(100))
    reserved: Mapped[int] = mapped_column(BigInteger)
    input_rate: Mapped[int] = mapped_column(BigInteger)
    output_rate: Mapped[int] = mapped_column(BigInteger)
    charged: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="inflight")


class DemoSlot(Base):
    __tablename__ = "demo_slots"
    kind: Mapped[str] = mapped_column(String(20), primary_key=True)
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("demo_jobs.id"), nullable=True)
    lease: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource: Mapped[str | None] = mapped_column(String(80), nullable=True)


class DemoIssuance(Base):
    __tablename__ = "demo_issuance"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)


class DemoRequest(Base):
    __tablename__ = "demo_requests"
    session_id: Mapped[str] = mapped_column(ForeignKey("demo_sessions.id"), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("demo_jobs.id"))
