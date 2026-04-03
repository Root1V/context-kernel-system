from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SessionState(BaseModel):
    session_id: UUID
    user_id: str | None = None
    active_task_id: str | None = None
    is_compiling: bool = False
    is_searching: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionStatePatch(BaseModel):
    """Partial update payload — all fields optional."""
    user_id: str | None = None
    active_task_id: str | None = None
    is_compiling: bool | None = None
    is_searching: bool | None = None
    metadata: dict[str, Any] | None = None
