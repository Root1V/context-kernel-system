## Context

The Context Kernel repository has a complete monorepo skeleton — all packages (`context_assembler`, `memory`, `model_adapter`, `orchestrator`, `retrieval`, `state`, `storage`, `tool_runtime`, `observability`) and both applications (`apps/api`, `apps/worker`) are scaffolded. The architectural vision, invariants, and runtime flows are fully documented in `docs/`. However, all module implementations are either empty stubs or have incomplete, unconnected logic. No capability specs exist yet, so there are no verifiable contracts between packages. The system cannot fulfill its core purpose of assembling and delivering an optimal context payload in response to a user turn.

**Constraints from invariants:**
- The `context_assembler` is the ONLY authorized composer of prompt payloads.
- The `model_adapter` is the ONLY authorized LLM provider gateway.
- All external knowledge enters ONLY through `retrieval` or `tool_runtime`.
- State MUST be schema-backed (Pydantic), never inferred from raw history.
- Module boundaries must be strictly enforced — no cross-package imports outside declared public APIs.

## Goals / Non-Goals

**Goals:**
- Define behavioral specs (I/O contracts + acceptance scenarios) for all 9 core capabilities.
- Wire the Turn-Time DAG in `packages/orchestrator/` as a functional LangGraph graph using all packages.
- Implement the four-layer memory model in `packages/memory/` with promotion/eviction policies.
- Implement the Context Assembler with token-budget-aware section ordering and pinning.
- Implement the Between-Turn worker for async compaction and archival promotion.
- Enforce strict module boundaries: each package exposes exactly one public interface file.

**Non-Goals:**
- Production auth, rate-limiting, or multi-tenant infrastructure.
- Advanced MCP tool server implementations (only the gateway proxy boundary is scoped here).
- UI or client SDKs.
- Benchmark optimization of inference latency (follow-on work).

## Decisions

### Decision 1: Spec-first, test-driven implementation order
Each capability spec is written before any implementation. Tests are derived directly from spec scenarios. Implementation proceeds package by package, starting with leaf dependencies (no upstream imports) and working toward the DAG root.

**Order:** `model-adapter` → `state-management` → `layered-memory` → `retrieval-pipeline` → `tool-runtime-mcp` → `context-assembly` → `orchestrator-dag` → `api-layer` → `background-worker`

**Rationale:** This order respects the dependency graph. `model-adapter` and `state` have no internal dependencies. `memory` depends on `storage` and `state`. `context_assembler` depends on `memory`, `retrieval`, and `state`. The orchestrator wires everything.

**Alternative considered:** Implement all packages simultaneously across agents. Rejected — without contracts at module boundaries, parallel implementations produce interface mismatches.

---

### Decision 2: All inter-package contracts are Pydantic models
Every package exposes a public Python file (e.g., `packages/memory/memory/service.py`) whose functions accept and return Pydantic `BaseModel` instances. No `dict` or untyped primitives cross package boundaries.

**Rationale:** Pydantic models provide runtime validation, schema introspection, and auto-generated JSON schemas — essential for testability and for generating accurate spec scenarios. Enforces Invariant 11 (State is Explicit, Never Implicit).

**Alternative considered:** TypedDict. Rejected — no runtime validation, no JSON schema generation.

---

### Decision 3: LangGraph as the Turn-Time DAG runtime
The orchestrator is implemented as a LangGraph `StateGraph` where each node corresponds to a pipeline step (receive → load state → hydrate memory → retrieve → assemble → infer → tool loop → persist).

**Rationale:** LangGraph provides conditional branching, checkpointing, and reproducible DAG execution — critical for the conditional tool loop and deterministic state tracing. Documented in ADR-003.

**Alternative considered:** Plain async Python chain. Rejected — lacks checkpointing, branching, and observability hooks.

---

### Decision 4: Storage-backed memory layers (PostgreSQL + pgvector)
Core memory blocks, recall logs, and session state persist to PostgreSQL. Archival memory uses pgvector for embedding-based similarity search.

**Rationale:** Documented in ADR-002. Provides transactional guarantees for core memory mutations and ACID-compliant state writes. pgvector collocates vector embeddings with relational metadata, avoiding a separate vector database.

---

### Decision 5: Background worker uses a simple task-queue pattern
The `apps/worker/` process polls a job queue (initially a DB table) and executes compaction/archival jobs. No distributed broker (Celery/Redis) in this iteration.

**Rationale:** Avoids operational complexity in early stages. The job schema is defined via spec so the worker can be swapped to a proper queue broker without changing the orchestrator's dispatch logic.

---

### Decision 6: One `__init__.py` public surface per package
Each package defines its public contract in its `__init__.py`. Other packages MUST import only from the top-level package namespace, never from internal submodules.

**Example:** `from memory import MemoryService` ✓ vs `from memory.core_memory import CoreMemory` ✗

**Rationale:** Enforces Invariant 10 (Boundaries > Short-Term Velocity). Allows internal refactoring without breaking the dependency graph.

## Risks / Trade-offs

- **[Risk] Scope is large (9 capabilities)** → Mitigation: Each capability spec is independently implementable. The `tasks.md` will sequence work in chunks with clear entry/exit criteria per capability.
- **[Risk] LangGraph API evolves rapidly** → Mitigation: Pin a specific LangGraph version in `pyproject.toml` and isolate all LangGraph imports to `packages/orchestrator/`.
- **[Risk] Token budget math depends on model-specific tokenizers** → Mitigation: All tokenization is delegated to `packages/model_adapter/tokenizer.py`; the Context Assembler calls it as an injected dependency, making it swappable.
- **[Risk] pgvector embedding dimension changes break existing indices** → Mitigation: Store embedding model name alongside each vector row; include migration scripts in the `background-worker` spec.
- **[Risk] Memory promotion policies are policy-subjective** → Mitigation: Encode policies as explicit configurable parameters with default values; spec scenarios assert behavior at policy boundaries (e.g., "WHEN core memory exceeds N tokens THEN evict lowest-scored block").
