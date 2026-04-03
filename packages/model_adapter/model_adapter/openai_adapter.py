from __future__ import annotations

from typing import Any

from .base import (
    FinishReason,
    ModelResponse,
    RateLimitError,
    ToolCall,
    TokenUsage,
    UnsupportedModelError,
)
from .limits import get_context_limit, is_openai
from .tokenizer import count_tokens

try:
    from openai import OpenAI, RateLimitError as _OAIRateLimit
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment,misc]
    _OAIRateLimit = None  # type: ignore[assignment,misc]


class OpenAIAdapter:
    """Provider adapter for OpenAI chat-completion models."""

    def complete(
        self,
        messages: list[dict[str, Any]],
        model_id: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        if not is_openai(model_id):
            raise UnsupportedModelError(model_id)

        if OpenAI is None:  # pragma: no cover
            raise RuntimeError(
                "openai package is required. Install with: pip install openai"
            )

        client = OpenAI()
        kwargs: dict[str, Any] = {"model": model_id, "messages": messages}
        if tools:
            kwargs["tools"] = tools

        try:
            response = client.chat.completions.create(**kwargs)
        except _OAIRateLimit as exc:
            retry_after = float(
                getattr(exc, "retry_after", None) or 0
            )
            raise RateLimitError(retry_after_seconds=retry_after) from exc

        choice = response.choices[0]
        message = choice.message

        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            import json

            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments or "{}"),
                    )
                )

        finish_map = {
            "stop": FinishReason.stop,
            "length": FinishReason.length,
            "tool_calls": FinishReason.tool_calls,
            "content_filter": FinishReason.content_filter,
        }

        return ModelResponse(
            content=message.content,
            tool_calls=tool_calls,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
            finish_reason=finish_map.get(choice.finish_reason, FinishReason.stop),
            model_id=model_id,
        )

    def count_tokens(self, text: str, model_id: str) -> int:
        return count_tokens(text, model_id)

    def get_context_limit(self, model_id: str) -> int:
        return get_context_limit(model_id)
