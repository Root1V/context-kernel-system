# Memory Subsystem - AGENTS.md

## Repository Mission & Module Context
This module serves as the **Memory Subsystem** for the agentic context kernel. Its primary responsibility is managing stateful memory across multiple tiers: **Core Memory** (immediate, high-signal active state), **Recall Memory** (short-term episodic trace), and **Archival Memory** (long-term, searchable semantic store). It also handles the complex workflow of **Memory Consolidation** (compressing raw histories into high-signal summaries over time).

## Core Directives for Agentic Development
When modifying code in this package, you MUST adhere to the following principles based on robust OpenCode and agentic AI patterns:
1. **Data Integrity Above All**: Memory transitions (e.g., compaction, archiving) are destructive by nature. Mutations must be strictly controlled, transactional where necessary, and comprehensively logged to prevent catastrophic amnesia (data loss).
2. **Boundary Enforcement**: This module strictly provides state storage, retrieval, and structural management. It contains **ZERO** cognitive logic or LLM orchestration.
3. **Type Safety**: Use robust domain schemas (e.g., Pydantic models, strictly typed dataclasses) for all memory objects: `CoreMemoryBlock`, `RecallEvent`, `ConsolidationPatch`.
4. **Event-Sourced Nature**: `Recall Memory` operates as an append-only ledger for traceability.

## Module Boundaries (What it builds vs. What it DOES NOT build)

### ✅ Responsibilities (IN SCOPE)
- **Core Memory Operations**: Reading and selectively patching active operational state.
- **Recall Memory Operations**: Appending episodic events sequentially and fetching recent history.
- **Archival Memory Operations**: Managing robust storage adapters for long-term semantic retrieval.
- **Consolidation Workflows**: Compressing `Recall` blocks into `Archival` or updating `Core` profiles when triggers are met.

### ❌ Anti-Patterns (OUT OF SCOPE)
- **NO Prompt Assembly**: Do not format contexts or build JSON prompt arrays for models (that belongs in `context_assembler`).
- **NO Direct LLM Integrations**: Do not make API calls to evaluate or summarize memory (this module relies on an injected `model_adapter` or an orchestration layer invoking the LLM to get the summarized data).
- **NO HTTP Routing/API Definitions**: This is a backend logical module; it does not define HTTP endpoints.

## Public Contracts & Interfaces
Any external module interacting with `memory` should rely strictly on these explicit interfaces:
- `read_core_memory(session_id: str) -> CoreMemoryContainer`
- `update_core_memory(session_id: str, patch: MemoryPatch) -> CoreMemoryContainer`
- `append_recall_event(session_id: str, event: RecallEvent) -> None`
- `consolidate_memory(session_id: str) -> ConsolidationResult`

*(Note: Data extraction for semantic retrieval should pass through dedicated `retrieval` modules that interface with the archival store).*

## Invariants & Design Rules
- **Core Memory Constraint**: Core memory must ALWAYS be strictly bounded (e.g., limit token size), holding only high-signal persistence necessary to bootstrap the persona/current task.
- **Recall Traceability**: Episodic recall memory cannot be mutated natively—it is an append-only log until it is fully consolidated and pruned.
- **Archival Discoverability**: Archival memory must implement necessary abstractions (vector/metadata bounds) to be consistently filterable and semantically recoverable.
- **Lossless Consolidation Principle**: The system must NOT permanently delete short-term recall traces unless their synthesized equivalent has been successfully persisted in archival or core.

## Dependencies

### Allowed Dependencies
- `core.models.interfaces` (Domain types handling memory models)
- `storage.repositories.*` (Interfaces to the database, vector DB, or file stores for persistence)

### Forbidden Dependencies
- `context_assembler.*` (Memory provides data, it doesn't construct prompts)
- `model_adapter.clients` (Memory operations shouldn't directly instantiate external LLM REST calls)
- `tool_runtime.*`

## Testing Strategy & Quality Assurance
All code in this module must be highly testable. When creating logic changes, ensure:
1. **Integration Tests (Mutations)**: Ensure that `update_core_memory` properly patches state without overwriting adjacent fields.
2. **Unit Tests (Consolidation)**: Mock the consolidation function output and verify that it adheres to the Lossless Consolidation Principle.
3. **Repository Mocks**: Use explicit mocks/fake-repos to test logic isolating it from actual DB latency or state issues.
4. **Golden Tests**: Regression test the serialization of complex memory JSON structures to prevent schema-breaking changes.
