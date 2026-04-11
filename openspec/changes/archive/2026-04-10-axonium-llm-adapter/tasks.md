## 1. Dependency Setup

- [x] 1.1 Clone or locate the Axonium SDK repo locally and run `uv build` to produce a wheel
- [x] 1.2 Run `uv add --find-links <path-to-axonium-dist> axonium` in this repo to install the wheel into the venv
- [x] 1.3 Verify the install: `uv run python -c "import axonium; print(axonium.__version__)"`

## 2. Model Registry

- [x] 2.1 Add `local/*` model entries to `_CONTEXT_LIMITS` in `packages/model_adapter/model_adapter/limits.py` (start with `local/mistral-7b-instruct` → `32_768`)
- [x] 2.2 Add `is_local(model_id: str) -> bool` helper in `limits.py` that returns `True` for any model_id starting with `local/`

## 3. AxoniumAdapter Implementation

- [x] 3.1 Create `packages/model_adapter/model_adapter/axonium_adapter.py` with `AxoniumAdapter` class
- [x] 3.2 Implement `AxoniumAdapter.__init__` with lazy import of `axonium.LlamaAdapter`; read `LLM_BASE_URL`, `LLM_USERNAME`, `LLM_PASSWORD` from env
- [x] 3.3 Implement `AxoniumAdapter.complete(messages, model_id, tools)` — strip `local/` prefix, call `LlamaAdapter.chat()`, normalize response to `ModelResponse`
- [x] 3.4 Raise `NotImplementedError` when `tools` is non-empty
- [x] 3.5 Map Axonium rate-limit / connection errors to `model_adapter.RateLimitError` or re-raise as `RuntimeError`

## 4. Routing Update

- [x] 4.1 Update `packages/model_adapter/model_adapter/__init__.py` to import `AxoniumAdapter` and add a lazy `_axonium` singleton
- [x] 4.2 Update `_get_adapter()` in `__init__.py` to route `local/*` model IDs to `_axonium`
- [x] 4.3 Add `AxoniumAdapter` to `__all__` in `__init__.py`

## 5. Tests

- [x] 5.1 Create `packages/model_adapter/tests/test_axonium_adapter.py` with `pytest.importorskip("axonium")` guard
- [x] 5.2 Write unit test: successful `complete()` call using a mock `LlamaAdapter` (verify `ModelResponse` normalization)
- [x] 5.3 Write unit test: `tools` non-empty raises `NotImplementedError`
- [x] 5.4 Write unit test: Axonium SDK missing raises `ImportError` with helpful message
- [x] 5.5 Write unit test: `is_local("local/mistral-7b-instruct")` returns `True`; `is_local("gpt-4o")` returns `False`
- [x] 5.6 Write unit test: `get_context_limit("local/mistral-7b-instruct")` returns `32_768`

## 6. Environment & Docs

- [x] 6.1 Add `LLM_BASE_URL`, `LLM_USERNAME`, and `LLM_PASSWORD` entries to `.env.example`
- [x] 6.2 Run `uv run ruff check packages/model_adapter/ && uv run ruff format --check packages/model_adapter/` and fix any issues
- [x] 6.3 Run `uv run mypy packages/model_adapter/` and fix any type errors
- [x] 6.4 Run `uv run pytest packages/model_adapter/tests/ -v` and confirm all tests pass
