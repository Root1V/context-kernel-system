"""Session endpoint request/response schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    user_id: Optional[str] = None
    metadata: dict = {}


class SessionResponse(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    is_active: bool = True
