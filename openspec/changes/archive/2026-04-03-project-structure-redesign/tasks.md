## 1. Foundation — Model Adapter

- [x] 1.1 Define `ModelResponse`, `UnsupportedModelError`, and `RateLimitError` Pydantic models in `packages/model_adapter/base.py`
- [x] 1.2 Implement `openai_adapter.py`: `complete()`, `count_tokens()`, `get_context_limit()` using OpenAI SDK
- [x] 1.3 Implement `anthropic_adapter.py`: `complete()`, `count_tokens()`, `get_context_limit()` using Anthropic SDK, normalized to `ModelResponse`
- [x] 1.4 Implement `tokenizer.py` with `count_tokens(text, model_id)` and `get_context_limit(model_id)` as the single public token utility
- [x] 1.5 Expose unified `complete()`, `count_tokens()`, `get_context_limit()` from `packages/model_adapter/__init__.py`
- [x] 1.6 Write unit tests for all model adapter scenarios in spec (happy paths, `UnsupportedModelError`, `RateLimitError`)

## 2. Foundation — State Management

- [x] 2.1 Define `SessionState`, `SessionStatePatch`, `TaskState`, `OpenFilesState` Pydantic models in `packages/state/session_state.py`, `task_state.py`, `open_files_state.py`
- [x] 2.2 Implement `StateService.get_session_state()` and `update_session_state()` with DB persistence via `packages/storage/`
- [x] 2.3 Implement `StateService.get_task_state()` and `update_task_state()` with `StateTransitionError` for invalid transitions
- [x] 2.4 Implement `StateService.add_open_file()` and `get_open_files()` per session
- [x] 2.5 Expose `StateService` from `packages/state/__init__.py`
- [x] 2.6 Write unit tests for all state management scenarios in spec (CRUD, transition validation, partial updates)

## 3. Foundation — Storage Layer

- [x] 3.1 Define DB schemas (SQLAlchemy models or raw SQL migrations) for: `sessions`, `session_state`, `task_state`, `core_memory_blocks`, `recall_entries`, `archival_entries`, `jobs`
- [x] 3.2 Implement `packages/storage/db.py` with async connection pool and session factory
- [x] 3.3 Implement repository classes for each entity in `packages/storage/repositories/`
- [x] 3.4 Confirm pgvector extension is enabled; create `archival_entries.embedding` column with correct dimension

## 4. Layered Memory

- [x] 4.1 Define `CoreMemoryBlock`, `RecallEntry`, `ArchivalEntry`, `MemorySnapshot` Pydantic models in `packages/memory/models.py`
- [x] 4.2 Implement `CoreMemoryService`: `get_core_memory()`, `add_core_memory_block()` with token-budget eviction policy
- [x] 4.3 Implement `MessageBufferService`: bounded buffer with overflow compaction event emission
- [x] 4.4 Implement `RecallMemoryService`: `get_recall_entries()` with recency window filtering
- [x] 4.5 Implement `ArchivalMemoryService`: `add_archival_entry()` with embedding generation and `search_archival()` via pgvector
- [x] 4.6 Expose unified `MemoryService` facade from `packages/memory/__init__.py`
- [x] 4.7 Write unit tests for all layered-memory spec scenarios (budget eviction, buffer overflow, search ranking, recall expiry)

## 5. Retrieval Pipeline

- [x] 5.1 Implement `chunking.py`: fixed-overlap token-window chunker with configurable `chunk_size` and `chunk_overlap`
- [x] 5.2 Implement BM25 indexing and search in `packages/retrieval/hybrid_search.py`
- [x] 5.3 Implement vector similarity search branch in `hybrid_search.py` using pgvector
- [x] 5.4 Implement score fusion and deduplication for hybrid results
- [x] 5.5 Implement `rerank.py`: cross-encoder reranker applied to top-N candidates
- [x] 5.6 Implement `filters.py`: metadata pre-filtering before BM25/vector search
- [x] 5.7 Expose `RetrievalService.search()` from `packages/retrieval/__init__.py`
- [x] 5.8 Write unit tests for retrieval-pipeline spec scenarios (hybrid merge, deduplication, filter application, reranker ordering)

## 6. Tool Runtime & MCP Gateway

- [x] 6.1 Implement `registry.py`: `load_tools(mcp_server_url)` and `get_tool_schema(tool_name)` with startup population
- [x] 6.2 Implement `safety.py`: JSON schema argument validation against registered tool schemas
- [x] 6.3 Implement `mcp_gateway.py`: `execute_tool(tool_name, arguments)` with safety validation, output size truncation, and `ToolResult` return
- [x] 6.4 Define `ToolResult`, `ToolNotFoundError`, `ToolArgumentValidationError` Pydantic models
- [x] 6.5 Expose `ToolRuntime.execute_tool()` from `packages/tool_runtime/__init__.py`
- [x] 6.6 Write unit tests for tool-runtime-mcp spec scenarios (valid call, unregistered tool, invalid args, size truncation)

## 7. Context Assembler

- [x] 7.1 Define `ActiveContext`, `AssemblyInput`, and section priority enum in `packages/context_assembler/assembler.py`
- [x] 7.2 Implement `TokenBudget` calculator using `model_adapter.count_tokens()` and `get_context_limit()`
- [x] 7.3 Implement canonical section ordering and pinning logic in `assembler.py`
- [x] 7.4 Implement truncation policy: drop/truncate non-pinned sections in reverse priority order until budget is met
- [x] 7.5 Implement section builders in `packages/context_assembler/sections/` (system instructions, tool schemas, memory, state summary, message buffer, retrieved chunks, open files)
- [x] 7.6 Expose `ContextAssembler.assemble()` from `packages/context_assembler/__init__.py`
- [x] 7.7 Write unit tests for context-assembly spec scenarios (budget fit, truncation, pinned survival, determinism)

## 8. Orchestrator DAG

- [x] 8.1 Define `TurnRequest`, `TurnResponse`, `RuntimeState` Pydantic models in `packages/orchestrator/`
- [x] 8.2 Implement `receive_request` node: normalize input to `TurnRequest`
- [x] 8.3 Implement `load_state` node: fetch `RuntimeState` from `StateService`
- [x] 8.4 Implement `hydrate_memory` node: produce `MemorySnapshot` from `MemoryService`
- [x] 8.5 Implement `retrieve_context` node with conditional skip based on `RuntimeState.retrieval_needed`
- [x] 8.6 Implement `assemble_context` node: call `ContextAssembler.assemble()` with all gathered inputs
- [x] 8.7 Implement `infer` node: call `model_adapter.complete()` with assembled context
- [x] 8.8 Implement `tool_loop` node: conditional loop — execute tools via `ToolRuntime`, append results, re-infer until no tool calls or `max_tool_iterations`
- [x] 8.9 Implement `persist_state` node: write `RuntimeState` checkpoint and dispatch compaction jobs
- [x] 8.10 Wire all nodes into a LangGraph `StateGraph` in `packages/orchestrator/graph.py`
- [x] 8.11 Write integration tests for orchestrator-dag spec scenarios (happy path, tool loop, max iterations, retrieval skip, checkpoint resume)

## 9. API Layer

- [x] 9.1 Define `ChatRequest`, `ChatResponse`, `SessionCreateRequest`, `SessionResponse` Pydantic schemas in `apps/api/app/schemas/`
- [x] 9.2 Implement `POST /chat` route: validate payload, call `orchestrate()`, return `ChatResponse`
- [x] 9.3 Implement `POST /sessions` route: create session via `StateService`, return `SessionResponse`
- [x] 9.4 Implement `GET /sessions/{session_id}` route: fetch session or return 404
- [x] 9.5 Implement `GET /health` route: check DB and MCP gateway connectivity, return status object
- [x] 9.6 Confirm no context-assembly, memory, or retrieval logic exists in any route file (enforce via linter rule or test)
- [x] 9.7 Write integration tests for api-layer spec scenarios (valid chat, 422 validation, session lifecycle, health)

## 10. Background Worker

- [x] 10.1 Define `Job` Pydantic model with `status` enum and `completed_at` field in `apps/worker/`
- [x] 10.2 Implement job poller in `apps/worker/worker/main.py`: claim pending jobs, dispatch to handler, mark complete/failed
- [x] 10.3 Implement `compaction.py` job handler: load compaction template from `prompts/summaries/compaction_template.md`, summarize buffer via `model_adapter`, write `RecallEntry` via `MemoryService`
- [x] 10.4 Implement archival promotion job handler: scan expired recall entries, generate embeddings, insert `ArchivalEntry`, delete recall entry (idempotent)
- [x] 10.5 Write unit tests for background-worker spec scenarios (compaction output, archival promotion, idempotency, job persistence/retry)

## 11. Observability & Cross-Cutting

- [x] 11.1 Instrument each DAG node with structured trace spans in `packages/observability/tracing.py`
- [x] 11.2 Add structured logging to all package public entry points
- [x] 11.3 Confirm `packages/*/` only import from sibling packages' top-level `__init__.py` (boundary enforcement check)
- [x] 11.4 Update `pyproject.toml` with all confirmed dependencies (LangGraph, pgvector, openai, anthropic, fastapi, rank-bm25, etc.)
- [x] 11.5 Write a smoke-test that exercises the full end-to-end turn path (API → orchestrator → all packages → response)
