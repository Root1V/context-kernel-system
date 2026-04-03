"""model_adapter — unified public interface for LLM provider adapters.

All other packages MUST import exclusively from this module, never from
internal submodules (e.g. openai_adapter, anthropic_adapter).
"""

from __future__ import annotations

from typing import Any

from .anthropic_adapter import AnthropicAdapter
from .base import (
    FinishReason,
    ModelResponse,
    RateLimitError,
    TokenUsage,
    ToolCall,
    UnsupportedModelError,
)
from .limits import get_context_limit, supported_models
from .openai_adapter import OpenAIAdapter
from .tokenizer import count_tokens

__all__ = [
    "complete",
    "count_tokens",
    "get_context_limit",
    "supported_models",
    # Models / exceptions
    "ModelResponse",
    "TokenUsage",
    "ToolCall",
    "FinishReason",
    "UnsupportedModelError",
    "RateLimitError",
]

_openai = OpenAIAdapter()
_anthropic = AnthropicAdapter()


def _get_adapter(model_id: str) -> OpenAIAdapter | AnthropicAdapter:
    from .limits import is_anthropic, is_openai

    if is_openai(model_id):
        return _openai
    if is_anthropic(model_id):
        return _anthropic
    raise UnsupportedModelError(model_id)


def complete(
    messages: list[dict[str, Any]],
    model_id: str,
    tools: list[dict[str, Any]] | None = None,
) -> ModelResponse:
    """Execute a chat completion and return a normalized ModelResponse."""
    return _get_adapter(model_id).complete(messages, model_id, tools)
