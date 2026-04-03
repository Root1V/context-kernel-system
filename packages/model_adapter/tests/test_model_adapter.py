"""Unit tests for model_adapter — covers all spec scenarios."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from model_adapter import (
    ModelResponse,
    RateLimitError,
    TokenUsage,
    UnsupportedModelError,
    complete,
    count_tokens,
    get_context_limit,
)
from model_adapter.base import FinishReason

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_openai_response(content: str = "hello", finish_reason: str = "stop"):
    """Build a minimal mock that mimics openai.ChatCompletion."""
    usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    message = MagicMock(content=content, tool_calls=None)
    choice = MagicMock(message=message, finish_reason=finish_reason)
    resp = MagicMock(choices=[choice], usage=usage)
    return resp


def _make_anthropic_response(text: str = "hi"):
    block = MagicMock()
    block.type = "text"
    block.text = text
    usage = MagicMock(input_tokens=8, output_tokens=4)
    resp = MagicMock(content=[block], stop_reason="end_turn", usage=usage)
    return resp


# ---------------------------------------------------------------------------
# UnsupportedModelError
# ---------------------------------------------------------------------------


class TestUnsupportedModel:
    def test_complete_raises_for_unknown_model(self):
        with pytest.raises(UnsupportedModelError) as exc_info:
            complete([], model_id="unknown-model-xyz")
        assert "unknown-model-xyz" in str(exc_info.value)

    def test_count_tokens_raises_for_unknown_model(self):
        with pytest.raises(UnsupportedModelError):
            count_tokens("text", model_id="does-not-exist")

    def test_get_context_limit_raises_for_unknown_model(self):
        with pytest.raises(UnsupportedModelError):
            get_context_limit("no-such-model")


# ---------------------------------------------------------------------------
# get_context_limit
# ---------------------------------------------------------------------------


class TestContextLimit:
    def test_gpt4o_returns_128k(self):
        assert get_context_limit("gpt-4o") == 128_000

    def test_claude_sonnet_returns_200k(self):
        assert get_context_limit("claude-3-5-sonnet-20241022") == 200_000


# ---------------------------------------------------------------------------
# count_tokens
# ---------------------------------------------------------------------------


class TestCountTokens:
    def test_anthropic_count_is_positive(self):
        result = count_tokens("Hello, world!", model_id="claude-3-5-sonnet-20241022")
        assert result >= 1

    @patch("model_adapter.tokenizer.tiktoken")
    def test_openai_delegates_to_tiktoken(self, mock_tiktoken):
        enc = MagicMock()
        enc.encode.return_value = [1, 2, 3]
        mock_tiktoken.encoding_for_model.return_value = enc
        result = count_tokens("hello", model_id="gpt-4o")
        assert result == 3


# ---------------------------------------------------------------------------
# OpenAI complete — happy path
# ---------------------------------------------------------------------------


class TestOpenAIComplete:
    @patch("model_adapter.openai_adapter.OpenAI")
    def test_returns_model_response(self, MockOpenAI):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_openai_response("hi")
        MockOpenAI.return_value = mock_client

        result = complete([{"role": "user", "content": "hello"}], model_id="gpt-4o")

        assert isinstance(result, ModelResponse)
        assert result.content == "hi"
        assert isinstance(result.usage, TokenUsage)
        assert result.model_id == "gpt-4o"
        assert result.finish_reason == FinishReason.stop

    @patch("model_adapter.openai_adapter.OpenAI")
    def test_rate_limit_raises_rate_limit_error(self, MockOpenAI):
        openai_mod = pytest.importorskip("openai", reason="openai not installed")
        OAIRateLimit = openai_mod.RateLimitError

        mock_client = MagicMock()
        mock_error = OAIRateLimit(
            message="rate limited",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        )
        mock_client.chat.completions.create.side_effect = mock_error
        MockOpenAI.return_value = mock_client

        with pytest.raises(RateLimitError) as exc_info:
            complete([{"role": "user", "content": "hi"}], model_id="gpt-4o")

        assert exc_info.value.retry_after_seconds >= 0


# ---------------------------------------------------------------------------
# Anthropic complete — happy path
# ---------------------------------------------------------------------------


class TestAnthropicComplete:
    @patch("model_adapter.anthropic_adapter.anthropic")
    def test_returns_normalized_model_response(self, mock_anthropic_module):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_anthropic_response("hello back")
        mock_anthropic_module.Anthropic.return_value = mock_client
        mock_anthropic_module.RateLimitError = Exception  # use generic so no real import

        result = complete(
            [{"role": "user", "content": "hello"}],
            model_id="claude-3-5-sonnet-20241022",
        )

        assert isinstance(result, ModelResponse)
        assert result.content == "hello back"
        assert result.model_id == "claude-3-5-sonnet-20241022"
        assert result.finish_reason == FinishReason.stop
