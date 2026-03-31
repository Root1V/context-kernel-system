# AGENTS.md — `packages/model_adapter`

## Module Mission
`model_adapter` is the **exclusive provider abstraction boundary** of the *Context Kernel* system. It is the ONLY module permitted to contain LLM provider-specific logic, message formatting rules, tokenization algorithms, or API client code.

Its primary mandate is to answer:
> *"How do we communicate with a specific LLM provider without contaminating the rest of the runtime with vendor-specific implementation details?"*

---

## Strict Boundaries

### This module IS responsible for:
- Exposing a stable, provider-agnostic internal interface for the Orchestrator and Assembler.
- Translating the internal `ContextAssembly` payload into provider-compatible request formats.
- Executing the raw inference call against the chosen LLM provider.
- Normalizing raw provider responses into stable internal `ModelResponse` types.
- Centralizing all token estimation and context window limit logic.
- Translating transient provider errors into stable, upstream-readable error types.

### This module is NOT responsible for:
- **Context selection or ordering** → Belongs to `packages/context_assembler`
- **Memory persistence or promotion** → Belongs to `packages/memory`
- **Retrieval decision-making** → Belongs to `packages/retrieval`
- **Tool execution or MCP routing** → Belongs to `packages/tool_runtime`
- **Session or task state persistence** → Belongs to `packages/state`
- **HTTP request validation** → Belongs to `apps/api`

---

## Public Contract (Stable Interface)

The module MUST expose the following stable, typed Python interface. The exact method signatures may evolve, but the behavioral contracts MUST remain consistent:

```python
def get_model_limits(model_name: str) -> ModelLimits:
    """Returns the total context window, max output tokens, and capability flags."""

def estimate_tokens(payload: str | list, model_name: str) -> int:
    """Returns an integer token count estimate for the given payload."""

def generate(
    model_name: str,
    assembly: ContextAssembly,
    options: GenerationOptions
) -> ModelResponse:
    """Executes the inference call and returns a normalized response."""

def supports_tools(model_name: str) -> bool:
    """Returns whether the model supports function/tool calling."""
```

---

## Core Data Contracts

### `ModelLimits`
```python
@dataclass
class ModelLimits:
    model_name: str
    context_window: int          # Total tokens (input + output)
    max_output_tokens: int       # Maximum generation length
    supports_tools: bool         # Function calling capability
    supports_vision: bool        # Multi-modal capability
```

### `ModelResponse`
```python
@dataclass
class ModelResponse:
    content: str                 # Normalized text response
    structured_output: dict | None  # Parsed structured output if requested
    prompt_tokens: int
    completion_tokens: int
    stop_reason: str             # e.g. "stop", "length", "tool_call"
    provider: str                # "openai" | "anthropic" | etc.
    raw_metadata: dict           # Full raw provider response for tracing
    error: str | None            # Normalized error message if applicable
```

---

## Invariants

1. **Provider Monopoly**: No other module is permitted to import or instantiate LLM provider SDK clients. All provider access is exclusively routed through this module.
2. **Format Containment**: Provider-specific message formatting (`ChatML`, Anthropic's `messages` format, etc.) must never appear outside this module.
3. **Limit Centralization**: Any module needing context window constraints reads them via `get_model_limits()`. Hardcoded limits in the assembler or orchestrator are forbidden.
4. **Response Normalization**: Upstream components (`orchestrator`, `observability`) MUST ONLY receive stable `ModelResponse` objects, never raw provider SDK response objects.
5. **Token Estimation Authority**: All token estimation logic lives here. No other module estimates tokens independently.
6. **Error Translation**: Network timeouts, rate-limits, and provider validation errors must be caught here and re-raised as normalized internal exceptions.

---

## Permitted Dependencies

| Dependency | Reason |
|---|---|
| LLM Provider SDKs (`openai`, `anthropic`) | The core function of this module |
| `tiktoken` / provider tokenizers | For `estimate_tokens()` implementation |
| `packages/observability` | For tracing and latency logging |
| Global configuration / settings | For API keys and model defaults |

## Prohibited Dependencies

| Dependency | Reason |
|---|---|
| `packages/memory` | This module does not care how memories are stored |
| `packages/retrieval` | This module does not know what was retrieved |
| `packages/state` | This module does not manage session context |
| `packages/tool_runtime` | Tool dispatch is the orchestrator's responsibility |
| `apps/api` (routes) | No circular dependency with the HTTP layer |

---

## Suggested Package Layout

```text
packages/model_adapter/
│
├── __init__.py
├── base.py                 # Abstract base adapter (ModelAdapter ABC)
├── openai_adapter.py       # OpenAI-specific implementation
├── anthropic_adapter.py    # Anthropic-specific implementation
├── tokenizer.py            # Centralized token estimation helpers
├── limits.py               # ModelLimits definitions per model
└── types.py                # ModelResponse, GenerationOptions dataclasses
```

---

## Design Rules

### Rule 1: Assembler Decides What, Adapter Decides How
The `context_assembler` decides *what content* enters the payload. This module decides *how* that payload is formatted and transmitted to a specific vendor. Never confuse these two responsibilities.

### Rule 2: Provider Divergences Resolve Here
If two providers behave differently (e.g., system prompt placement), the conditional logic lives in the respective adapter class, NOT in the orchestrator or elsewhere in the runtime.

### Rule 3: New Provider = New Adapter Class
Adding support for a new model provider means creating a new adapter file (e.g., `gemini_adapter.py`) and registering it via the factory. It must NEVER require changes to the `orchestrator` or `context_assembler`.

### Rule 4: Outputs Must Serve Observability
All `ModelResponse` objects must contain sufficient metadata (`raw_metadata`, `prompt_tokens`, `completion_tokens`, `stop_reason`) so that `packages/observability` can produce a complete audit trace without needing any additional provider calls.

---

## Testing Requirements

| Test Type | Scope |
|---|---|
| **Unit** | `estimate_tokens()` accuracy, `ModelLimits` correctness, `ModelResponse` normalization logic. |
| **Contract** | All adapters (`openai`, `anthropic`) MUST return the identical `ModelResponse` shape. |
| **Stub/Fake** | Live provider API calls MUST be mockable. Test suites MUST pass 100% offline. |
| **Edge Cases** | Tiny context windows, maximum-fill payloads, tools not supported, transient 429 errors. |

---

## Sensitive Change Policy
Changes to this module's public interface can cascade to:
- `packages/context_assembler` (reads token limits)
- `packages/orchestrator` (calls `generate()`)
- `packages/observability` (consumes `ModelResponse`)

**Before merging any change here:**
1. Confirm the public contract (`ModelLimits`, `ModelResponse`) shape is still backward-compatible.
2. Confirm no provider-specific logic leaked into another module.
3. Confirm all adapters pass contract tests.
4. Confirm all tests pass offline (no live API calls in CI).

---

## Definition of Done
A change to `model_adapter` is complete when:
- [ ] The provider boundary is clean; no SDK imports exist outside this module.
- [ ] Limits are normalized and exposed via `get_model_limits()`.
- [ ] Responses are normalized to `ModelResponse` before returning.
- [ ] The change is unit-tested without live provider calls.
- [ ] The `AGENTS.md` is updated if the public interface changed.
