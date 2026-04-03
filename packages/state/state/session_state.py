from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SessionState(BaseModel):
    session_id: UUID
    user_id: Optional[str] = None
    active_task_id: Optional[str] = None
    is_compiling: bool = False
    is_searching: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionStatePatch(BaseModel):
    """Partial update payload — all fields optional."""

    user_id: Optional[str] = None
    active_task_id: Optional[str] = None
    is_compiling: Optional[bool] = None
    is_searching: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None
