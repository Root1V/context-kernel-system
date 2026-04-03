from __future__ import annotations

from .base import UnsupportedModelError

# Context window limits per model (in tokens)
_CONTEXT_LIMITS: dict[str, int] = {
    # OpenAI
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-3.5-turbo": 16_385,
    # Anthropic
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-5-haiku-20241022": 200_000,
    "claude-3-opus-20240229": 200_000,
    "claude-3-sonnet-20240229": 200_000,
    "claude-3-haiku-20240307": 200_000,
}

_OPENAI_MODELS = {k for k in _CONTEXT_LIMITS if k.startswith("gpt")}
_ANTHROPIC_MODELS = {k for k in _CONTEXT_LIMITS if k.startswith("claude")}


def get_context_limit(model_id: str) -> int:
    """Return the context window size (tokens) for a given model."""
    if model_id not in _CONTEXT_LIMITS:
        raise UnsupportedModelError(model_id)
    return _CONTEXT_LIMITS[model_id]


def is_openai(model_id: str) -> bool:
    return model_id in _OPENAI_MODELS


def is_anthropic(model_id: str) -> bool:
    return model_id in _ANTHROPIC_MODELS


def supported_models() -> list[str]:
    return list(_CONTEXT_LIMITS.keys())
