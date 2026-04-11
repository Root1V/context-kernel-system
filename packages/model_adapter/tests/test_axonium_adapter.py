"""Unit tests for AxoniumAdapter — covers spec scenarios for axonium-provider."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Guard: skip entire module on Python < 3.13 (axonium requires 3.13)
if sys.version_info < (3, 13):
    pytest.skip("AxoniumAdapter tests require Python 3.13+", allow_module_level=True)

axonium = pytest.importorskip("axonium", reason="axonium SDK not installed")

from model_adapter import RateLimitError, get_context_limit  # noqa: E402
from model_adapter.axonium_adapter import AxoniumAdapter  # noqa: E402
from model_adapter.base import FinishReason, ModelResponse  # noqa: E402
from model_adapter.limits import is_local  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_axonium_result(
    content: str = "hello",
    finish_reason: str = "stop",
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
    total_tokens: int = 15,
) -> MagicMock:
    """Build a minimal mock mimicking axonium.ChatCompletionResult."""
    usage = MagicMock(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
    message = MagicMock(content=content)
    choice = MagicMock(message=message, finish_reason=finish_reason)
    result = MagicMock(choices=[choice], usage=usage)
    return result


# ---------------------------------------------------------------------------
# 5.5 — is_local helper
# ---------------------------------------------------------------------------


def test_is_local_true_for_local_prefix() -> None:
    assert is_local("local/mistral-7b-instruct") is True


def test_is_local_false_for_openai() -> None:
    assert is_local("gpt-4o") is False


def test_is_local_false_for_anthropic() -> None:
    assert is_local("claude-3-5-sonnet-20241022") is False


# ---------------------------------------------------------------------------
# 5.6 — get_context_limit for local models
# ---------------------------------------------------------------------------


def test_get_context_limit_local_model() -> None:
    assert get_context_limit("local/mistral-7b-instruct") == 32_768


# ---------------------------------------------------------------------------
# 5.2 — Successful complete() with mocked LlamaAdapter
# ---------------------------------------------------------------------------


def test_complete_success_normalizes_model_response() -> None:
    mock_result = _make_axonium_result(content="Paris", finish_reason="stop")

    with patch("model_adapter.axonium_adapter.AxoniumAdapter.__init__", return_value=None):
        adapter = AxoniumAdapter.__new__(AxoniumAdapter)
        # Set attributes that __init__ would set
        mock_llama_cls = MagicMock(return_value=MagicMock(chat=MagicMock(return_value=mock_result)))
        adapter._LlamaAdapter = mock_llama_cls
        adapter._base_url = "http://localhost:8080"

    response = adapter.complete(
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        model_id="local/mistral-7b-instruct",
        tools=None,
    )

    assert isinstance(response, ModelResponse)
    assert response.content == "Paris"
    assert response.model_id == "local/mistral-7b-instruct"
    assert response.usage.prompt_tokens == 10
    assert response.usage.completion_tokens == 5
    assert response.usage.total_tokens == 15
    assert response.finish_reason == FinishReason.stop
    assert response.tool_calls == []


# ---------------------------------------------------------------------------
# 5.3 — tools non-empty raises NotImplementedError
# ---------------------------------------------------------------------------


def test_complete_raises_not_implemented_when_tools_provided() -> None:
    with patch("model_adapter.axonium_adapter.AxoniumAdapter.__init__", return_value=None):
        adapter = AxoniumAdapter.__new__(AxoniumAdapter)
        adapter._LlamaAdapter = MagicMock()
        adapter._base_url = "http://localhost:8080"

    with pytest.raises(NotImplementedError, match="Tool calls are not supported"):
        adapter.complete(
            messages=[{"role": "user", "content": "hi"}],
            model_id="local/mistral-7b-instruct",
            tools=[{"name": "get_weather", "description": "...", "parameters": {}}],
        )


# ---------------------------------------------------------------------------
# 5.4 — Axonium SDK missing raises ImportError
# ---------------------------------------------------------------------------


def test_init_raises_import_error_when_axonium_missing() -> None:
    with patch.dict(sys.modules, {"axonium": None}), pytest.raises(ImportError, match="axonium"):
        AxoniumAdapter()


# ---------------------------------------------------------------------------
# Rate-limit error mapping
# ---------------------------------------------------------------------------


def test_complete_maps_429_to_rate_limit_error() -> None:
    with patch("model_adapter.axonium_adapter.AxoniumAdapter.__init__", return_value=None):
        adapter = AxoniumAdapter.__new__(AxoniumAdapter)

        class FakeLlamaInstance:
            def chat(self, messages: Any, **kwargs: Any) -> Any:
                raise RuntimeError("HTTP 429: Too Many Requests")

        adapter._LlamaAdapter = MagicMock(return_value=FakeLlamaInstance())
        adapter._base_url = "http://localhost:8080"

    with pytest.raises(RateLimitError):
        adapter.complete(
            messages=[{"role": "user", "content": "hi"}],
            model_id="local/mistral-7b-instruct",
        )
