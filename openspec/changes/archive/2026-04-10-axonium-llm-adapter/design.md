## Context

`packages/model_adapter` exposes a single `complete(messages, model_id, tools) -> ModelResponse` function that routes requests to either `OpenAIAdapter` or `AnthropicAdapter` based on the `model_id` prefix. Both existing adapters call cloud APIs that require keys and billing. The Axonium SDK (`https://github.com/Root1V/axonium-sdk`) is a first-party library that wraps `llama-server` (OpenAI-compatible `/v1/chat/completions`) behind managed Bearer-token authentication, a circuit breaker, and optional Langfuse observability. Integrating it as a third adapter adds an offline-capable, cost-free local inference path.

The project runs tests with system Python 3.9 but tooling (ruff, mypy) with `.venv` Python 3.13. Axonium SDK requires `python >= 3.13`, which creates an import-time compatibility constraint.

## Goals / Non-Goals

**Goals:**
- Add `AxoniumAdapter` inside `packages/model_adapter` that satisfies the same `complete()` contract.
- Route any `model_id` prefixed with `local/` to `AxoniumAdapter` (e.g., `local/mistral-7b`).
- Surface Axonium auth/circuit-breaker errors as the system's typed `RateLimitError` or `RuntimeError`.
- Keep the change fully additive — existing call-sites are unaffected.

**Non-Goals:**
- Tool-call support (llama.cpp / llama-server does not natively support OpenAI function-calling in this setup).
- Streaming responses.
- Embeddings via this adapter.
- Modifying the Axonium SDK source.
- Updating the pre-push hook to switch test runners for model_adapter.

## Decisions

### 1. Model ID prefix convention: `local/<model-name>`

**Chosen**: reserve the `local/` namespace in `limits.py` for any model served by the local llama-server (e.g., `local/mistral-7b-instruct`, `local/llama3-8b`).

**Alternatives considered**:
- Separate env-var flag (`USE_LOCAL=true`): too implicit; breaks the model-routing contract.
- New keyword arg to `complete()`: would touch every call-site — unnecessary.

The prefix is declarative and visible at the call-site, consistent with how OpenAI uses `gpt-*` and Anthropic uses `claude-*`.

### 2. Lazy import of the Axonium SDK

**Chosen**: `import axonium` is deferred to inside `AxoniumAdapter.__init__`. The module-level `axonium_adapter.py` does **not** import axonium at the top.

**Rationale**: Axonium requires Python 3.13. Test suites using `python3` (3.9) would fail at import time even if no `local/*` model is requested. Lazy import means the module loads fine on 3.9; instantiation only fails if axonium is genuinely absent from the runtime.

**Consequence**: tests for `AxoniumAdapter` must use `pytest.importorskip("axonium")` and be run inside the venv (via `uv run pytest`).

### 3. Singleton instantiation, lazy

**Chosen**: `_axonium: AxoniumAdapter | None = None` at module level in `__init__.py`, instantiated on first request (matching the lazy-import strategy above).

**Rationale**: consistent with existing eager singletons for OpenAI/Anthropic but safe across runtime environments. Avoids importing Axonium at import time of the package.

### 4. Response normalization

Axonium's `LlamaAdapter.chat()` returns an object with `response.choices[0].message.content` and `response.usage` (an Axonium `Usage` model with `prompt_tokens`, `completion_tokens`, `total_tokens`).

**Mapping**:

| Axonium field | System field |
|---|---|
| `choices[0].message.content` | `ModelResponse.content` |
| `usage.prompt_tokens` | `TokenUsage.prompt_tokens` |
| `usage.completion_tokens` | `TokenUsage.completion_tokens` |
| `usage.total_tokens` | `TokenUsage.total_tokens` |
| `choices[0].finish_reason` (str) | `FinishReason` enum (default `stop`) |
| *model_id argument* | `ModelResponse.model_id` |

### 5. Error mapping

| Axonium exception | System exception |
|---|---|
| `axonium.exceptions.RateLimitError` or HTTP 429 | `model_adapter.RateLimitError` |
| Any other `Exception` during inference | re-raise as-is (`RuntimeError` or original) |

## Risks / Trade-offs

- **Python version mismatch** → Axonium requires 3.13; project tests use Python 3.9. Mitigation: lazy import + `pytest.importorskip` in tests; tests for `AxoniumAdapter` run via `uv run pytest` (3.13 venv).
- **llama-server must be running** → `AxoniumAdapter` will fail at inference time if `LLM_BASE_URL` is unreachable. Mitigation: tests mock `LlamaAdapter`; integration tests are optional / require local server.
- **No tool-call support** → calling `complete()` with `tools` on a `local/*` model silently ignores `tools`. Mitigation: document clearly; `AxoniumAdapter.complete()` raises `NotImplementedError` if `tools` is non-empty.
- **Axonium installed via wheel** → not on PyPI; must be built locally and added via `uv add --find-links`. Mitigation: document exact steps in tasks; add `dist/` to venv path.

## Migration Plan

1. Build the Axonium wheel locally (`uv build` inside axonium-sdk clone).
2. Run `uv add --find-links <path-to-dist> axonium` in this repo.
3. Add env vars `LLM_BASE_URL`, `LLM_USERNAME`, `LLM_PASSWORD` to `.env`.
4. No existing call-sites change; the new path is only activated by `local/*` model IDs.
5. Rollback: remove `axonium_adapter.py`, revert `__init__.py` and `limits.py`. Existing tests continue to pass.

## Open Questions

- What is the default context limit to register for `local/*` models? Llama.cpp defaults to 4096 but models like Mistral support 32K. **Decision**: register a configurable default of `32_768` overridable via `LOCAL_MODEL_CONTEXT_LIMIT` env var (out of scope for this change — use hardcoded `32_768` for now and revisit when more local models are registered).
