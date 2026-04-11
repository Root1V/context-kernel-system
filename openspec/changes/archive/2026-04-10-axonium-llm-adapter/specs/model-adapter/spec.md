## MODIFIED Requirements

### Requirement: Model adapter abstracts provider-specific APIs
The model adapter SHALL expose `complete(messages, model_id, tools) -> ModelResponse` as a unified interface. All provider-specific API calls (OpenAI, Anthropic, and local llama-server via Axonium) MUST be encapsulated inside adapter implementations. No other package SHALL import `openai`, `anthropic`, or `axonium` SDKs directly.

#### Scenario: OpenAI completion succeeds
- **WHEN** `complete` is called with `model_id="gpt-4o"` and valid messages
- **THEN** a `ModelResponse` is returned with `content`, `usage` (prompt/completion/total tokens), and `finish_reason`

#### Scenario: Anthropic completion succeeds
- **WHEN** `complete` is called with `model_id="claude-3-5-sonnet-20241022"` and valid messages
- **THEN** a `ModelResponse` is returned with the same `ModelResponse` schema as OpenAI, normalized

#### Scenario: Local llama-server completion succeeds
- **WHEN** `complete` is called with `model_id="local/mistral-7b"` and valid messages
- **THEN** a `ModelResponse` is returned with `content`, `usage`, and `finish_reason`, normalized to the same schema as cloud providers

#### Scenario: Unsupported model raises error
- **WHEN** `complete` is called with an unrecognized `model_id`
- **THEN** the adapter raises `UnsupportedModelError` without making any API call
