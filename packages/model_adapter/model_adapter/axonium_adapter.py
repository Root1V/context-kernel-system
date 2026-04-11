from __future__ import annotations

import os
from typing import Any, Optional

from .base import FinishReason, ModelResponse, RateLimitError, TokenUsage


class AxoniumAdapter:
    """Adapter that bridges the Axonium SDK's LlamaAdapter to the system's ModelResponse contract.

    Model IDs must use the ``local/<name>`` prefix (e.g. ``local/mistral-7b-instruct``).
    The ``local/`` prefix is stripped before the model name is forwarded to llama-server.

    Authentication (Bearer token) is handled transparently by the Axonium SDK using the
    ``LLM_BASE_URL``, ``LLM_USERNAME``, and ``LLM_PASSWORD`` environment variables.
    """

    def __init__(self) -> None:
        try:
            from axonium import LlamaAdapter  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "The 'axonium' package is required for local model inference but is not "
                "installed. Install it with: "
                "uv add --find-links <path-to-axonium-dist> axonium"
            ) from exc

        base_url = os.environ.get("LLM_BASE_URL", "http://localhost:8080")
        self._LlamaAdapter = LlamaAdapter
        self._base_url = base_url

    def complete(
        self,
        messages: list[dict[str, Any]],
        model_id: str,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> ModelResponse:
        """Run a chat completion against the local llama-server and return a ModelResponse."""
        if tools:
            raise NotImplementedError(
                "Tool calls are not supported for local/* models via AxoniumAdapter. "
                "Use an OpenAI or Anthropic model for tool-call support."
            )

        # Strip "local/" prefix to get the bare model name for llama-server
        bare_model = model_id.removeprefix("local/")

        adapter = self._LlamaAdapter(model=bare_model, base_url=self._base_url)

        try:
            result = adapter.chat(messages=messages)
        except Exception as exc:
            self._handle_error(exc)

        return self._normalize(result, model_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(result: Any, model_id: str) -> ModelResponse:
        choice = result.choices[0]
        content: Optional[str] = choice.message.content if choice.message else None

        usage_obj = result.usage
        if usage_obj is not None:
            usage = TokenUsage(
                prompt_tokens=usage_obj.prompt_tokens,
                completion_tokens=usage_obj.completion_tokens,
                total_tokens=usage_obj.total_tokens,
            )
        else:
            usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        raw_finish = (choice.finish_reason or "stop").lower()
        try:
            finish_reason = FinishReason(raw_finish)
        except ValueError:
            finish_reason = FinishReason.stop

        return ModelResponse(
            content=content,
            tool_calls=[],
            usage=usage,
            finish_reason=finish_reason,
            model_id=model_id,
        )

    @staticmethod
    def _handle_error(exc: Exception) -> None:
        """Map Axonium / httpx errors to the system's typed exceptions."""
        exc_str = str(exc)
        # LlmAPIError message format: "HTTP 429: ..."
        if "429" in exc_str or "rate" in exc_str.lower():
            raise RateLimitError(retry_after_seconds=0) from exc
        raise RuntimeError(f"Local LLM inference error: {exc_str}") from exc
