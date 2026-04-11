## Why

The system currently supports only cloud LLM providers (OpenAI, Anthropic), both of which require external billing and can be unavailable due to quota exhaustion. Integrating the Axonium SDK enables inference against locally-running `llama-server` instances, giving the system an offline-capable, cost-free fallback provider with managed authentication, circuit breaker protection, and optional Langfuse observability — all already implemented inside Axonium.

## What Changes

- Add `packages/model_adapter/model_adapter/axonium_adapter.py` — a new `AxoniumAdapter` class that wraps `axonium.LlamaAdapter`, translating the Axonium response shape to the system's `ModelResponse` contract.
- Extend `packages/model_adapter/model_adapter/limits.py` with a local-model registry keyed on the `local/<model-name>` prefix convention.
- Update `packages/model_adapter/model_adapter/__init__.py` to route `local/*` model IDs to a singleton `AxoniumAdapter`.
- Expose `AxoniumAdapter` from the package's public `__init__` (for testing / direct instantiation).
- Add `axonium` as a production dependency in `pyproject.toml` via `uv add axonium`.
- Extend `.env.example` with the three new Axonium env vars (`LLM_BASE_URL`, `LLM_USERNAME`, `LLM_PASSWORD`).

## Capabilities

### New Capabilities
- `axonium-provider`: Adapter that bridges the Axonium SDK's `LlamaAdapter` to the system's `ModelAdapter` contract, routing `local/*` model IDs to a local llama-server via managed Bearer-token authentication.

### Modified Capabilities
- `model-adapter`: New routing logic and new scenarios — `local/*` model IDs resolve to `AxoniumAdapter`; `UnsupportedModelError` still raised for unknown IDs; `RateLimitError` surfaced for server-side 429s from llama-server.

## Impact

- **`packages/model_adapter/`**: new file `axonium_adapter.py`; changed files `limits.py`, `__init__.py`.
- **`pyproject.toml`**: new production dependency `axonium`.
- **`.env.example`**: three new environment variable entries.
- **No breaking changes** — existing `complete()` call-sites are unaffected; new provider is additive.
- **External dependency**: Axonium SDK (`https://github.com/Root1V/axonium-sdk`) must be built and added via `uv add --find-links`.
- **Runtime dependency**: local `llama-server` + `llm-security` auth server (as documented in Axonium's own README).
