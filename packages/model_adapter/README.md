# model_adapter

## Purpose

`model_adapter` is the provider boundary for language models.

It is the only module that should know:
- how to talk to a specific provider
- how that provider expects messages
- model-specific limits
- token estimation helpers
- provider-specific response normalization

This module protects the rest of the system from provider-specific details.

---

## Why this module exists

Without a dedicated model adapter, provider details tend to leak into:
- APIs
- orchestrator code
- context assembler
- tests
- memory policies

That makes the system fragile and difficult to evolve.

`model_adapter` exists so that the rest of the runtime can stay focused on:
- state
- memory
- retrieval
- context composition
- tool orchestration

while this module handles:
- provider formatting
- call semantics
- limits
- response normalization

---

## Mental model

```text
context assembly
     |
     v
model_adapter
     |
     +-- normalize request
     +-- apply provider format
     +-- know model limits
     +-- estimate token usage
     +-- call provider
     +-- normalize response
     |
     v
rest of the system gets a stable interface

Responsibilities
1. Provider abstraction
Expose a stable internal interface even if underlying providers differ.
2. Request normalization
Transform the internal assembly into provider-compatible input.
3. Response normalization
Return a normalized result structure:
content
usage
raw metadata
status/errors
4. Limits and budgeting support
Expose model-specific limits such as:
total context window
output limits
optional tool/function calling capabilities
5. Token helpers
Provide estimation helpers for budgeting and overflow handling.

What this module does NOT own
what context should be selected
how memory is updated
whether retrieval should happen
whether a tool should be called
persistence of application state
Those responsibilities belong elsewhere.

Package layout
model_adapter/
|
|-- base.py
|-- openai_adapter.py        # Cloud — gpt-* models
|-- anthropic_adapter.py     # Cloud — claude-* models
|-- axonium_adapter.py       # Local — local/* models via llama-server + Axonium SDK
|-- tokenizer.py
`-- limits.py

Suggested public interface
A stable internal interface might look conceptually like:
get_model_limits(model_name) -> ModelLimits
estimate_tokens(payload, model_name) -> int
generate(model_name, assembly, options) -> ModelResponse
supports_tools(model_name) -> bool
The exact shape may evolve, but the role must stay stable.

Key data structures
ModelLimits
Should capture at least:
model name
total context window
max output tokens if relevant
tool support flags if relevant
ModelResponse
Should capture at least:
normalized text/content
structured response if used
usage info
provider metadata
error/status information

Design rules
This module is the only place that knows provider-specific message formatting.
The rest of the system should depend on stable internal types, not provider SDKs.
Token estimation logic should be centralized here or in helpers owned by this module.
New providers should be added by extending this module, not by branching the whole runtime.
Failures should be normalized enough for upstream modules to handle gracefully.

Model limits and budgeting
The context assembler depends on this module for model constraints.
That means:
if model limits change, this module updates them
the assembler reads limits through this boundary
no other module should hardcode provider-specific limits

Error handling
This module should normalize:
invalid request shape
provider timeouts
unsupported features
transient provider errors
context window overflow at provider level
Upstream modules should receive consistent errors or statuses.

Testing strategy
Unit tests
request normalization
response normalization
limits helpers
token estimator helpers
Contract tests
adapters return the same internal response shape
limits are exposed consistently
Non-goal
Do not require live provider calls for all tests.
Use stubs/fakes where possible.

Extensibility
When adding a new provider:
implement adapter in this module
map provider request format
normalize provider response
define limits exposure
add tests
do not change orchestrator or assembler unless the internal contract truly needs to evolve

Supported providers
| Prefix | Provider | Adapter | Notes |
|---|---|---|---|
| `gpt-*` | OpenAI | `OpenAIAdapter` | Cloud — requires `OPENAI_API_KEY` |
| `claude-*` | Anthropic | `AnthropicAdapter` | Cloud — requires `ANTHROPIC_API_KEY` |
| `local/*` | llama-server (Axonium SDK) | `AxoniumAdapter` | Local — requires `LLM_BASE_URL`, `LLM_USERNAME`, `LLM_PASSWORD` and a running llama-server. No tool-call support. See ADR-006. |

To use a local model, pass `model_id="local/<model-name>"` to `complete()`.
The `local/` prefix is stripped before forwarding to llama-server.
Authentication (Bearer token) is managed transparently by the Axonium SDK.
Install the wheel: `uv add --find-links <path-to-dist> axonium` (Python 3.13 venv only).

Practical checklist
Before merging changes here, ask:
Did provider-specific logic stay inside this module?
Does the rest of the system still consume normalized types?
Are limits exposed clearly?
Can the assembler keep working without knowing provider internals?
Are errors normalized enough for upper layers?
