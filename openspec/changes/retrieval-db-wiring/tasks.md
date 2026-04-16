# Tasks: retrieval-db-wiring

## RetrievalService — async DB wiring

- [x] 1. Add `_archival_entry_to_corpus_dict(row) -> dict` module-level helper to
  `packages/retrieval/retrieval/service.py` — converts an `ArchivalEntry` ORM row
  to the `{id, content, source_type, embedding, ...metadata_}` dict format expected
  by `HybridSearcher`

- [x] 2. Add `session_factory: Optional[Any] = None` parameter to
  `RetrievalService.__init__`; store as `self._session_factory`

- [x] 3. Add `async_search(session_id, query, top_k, filters) -> list[DocumentChunk]`
  to `RetrievalService`:
  - Opens `async with self._session_factory() as db`
  - Calls `ArchivalRepository(db).search(session_id, embedding=None, top_k * 2)`
  - Converts rows via `_archival_entry_to_corpus_dict`
  - Runs existing `HybridSearcher` + `Reranker` over the loaded corpus
  - Returns `list[DocumentChunk]`
  - Falls back to `self.search(query, top_k, filters)` when `session_factory is None`

## Orchestrator node — async update

- [x] 4. Rewrite `packages/orchestrator/orchestrator/nodes/retrieve_context.py` as
  `async def retrieve_context(state: RuntimeState) -> RuntimeState`:
  - Reads `session_factory = getattr(state, "session_factory", None)`
  - Instantiates `RetrievalService(session_factory=session_factory)`
  - Calls `await svc.async_search(session_id, query, top_k=5)` when factory is set
  - Falls back to `svc.search(query, top_k=5)` when factory is None
  - Keeps the `if not state.retrieval_needed: return state` guard

- [x] 5. Update `packages/orchestrator/orchestrator/graph.py` `_run_sequential` to
  `await retrieve_context(state)` (the call is already conditional on
  `state.retrieval_needed`)

## Tests

- [x] 6. Add async tests to `packages/retrieval/tests/test_retrieval.py` covering:
  - `async_search` with `session_factory=None` returns `[]` (no corpus)
  - `async_search` with a mock `session_factory` + `AsyncMock` `ArchivalRepository`
    returns `DocumentChunk` list populated from the mocked rows

## Quality gate

- [x] 7. Run `bash .git/hooks/pre-push` — all checks must pass (ruff ✓ mypy ✓ all
  test suites ✓)
