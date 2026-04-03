"""SQLAlchemy ORM models for all entities.

Table definitions:
- sessions / session_state
- task_state
- core_memory_blocks
- recall_entries
- archival_entries  (with pgvector embedding column)
- jobs
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .db import Base

try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_AVAILABLE = True
except ImportError:
    # Allows importing without pgvector installed (tests/CI)
    Vector = None  # type: ignore[assignment]
    _VECTOR_AVAILABLE = False


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    state: Mapped["SessionStateRow | None"] = relationship("SessionStateRow", back_populates="session", uselist=False)
    core_memory: Mapped[list["CoreMemoryBlock"]] = relationship("CoreMemoryBlock", back_populates="session")
    recall_entries: Mapped[list["RecallEntry"]] = relationship("RecallEntry", back_populates="session")
    archival_entries: Mapped[list["ArchivalEntry"]] = relationship("ArchivalEntry", back_populates="session")


class SessionStateRow(Base):
    __tablename__ = "session_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"), unique=True)
    active_task_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_compiling: Mapped[bool] = mapped_column(Boolean, default=False)
    is_searching: Mapped[bool] = mapped_column(Boolean, default=False)
    retrieval_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    extra: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped[Session] = relationship("Session", back_populates="state")


class TaskStateRow(Base):
    __tablename__ = "task_state"

    task_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    status: Mapped[str] = mapped_column(String(64), default="pending")
    current_step: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CoreMemoryBlock(Base):
    __tablename__ = "core_memory_blocks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    label: Mapped[str] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[Session] = relationship("Session", back_populates="core_memory")


class RecallEntry(Base):
    __tablename__ = "recall_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    entry_type: Mapped[str] = mapped_column(String(64))  # tool_call, decision, citation
    content: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[Session] = relationship("Session", back_populates="recall_entries")


class ArchivalEntry(Base):
    __tablename__ = "archival_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    content: Mapped[str] = mapped_column(Text)
    embedding_model: Mapped[str] = mapped_column(String(128))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # pgvector column — dimension 1536 (OpenAI text-embedding-3-small)
    # Falls back to no column if pgvector is not available
    if _VECTOR_AVAILABLE:
        embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=True)

    session: Mapped[Session] = relationship("Session", back_populates="archival_entries")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type: Mapped[str] = mapped_column(String(128))  # compaction, archival_promotion
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="pending")
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
