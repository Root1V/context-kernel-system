## 1. Storage + State Smoke Script

- [x] 1.1 Create `examples/01_storage_state_smoke.py` — first line: `# Run: uv run python3 examples/01_storage_state_smoke.py`
- [x] 1.2 Import `init_db`, `Base` from `storage`; call `init_db()`; print table names from `Base.metadata.tables` under `--- Storage Tables ---`; wrap in try/except with `⚠️ fallback: <reason>`
- [x] 1.3 Import `StateService` from `state`; call `.get_session_state("demo-session-001")`; print result under `--- Session State ---`; wrap in try/except with `⚠️ fallback: <reason>`

## 2. Memory + Retrieval Smoke Script

- [x] 2.1 Create `examples/02_memory_retrieval_smoke.py` — first line: `# Run: uv run python3 examples/02_memory_retrieval_smoke.py`
- [x] 2.2 Import `MemoryService` from `memory`; call `.snapshot("demo-session-001")`; print snapshot keys and values under `--- Memory Snapshot ---`; wrap in try/except with `⚠️ fallback: <reason>`
- [x] 2.3 Import `RetrievalService` from `retrieval`; call `.search("context engineering memory system", top_k=3)`; print chunk count and each `chunk.content` under `--- Retrieved Chunks ---`; wrap in try/except

## 3. Context Assembly + Observability Smoke Script

- [x] 3.1 Create `examples/03_context_observability_smoke.py` — first line: `# Run: uv run python3 examples/03_context_observability_smoke.py`
- [x] 3.2 Import `configure_logging`, `get_logger` from `observability`; call `configure_logging()`; log one INFO message; print `✓ Logging configured` under `--- Observability ---`
- [x] 3.3 Import `trace_node` from `observability`; wrap the assemble call in a `trace_node("assemble_context", "demo-session-001")` context manager; print the span record under `--- Trace Span ---`
- [x] 3.4 Import `assemble`, `AssemblyInput` from `context_assembler`; build `AssemblyInput` with hardcoded `core_memory_blocks=["User prefers concise answers"]`, `message_buffer=["user: How does memory work?", "assistant: Memory has three layers."]`, `retrieved_chunks=["Recall memory stores recent facts."]`, `model_id="gpt-4o"`; call `assemble(inp)`; print `ctx.render()` under `--- Assembled Context ---`

## 4. Model Adapter + Tool Runtime Smoke Script

- [x] 4.1 Create `examples/04_model_tool_runtime_smoke.py` — first line: `# Run: uv run python3 examples/04_model_tool_runtime_smoke.py`
- [x] 4.2 Import `ToolRegistry`, `ToolRuntime` from `tool_runtime`; create a `ToolRegistry`; register a minimal echo tool (name: `"echo"`, handler returns the `message` arg as output); instantiate `ToolRuntime(registry=registry)`; call `runtime.execute_tool("echo", {"message": "hello from tool_runtime"})`; print `ToolResult` fields under `--- Tool Runtime ---`
- [x] 4.3 Import `complete` from `model_adapter`; call `complete(messages=[{"role":"user","content":"What is context assembly in 1 sentence?"}], model_id="gpt-4o")`; on `UnsupportedModelError` or any `Exception` print `⚠️ No LLM configured: set OPENAI_API_KEY or ANTHROPIC_API_KEY` and skip; on success print `content` and `usage` under `--- Model Adapter ---`

## 5. Orchestrator Direct Script

- [x] 5.1 Create `examples/05_orchestrator_direct.py` — first line: `# Run: uv run python3 examples/05_orchestrator_direct.py`
- [x] 5.2 Import `orchestrate`, `TurnRequest` from `orchestrator`; build `TurnRequest(session_id="demo-session-001", user_message="Explain how context assembly works in this system", model_id="gpt-4o", max_tool_iterations=3, retrieval_needed=True)`
- [x] 5.3 Call `orchestrate(req)`; print all 6 TurnResponse fields under labeled sections: `--- Turn Request ---`, `--- Turn Response ---`; wrap in try/except — print error clearly but exit 0
- [x] 5.4 Add a comment block above the call explaining which packages each orchestrator node exercises (load_state→state, hydrate_memory→memory, retrieve_context→retrieval, assemble_context→context_assembler, infer→model_adapter, tool_loop→tool_runtime, persist_state→state)

## 6. API + Worker E2E Script

- [x] 6.1 Create `examples/06_api_worker_e2e.py` — first line: `# Run: PYTHONPATH=packages:apps/worker python3 examples/06_api_worker_e2e.py`
- [x] 6.2 API section: use only `urllib.request` + `json` (stdlib); POST `{"session_id":"demo-session-001","message":"What is the status of our project?","model_id":"gpt-4o"}` to `http://localhost:8000/chat`; print full JSON response under `--- API E2E ---`; on `URLError` print `⚠️ API not running. Start with: cd apps/api && PYTHONPATH=../../packages uvicorn app.main:app --reload` and continue (do not exit)
- [x] 6.3 Worker section: import `Job`, `JobType`, `enqueue_job` from `worker.main` (via `apps/worker`); import `handle_compaction` from `worker.jobs.compaction`; create `Job(job_type=JobType.compaction, session_id="demo-session-001", payload={"messages":["Turn 1: user asked about memory","Turn 2: assistant explained layers"]})`; call `enqueue_job(job)` then `result = handle_compaction(job)`; print `result.status`, `result.error`, `result.completed_at` under `--- Worker Job ---`; wrap in try/except with `⚠️ fallback: <reason>`
