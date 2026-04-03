## ADDED Requirements

### Requirement: Model adapter abstracts provider-specific APIs
The model adapter SHALL expose `complete(messages, model_id, tools) -> ModelResponse` as a unified interface. All provider-specific API calls (OpenAI, Anthropic) MUST be encapsulated inside adapter implementations. No other package SHALL import `openai` or `anthropic` SDKs directly.

#### Scenario: OpenAI completion succeeds
- **WHEN** `complete` is called with `model_id="gpt-4o"` and valid messages
- **THEN** a `ModelResponse` is returned with `content`, `usage` (prompt/completion/total tokens), and `finish_reason`

#### Scenario: Anthropic completion succeeds
- **WHEN** `complete` is called with `model_id="claude-3-5-sonnet-20241022"` and valid messages
- **THEN** a `ModelResponse` is returned with the same `ModelResponse` schema as OpenAI, normalized

#### Scenario: Unsupported model raises error
- **WHEN** `complete` is called with an unrecognized `model_id`
- **THEN** the adapter raises `UnsupportedModelError` without making any API call

### Requirement: Token counting is exposed as a public utility
The model adapter SHALL expose `count_tokens(text, model_id) -> int` and `get_context_limit(model_id) -> int`. These are the ONLY token-counting functions in the system.

#### Scenario: Token count matches provider's encoding
- **WHEN** `count_tokens("Hello, world!", model_id="gpt-4o")` is called
- **THEN** the returned count matches the token count produced by the model's official tokenizer

#### Scenario: Context limit is model-specific
- **WHEN** `get_context_limit("gpt-4o")` is called
- **THEN** it returns `128000` (or the current published limit for that model)

### Requirement: Rate limit errors are surfaced as typed exceptions
The model adapter SHALL catch provider rate-limit HTTP errors and raise `RateLimitError` with `retry_after_seconds` populated. The orchestrator is responsible for deciding retry behavior.

#### Scenario: Rate limit from provider becomes RateLimitError
- **WHEN** the provider API returns a 429 response
- **THEN** the adapter raises `RateLimitError` with a non-negative `retry_after_seconds` value
