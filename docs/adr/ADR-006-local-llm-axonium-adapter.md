# ADR-006: Local LLM Inference via Axonium SDK Adapter

- **Status**: Accepted
- **Date**: 2026-04-10
- **Impacts**: `packages/model_adapter`

## Context

The system's two cloud providers (OpenAI, Anthropic) require external billing and are unavailable when API quotas are exhausted. A local inference path is needed for offline-capable, cost-free development and fallback operation. The Axonium SDK (`https://github.com/Root1V/axonium-sdk`) is a first-party library that wraps `llama-server` (OpenAI-compatible `/v1/chat/completions`) behind managed Bearer-token authentication and a circuit breaker — allowing local LLMs to be consumed through the same interface as cloud providers.

Additionally, Axonium requires Python ≥ 3.13, while the project's test suite runs on Python 3.9 (system). This created an import-time compatibility challenge that influenced the implementation strategy.

## Decision

1. **New `AxoniumAdapter`** in `packages/model_adapter/model_adapter/axonium_adapter.py` that wraps `axonium.LlamaAdapter` and normalizes its response to the system's `ModelResponse` contract.

2. **`local/<model-name>` prefix convention** for local model IDs (e.g., `local/mistral-7b-instruct`). The routing function `_get_adapter()` dispatches any `local/*` model ID to `AxoniumAdapter`. This is consistent with how `gpt-*` routes to `OpenAIAdapter` and `claude-*` routes to `AnthropicAdapter`.

3. **Lazy import of the Axonium SDK** inside `AxoniumAdapter.__init__`. The module loads cleanly under Python 3.9 (test runner) — the `ImportError` is only raised if a `local/*` model is actually requested in an environment without axonium installed.

4. **Lazy singleton** for the `AxoniumAdapter` instance in `__init__.py` (`_axonium = None`, instantiated on first `local/*` request), consistent with the existing eager singletons for OpenAI/Anthropic but safe across Python versions.

5. **Tool-call requests raise `NotImplementedError`** — llama-server does not support OpenAI function-calling in this configuration. Callers attempting to pass `tools` to a `local/*` model get an explicit error rather than silent omission.

6. **`mypy python_version` updated to `3.13`** to match the `.venv` interpreter used by the pre-push hook, eliminating false-positive syntax errors from third-party packages that use Python 3.10+ syntax.

## Consequences

- **Positive**: The system can now run inference locally via any GGUF model served by `llama-server`, with no cloud billing required.
- **Positive**: Authentication (Bearer token via `llm-security`) is fully transparent — managed by the Axonium SDK's `TokenManager`.
- **Positive**: Fully additive — no existing `complete()` call-sites change. `UnsupportedModelError` is still raised for any unrecognized model ID.
- **Positive**: Tests for `AxoniumAdapter` auto-skip on Python 3.9, pass on Python 3.13, and mock `LlamaAdapter` for isolation.
- **Limitation**: No tool-call support for local models. Adding function-calling support would require a version of llama-server with native OpenAI tools compatibility.
- **Limitation**: `axonium` is not on PyPI and must be installed via `uv add --find-links` from a locally-built wheel.
- **Limitation**: `get_context_limit` returns `32_768` for all registered `local/*` models. Per-model context limits should be configured explicitly as more models are registered.
