"""Chat endpoint request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: str
    model_id: str = "gpt-4o"
    max_tool_iterations: int = Field(default=5, ge=0, le=20)
    retrieval_needed: bool = True


class ChatResponse(BaseModel):
    session_id: str
    turn_id: str
    assistant_message: str
    status: str
    tool_calls_made: int
    state_persisted: bool
