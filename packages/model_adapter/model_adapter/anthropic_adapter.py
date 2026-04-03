from __future__ import annotations

from typing import Any

try:
    import anthropic
    from anthropic import RateLimitError as _AnthRateLimit
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore[assignment]
    _AnthRateLimit = None  # type: ignore[assignment,misc]

from .base import (
    FinishReason,
    ModelResponse,
    RateLimitError,
    ToolCall,
    TokenUsage,
    UnsupportedModelError,
)
from .limits import get_context_limit, is_anthropic
from .tokenizer import count_tokens


class AnthropicAdapter:
    """Provider adapter for Anthropic claude models, normalized to ModelResponse."""

    def complete(
        self,
        messages: list[dict[str, Any]],
        model_id: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        if not is_anthropic(model_id):
            raise UnsupportedModelError(model_id)

        if anthropic is None:  # pragma: no cover
            raise RuntimeError(
                "anthropic package is required. Install with: pip install anthropic"
            )

        client = anthropic.Anthropic()

        # Separate system message (Anthropic uses a dedicated param)
        system: str | None = None
        user_messages: list[dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                user_messages.append(msg)

        kwargs: dict[str, Any] = {
            "model": model_id,
            "messages": user_messages,
            "max_tokens": 4096,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        try:
            response = client.messages.create(**kwargs)
        except _AnthRateLimit as exc:
            retry_after = float(
                getattr(exc, "retry_after_seconds", None)
                or getattr(exc, "retry_after", None)
                or 0
            )
            raise RateLimitError(retry_after_seconds=retry_after) from exc

        text_content: str | None = None
        tool_calls: list[ToolCall] = []
        import uuid

        for block in response.content:
            if block.type == "text":
                text_content = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=getattr(block, "id", str(uuid.uuid4())),
                        name=block.name,
                        arguments=block.input or {},
                    )
                )

        stop_reason = getattr(response, "stop_reason", "end_turn")
        finish_map = {
            "end_turn": FinishReason.stop,
            "max_tokens": FinishReason.length,
            "tool_use": FinishReason.tool_calls,
        }

        usage = response.usage
        return ModelResponse(
            content=text_content,
            tool_calls=tool_calls,
            usage=TokenUsage(
                prompt_tokens=usage.input_tokens,
                completion_tokens=usage.output_tokens,
                total_tokens=usage.input_tokens + usage.output_tokens,
            ),
            finish_reason=finish_map.get(stop_reason, FinishReason.stop),
            model_id=model_id,
        )

    def count_tokens(self, text: str, model_id: str) -> int:
        return count_tokens(text, model_id)

    def get_context_limit(self, model_id: str) -> int:
        return get_context_limit(model_id)
