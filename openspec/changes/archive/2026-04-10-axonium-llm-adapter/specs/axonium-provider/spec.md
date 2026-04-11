## ADDED Requirements

### Requirement: AxoniumAdapter wraps local llama-server via Axonium SDK
The system SHALL expose an `AxoniumAdapter` class inside `packages/model_adapter` that, given a `model_id` prefixed with `local/`, invokes the Axonium SDK's `LlamaAdapter` to run inference against a locally-running `llama-server`. The adapter MUST strip the `local/` prefix before passing the model name to `LlamaAdapter`. Authentication MUST be handled transparently via Axonium's `TokenManager` using `LLM_BASE_URL`, `LLM_USERNAME`, and `LLM_PASSWORD` environment variables.

#### Scenario: Successful local inference
- **WHEN** `AxoniumAdapter.complete(messages, model_id="local/mistral-7b", tools=None)` is called and llama-server returns a completion
- **THEN** a `ModelResponse` is returned with `content` set to the response text, `usage` populated with prompt/completion/total token counts, `finish_reason` set to `FinishReason.stop`, and `model_id` set to `"local/mistral-7b"`

#### Scenario: Tools not supported
- **WHEN** `AxoniumAdapter.complete(messages, model_id="local/mistral-7b", tools=[...])` is called with a non-empty `tools` list
- **THEN** the adapter raises `NotImplementedError` before making any network call

#### Scenario: Server returns 429 rate limit
- **WHEN** the llama-server responds with an HTTP 429 or Axonium raises a rate-limit error
- **THEN** the adapter raises `model_adapter.RateLimitError` with `retry_after_seconds >= 0`

#### Scenario: Axonium SDK not installed
- **WHEN** `AxoniumAdapter` is instantiated in an environment where the `axonium` package is absent
- **THEN** an `ImportError` is raised with a message directing the user to install axonium via `uv add --find-links`

### Requirement: Local model IDs are registered with a context limit
The system SHALL register every `local/*` model in `limits.py` with a default context window of `32_768` tokens. `get_context_limit("local/mistral-7b")` MUST return `32_768`. `supported_models()` MUST include all registered `local/*` model IDs.

#### Scenario: Context limit for local model
- **WHEN** `get_context_limit("local/mistral-7b")` is called
- **THEN** it returns `32_768`

#### Scenario: Local models appear in supported list
- **WHEN** `supported_models()` is called
- **THEN** the returned list includes `"local/mistral-7b"` and other registered local models
