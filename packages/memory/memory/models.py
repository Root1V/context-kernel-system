"""Pydantic models for all memory layers."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CoreMemoryBlock(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    label: str
    content: str
    token_count: int = 0
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RecallEntryType(str, Enum):
    tool_call = "tool_call"
    decision = "decision"
    citation = "citation"
    event = "event"


class RecallEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    entry_type: RecallEntryType
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ArchivalEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    content: str
    embedding_model: str
    embedding: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageTurn(BaseModel):
    role: str  # user | assistant | tool
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MemorySnapshot(BaseModel):
    """Aggregated view of all memory layers for a session turn."""

    session_id: UUID
    core_memory: list[CoreMemoryBlock] = Field(default_factory=list)
    message_buffer: list[MessageTurn] = Field(default_factory=list)
    recall_entries: list[RecallEntry] = Field(default_factory=list)
    # archival entries are fetched on demand via retrieval, not bulk-loaded
