## ADDED Requirements

### Requirement: Storage and state smoke script
The system SHALL include `examples/01_storage_state_smoke.py`, a standalone Python script that (1) imports `init_db` and `Base` from `storage`, calls `init_db()`, and prints the list of mapped table names from `Base.metadata.tables`; (2) imports `StateService` from `state`, calls `.get_session_state("demo-session-001")`, and prints the result or empty dict. Both calls SHALL be wrapped in try/except; any failure prints `⚠️ fallback: <reason>` and exits 0.

#### Scenario: Script runs without error when DB is not configured
- **WHEN** `PYTHONPATH=packages python3 examples/01_storage_state_smoke.py` is executed with no database
- **THEN** the script exits 0 and prints either real data under `--- Storage Tables ---` and `--- Session State ---`, or a `⚠️ fallback` message for each section

#### Scenario: Script shows table names when DB is reachable
- **WHEN** the script runs and PostgreSQL is available
- **THEN** stdout under `--- Storage Tables ---` contains at least one table name

### Requirement: Memory and retrieval smoke script
The system SHALL include `examples/02_memory_retrieval_smoke.py`, a standalone Python script that (1) imports `MemoryService` from `memory`, calls `.snapshot("demo-session-001")`, and prints the snapshot fields; (2) imports `RetrievalService` from `retrieval`, calls `.search("context engineering memory system", top_k=3)`, and prints the number of chunks and each chunk's content. Both sections SHALL be wrapped in try/except with `⚠️ fallback` on error — exit 0 always.

#### Scenario: Script runs without DB
- **WHEN** `PYTHONPATH=packages python3 examples/02_memory_retrieval_smoke.py` is executed with no database
- **THEN** the script exits 0 and prints both `--- Memory Snapshot ---` and `--- Retrieved Chunks ---` sections (may contain fallback messages)

#### Scenario: Memory snapshot section shows expected keys
- **WHEN** MemoryService returns data
- **THEN** stdout under `--- Memory Snapshot ---` contains `core_memory`, `message_buffer`, or `recent_recall`

### Requirement: Context assembly and observability smoke script
The system SHALL include `examples/03_context_observability_smoke.py`, a standalone Python script that (1) imports `configure_logging` and `get_logger` from `observability`, calls `configure_logging()`, gets a logger, and logs one INFO message — printing confirmation that logging is configured; (2) imports `assemble` and `AssemblyInput` from `context_assembler`, builds a sample `AssemblyInput` with hardcoded core_memory blocks, message_buffer, and retrieved_chunks, calls `assemble()`, and prints `ctx.render()` under `--- Assembled Context ---`; (3) imports `trace_node` from `observability` and shows a sample span record around the assemble call.

#### Scenario: Script runs and produces assembled context
- **WHEN** `PYTHONPATH=packages python3 examples/03_context_observability_smoke.py` is executed
- **THEN** the script exits 0 and stdout contains `--- Observability ---`, `--- Assembled Context ---`, and at least one non-empty line of assembled text

#### Scenario: Observability section shows logging is configured
- **WHEN** the script runs
- **THEN** stdout under `--- Observability ---` confirms that configure_logging ran without error

### Requirement: Model adapter and tool runtime smoke script
The system SHALL include `examples/04_model_tool_runtime_smoke.py`, a standalone Python script that (1) imports `ToolRegistry` and `ToolRuntime` from `tool_runtime`, registers a no-op echo tool, calls `runtime.execute_tool("echo", {"message": "hello"})`, and prints the `ToolResult`; (2) imports `complete` from `model_adapter`, calls it with a test message and `model_id="gpt-4o"` — on `UnsupportedModelError` or any exception prints `⚠️ No LLM configured: set OPENAI_API_KEY or ANTHROPIC_API_KEY` and skips that section (exit 0); on success prints `content` and `usage`.

#### Scenario: Tool runtime section always runs
- **WHEN** `PYTHONPATH=packages python3 examples/04_model_tool_runtime_smoke.py` is executed without an LLM key
- **THEN** stdout contains `--- Tool Runtime ---` with the echo tool result, and `--- Model Adapter ---` with the no-LLM warning

#### Scenario: Model adapter section runs when LLM key is set
- **WHEN** `OPENAI_API_KEY` is configured and the script runs
- **THEN** stdout under `--- Model Adapter ---` contains `content:` and the response text

### Requirement: Orchestrator direct script
The system SHALL include `examples/05_orchestrator_direct.py`, a standalone Python script that imports `orchestrate` and `TurnRequest` from `orchestrator`, constructs a `TurnRequest` with `session_id="demo-session-001"`, `user_message="Explain how context assembly works in this system"`, `model_id="gpt-4o"`, `retrieval_needed=True`, calls `orchestrate(req)`, and prints all 6 TurnResponse fields under labeled sections. This script exercises all 9 packages in a single call.

#### Scenario: Script runs end-to-end through all packages
- **WHEN** `PYTHONPATH=packages python3 examples/05_orchestrator_direct.py` is executed
- **THEN** the script exits 0 and prints all 6 TurnResponse fields: `session_id`, `turn_id`, `assistant_message`, `status`, `tool_calls_made`, `state_persisted`

#### Scenario: Script shows fallback status when no external services available
- **WHEN** neither DB nor LLM are configured
- **THEN** the TurnResponse printed has `status` of `"ok"` or `"error"` and `state_persisted: False`, not an unhandled exception

### Requirement: API and worker e2e script
The system SHALL include `examples/06_api_worker_e2e.py`, a standalone Python script with two independent sections: (1) API section — uses `urllib.request` (stdlib only) to POST `{"session_id":"demo-session-001","message":"What is the status of our project?","model_id":"gpt-4o"}` to `http://localhost:8000/chat` and prints the full JSON response; on `URLError` / `ConnectionRefusedError` prints `⚠️ API not running. Start with: cd apps/api && PYTHONPATH=../../packages uvicorn app.main:app --reload` and continues; (2) worker section — imports `enqueue_job`, `Job`, `JobType` from `apps/worker`, creates a `Job(job_type=JobType.compaction, session_id="demo-session-001", payload={"messages":["msg 1","msg 2"]})`, calls `enqueue_job(job)`, then imports and calls `handle_compaction(job)` directly, and prints the resulting Job status.

#### Scenario: Worker section runs independently of API
- **WHEN** `PYTHONPATH=packages:apps/worker python3 examples/06_api_worker_e2e.py` is executed with no API server
- **THEN** the script exits 0, prints the API not-running warning under `--- API E2E ---`, and still executes and prints the worker compaction result under `--- Worker Job ---`

#### Scenario: API section returns ChatResponse when server is running
- **WHEN** the API server is active and the script runs
- **THEN** stdout under `--- API E2E ---` contains the JSON response with `session_id`, `assistant_message`, and `status`
