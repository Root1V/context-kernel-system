# Context Kernel: Global System Invariants

## Purpose
This document establishes the **Architectural Invariants** of the *Context Kernel* system. An invariant is an absolute axiomatic rule that MUST be upheld regardless of feature evolution or implementation changes.

If an AI subagent or developer proposes a change that breaches an invariant, the proposal MUST be automatically **REJECTED** unless accompanied by a formally accepted Architecture Decision Record (ADR) explicitly mutating these rules.

---

### Category 1: Cognitive Boundaries & High-Signal Constraints

#### Invariant 1: The Model Reads ONLY Assembled Context
The inference layer (LLM) MUST NEVER directly query raw databases, full uncompressed chat histories, or unfiltered tool outputs. It strictly consumes an immutably curated `Context Assembly` generated specifically for that turn.

#### Invariant 2: Active Context < Total System Memory
The system's total knowledge payload is mathematically larger than the LLM's active context window. Therefore, explicit policies for **Selection, Compaction, Retrieval, and Pinning** are non-negotiable requirements before introducing data streams.

#### Invariant 3: Memory is Strictly Layered
Memory is not a monolithic text blob. The architecture mandates an explicit separation into:
- **Message Buffer**: Immediate short-term turn history.
- **Core Memory**: Always-in-prompt, highly curated persistent state.
- **Recall Memory**: Short-term structured logs.
- **Archival Memory**: Vectorized, highly summarized semantic knowledge facts.

#### Invariant 4: Core Memory Must Remain Small & High-Signal
Core memory token footprints cannot grow unbounded. Every promotion policy targeting the `Core` layer must be extremely conservative and natively testable for token bloat eviction.

#### Invariant 5: Minimum High-Signal Context (Token Economy)
The overarching system goal is NOT to inject the maximum possible context, but the *minimum mathematically required* set of high-signal tokens to complete the current task. More tokens do not equate to better reasoning.

---

### Category 2: Modularity & Absolute Separation of Concerns

#### Invariant 6: The Assembler is the Exclusive Composer
The `context_assembler` package is the ONLY domain authorized to format, order, and inject data into the final prompt topology. Context composition is strictly forbidden inside HTTP endpoints, memory managers, or retrieval modules.

#### Invariant 7: The Model Adapter is the Exclusive Provider Gateway
Only the `model_adapter` package contains logic relating to specific LLM providers (OpenAI, Anthropic). No other module is permitted to hardcode provider-specific tokenization limits, system prompt formatting rules, or API signatures.

#### Invariant 8: External Context Enters ONLY Through Gates
Knowledge and side effects from the outside world enter the system strictly via the `retrieval` package or the `tool_runtime` (MCP Gateway). Ad-hoc HTTP requests or custom API clients scattered across arbitrary modules are forbidden.

#### Invariant 9: Tools NEVER Bypass Orchestration
Tools lack autonomy. The `orchestrator` solely dictates *when* a tool enters the cognitive loop. The `tool_runtime` safely executes the tool payload, but never governs the system's operational flow.

#### Invariant 10: Boundaries > Short-Term Velocity
It is mathematically preferable to delay a feature release than to compromise modular boundaries. The repository structure must always support simultaneous, parallel modifications by multiple AI agents without merge-conflict chaos.

---

### Category 3: Explicit State, Tracing & QA

#### Invariant 11: State is Explicit, Never Implicit
System state must not be inferred from raw message history or loose variables. All states MUST have explicit, schema-backed (`Pydantic` / `JSON`) representations for:
- Session State
- Task/Execution State
- Active Artifacts / Open Files

#### Invariant 12: Policies Must Be Deterministically Testable
All architecture logic relating to Context Assembly (Ordering, Compaction), Memory (Promotion), and Retrieval (Selection) MUST possess corresponding `pytest` coverage evaluating logical edge cases. "Fuzzy" prompt-engineering without contract tests is forbidden.

#### Invariant 13: Sleep-Time Compute Preserves Traceability
Offline background jobs (Compaction, Summarization, Eviction) must never destroy data without persisting a traceable audit log or metadata linkage preserving the absolute origin of the facts.

#### Invariant 14: Documentation is Code
Documentation is not an afterthought; it is the runtime environment for AI subagents. Changes to logic contracts MUST trigger an immediate synchronization of the localized `AGENTS.md` and `README.md` boundaries.

#### Invariant 15: The Kernel Remains Payload-Agnostic
The core orchestration engine must remain universally reusable across discrete use-cases. Domain-specific business logic enters the system strictly as external MCP Tools or isolated rule-profiles, never by mutating the kernel's core execution algorithms.

---

## ⛔ The Evaluator's "Pull Request" Checklist

Before an AI agent or developer can merge code into the main branch, the execution log MUST mathematically pass this evaluation gate:

1. Did you mutate variables outside your assigned isolated module boundary?
2. Did you hardcode provider-specific logic (e.g., Anthropic limits) outside of `model_adapter`?
3. Are you injecting string data into the prompt outside of `context_assembler`?
4. Are you querying a database or an external API without passing through `storage`, `retrieval`, or `tool_runtime`?
5. Does the `Core Memory` footprint grow unconditionally without an eviction policy?
6. Does the implementation lack strict typing (`mypy`) or `pytest` coverage for its decisions?
7. Did you neglect to update the local `AGENTS.md` after modifying an interface?

*If the answer to **ANY** of the above is "YES", the Pull Request must be instantly REJECTED.*
