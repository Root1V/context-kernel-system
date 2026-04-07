from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class FinishReason(str, Enum):
    stop = "stop"
    length = "length"
    tool_calls = "tool_calls"
    content_filter = "content_filter"


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class ModelResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: TokenUsage
    finish_reason: FinishReason
    model_id: str


class UnsupportedModelError(Exception):
    def __init__(self, model_id: str) -> None:
        super().__init__(f"Unsupported model: {model_id!r}")
        self.model_id = model_id


class RateLimitError(Exception):
    def __init__(self, retry_after_seconds: float = 0, is_quota_exceeded: bool = False) -> None:
        msg = "OpenAI quota exhausted" if is_quota_exceeded else f"Rate limit exceeded. Retry after {retry_after_seconds}s"
        super().__init__(msg)
        self.retry_after_seconds = retry_after_seconds
        self.is_quota_exceeded = is_quota_exceeded
