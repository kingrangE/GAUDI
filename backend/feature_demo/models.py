from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
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
