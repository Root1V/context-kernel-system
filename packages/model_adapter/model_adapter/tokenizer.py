from __future__ import annotations

from .base import UnsupportedModelError
from .limits import get_context_limit, is_anthropic, is_openai  # noqa: F401

try:
    import tiktoken
except ImportError:  # pragma: no cover
    tiktoken = None  # type: ignore[assignment]


def count_tokens(text: str, model_id: str) -> int:
    """Count the number of tokens in *text* for the given model.

    Uses tiktoken for OpenAI models and a character-based heuristic
    (chars / 4) for Anthropic models (Anthropic does not publish a public
    tokenizer). The heuristic is intentionally conservative.
    """
    if is_openai(model_id):
        return _count_tiktoken(text, model_id)
    if is_anthropic(model_id):
        # Anthropic's typical ratio is ~4 chars per token
        return max(1, len(text) // 4)
    raise UnsupportedModelError(model_id)


def _count_tiktoken(text: str, model_id: str) -> int:
    if tiktoken is None:  # pragma: no cover
        raise RuntimeError(
            "tiktoken is required for OpenAI token counting. Install it with: pip install tiktoken"
        )
    try:
        encoding = tiktoken.encoding_for_model(model_id)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))
