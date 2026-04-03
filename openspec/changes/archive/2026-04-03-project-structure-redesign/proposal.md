## Why

The Context Kernel codebase has all the right packages scaffolded, but none of the modules have spec-level contracts defining their behavior — no interface agreements between packages, no capability specs that can drive test-first development, and no verifiable boundaries enforcing the architectural invariants documented in the system vision. Without these contracts, parallel development by multiple agents will produce incompatible implementations and drift from the original cognitive topology design.

## What Changes

- Introduce `openspec/specs/` capability specs for every core module, each defining its I/O contracts, invariants, and acceptance criteria.
- Establish explicit Pydantic schemas at every module boundary (inputs and outputs of each package's public API).
- Implement the full **Turn-Time DAG** in `packages/orchestrator/` as a wired LangGraph graph connecting all packages.
- Implement the **Between-Turn Worker** in `apps/worker/` for async memory compaction and archival promotion.
- Wire `packages/context_assembler/` as the exclusive composer for Active Context, receiving structured inputs from all other packages.
- Implement `packages/memory/` with the four-layer architecture (message buffer, core memory, recall memory, archival memory) backed by the storage layer.
- Implement `packages/retrieval/` with hybrid search (BM25 + vector) and a reranker.
- Implement `packages/tool_runtime/` with MCP Gateway isolation and tool-safety policies.
- Implement `packages/model_adapter/` as the exclusive LLM provider gateway.
- **BREAKING**: Define and enforce strict module boundary rules — no package may import from another except through its declared public interface.

## Capabilities

### New Capabilities

- `context-assembly`: Assembles the Active Context payload per turn from structured inputs. Manages token budget, section ordering, and pinning policies. Owner: `packages/context_assembler`.
- `layered-memory`: Four-layer memory model (message buffer, core memory, recall memory, archival memory) with explicit promotion/eviction policies. Owner: `packages/memory`.
- `orchestrator-dag`: LangGraph-based Turn-Time DAG wiring all packages into the full request-to-response pipeline. Owner: `packages/orchestrator`.
- `state-management`: Explicit schema-backed session state, task state, and open-files state with persistence. Owner: `packages/state`.
- `retrieval-pipeline`: Hybrid BM25 + vector search with reranking and metadata filtering for external context retrieval. Owner: `packages/retrieval`.
- `tool-runtime-mcp`: MCP gateway that proxies all external tool calls through safety validation and schema enforcement. Owner: `packages/tool_runtime`.
- `model-adapter`: Provider-agnostic LLM gateway abstracting OpenAI and Anthropic with token counting and limit enforcement. Owner: `packages/model_adapter`.
- `api-layer`: FastAPI routes for chat, sessions, and health — validates auth/payloads and triggers the orchestrator. Owner: `apps/api`.
- `background-worker`: Async worker executing memory compaction, summarization, and archival promotion jobs between turns. Owner: `apps/worker`.

### Modified Capabilities

_None — all capabilities are being established for the first time._

## Impact

- **All packages**: Every package in `packages/` transitions from placeholder stubs to spec-backed implementations.
- **apps/api**: Routes must conform to the `api-layer` spec; context-assembly logic is strictly forbidden here.
- **apps/worker**: Job definitions must conform to the `background-worker` spec.
- **Database**: Storage layer (`packages/storage/`) must support all memory layer persistence needs (core memory blocks, archival embeddings, recall logs, session state).
- **Dependencies**: LangGraph, pgvector, and an MCP-compatible tool server must be confirmed as active dependencies.
- **Testing**: Each capability spec directly generates the acceptance criteria for unit and integration tests.
