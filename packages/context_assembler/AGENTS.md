# Context Assembler - AGENTS.md

## Repository Mission & Module Context
This module acts as the **Context Assembler**. Its primary responsibility is to construct the final, optimized active context payload that will be sent to the Language Model (LLM). It operates as a set of pure, deterministic functions that take raw inputs (state, memory, retrieval, tools) and format them into a coherent, budget-aware prompt structure.

## Core Directives for Agentic Development
When modifying code in this package, you MUST adhere to the following principles based on robust OpenCode and agentic AI patterns:
1. **Pure Functions Over Side Effects**: The assembler should rarely perform I/O. All inputs must be injected.
2. **Determinism**: Context assembly must be 100% deterministic given the same inputs. Avoid relying on random numbers or unstable hash/dictionary orders.
3. **Type Safety**: Strictly define interfaces, schemas, and type hints for all data structures (e.g., `ContextAssembly`, `TokenBudget`, `ContextRequest`).
4. **Fail Gracefully**: If token limits are exceeded, use defined compaction strategies rather than truncating critical system prompts blindly.

## Module Boundaries (What it builds vs. What it DOES NOT build)

### ✅ Responsibilities (IN SCOPE)
- Formatting message sequences (system, user, assistant).
- Compacting, filtering, and summarizing overflowing raw context based on priority.
- Calculating and enforcing dynamic token budgets (`TokenBudget`).
- Ordering context sections deterministically.
- Assembling tool definitions into the context prompt.

### ❌ Anti-Patterns (OUT OF SCOPE)
- **NO Direct LLM Calls**: Do not import or call any model provider clients (e.g., OpenAI, Anthropic adapters).
- **NO Persistence**: Do not save or fetch data directly from databases, vector stores, or file storage.
- **NO Tool Execution**: Do not execute the tools; only format their schemas/definitions.
- **NO Direct HTTP/Network Activity**.

## Public Contracts & Interfaces
Any module interacting with the `context_assembler` should rely on explicit interfaces:
- `assemble_context(request: AssemblyRequest, state: ActiveState, memory: MemoryContext, retrieved: RetrievedContext, tools: list[Tool]) -> ContextAssembly`
- `estimate_budget(model_limits: ModelLimits, desired_output_tokens: int) -> TokenBudget`
- `compact_context(payload: RawPayload, budget: TokenBudget, policy: CompactionPolicy) -> CompactedPayload`

## Invariants & Design Rules
- **Output Reserve**: The context assembler MUST always reserve a guaranteed, non-negotiable token budget for the model's output.
- **Strict Ordering Priority**: System instructions > Tool definitions > Relevant Memory/Retrieval > Active Conversation State.
- **Deduplication**: Context must not contain duplicate information. If a summarized version of an episodic memory exists in the semantic memory, do not inject both redundantly.
- **Immutability**: Input data structures (state, memory) must not be mutated during the assembly processing.

## Dependencies

### Allowed Dependencies
- `core.models.interfaces` (Domain types)
- `model_adapter.limits` (Token counters and model limits metadata)
- `memory.public_interfaces` (Read-only data classes)
- `retrieval.public_interfaces` (Read-only data classes)
- `state.public_interfaces` (Session state data)

### Forbidden Dependencies
- `storage.repositories.*` (Direct database/vector store access)
- `clients.http` or `requests` module (Network side-effects)
- `tool_runtime.*` (Execution-layer adapters)

## Testing Strategy & Quality Assurance
All code in this module must be highly testable. When creating logic changes, ensure:
1. **Unit Tests (Compaction)**: Mock token limits and verify that the correct, lower-priority context is dropped or parameterized.
2. **Unit Tests (Ordering)**: Assert that final arrays of messages respect the strict deterministic ordering invariant.
3. **Golden Tests / Snapshot Tests**: Run complex inputs against expected final JSON payloads (Snapshot testing) to prevent accidental prompt mutations.
4. **Token Counting Mocks**: Ensure token counting logic is cleanly abstracted allowing tests to run fast without loading expensive LLM tokenizers whenever possible.

## Documentation Requirements
- Document the rationale behind compaction rules.
- Maintain up-to-date docstrings on public contracts (`assemble_context`).
