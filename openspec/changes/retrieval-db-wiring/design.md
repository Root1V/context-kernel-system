# Design: retrieval-db-wiring

## Architecture

```
retrieve_context node
  │  passes session_factory (from RuntimeState or None)
  ▼
RetrievalService(session_factory=factory)
  │
  ├─ session_factory is None  →  in-memory corpus (current behaviour, unchanged)
  │
  └─ session_factory set      →  async_search(session_id, query, top_k)
       │
       └─ async with session_factory() as db:
            ArchivalRepository(db).search(session_id, embedding=None, top_k)
            → list[ArchivalEntry ORM rows]
            → convert to corpus dicts
            → run existing HybridSearcher + Reranker
            → return list[DocumentChunk]
```

## Key design decisions

### 1. `session_factory` dependency injection (same pattern as memory package)
`RetrievalService.__init__` gains `session_factory: Optional[Any] = None`.
- `None` → all existing sync behaviour unchanged, zero regression risk.
- Set → async path activated.

### 2. `async_search()` — new async method
```python
async def async_search(
    self,
    session_id: str,
    query: str,
    top_k: int = 10,
    filters: dict | None = None,
) -> list[DocumentChunk]:
```
- Opens a DB session via `async with self._session_factory() as db`.
- Calls `ArchivalRepository(db).search(session_id, embedding=None, top_k * 2)`.
- Converts ORM `ArchivalEntry` rows to corpus dicts: `{id, content, source_type, embedding}`.
- Runs `HybridSearcher` + `Reranker` over the loaded corpus.
- Returns `list[DocumentChunk]`.

### 3. ORM → corpus dict converter (module-level helper)
```python
def _archival_entry_to_corpus_dict(row) -> dict:
    return {
        "id": str(row.id),
        "content": row.content,
        "source_type": row.metadata_.get("source_type", "archival"),
        "embedding": list(row.embedding) if row.embedding is not None else [],
        **row.metadata_,
    }
```

### 4. `retrieve_context` node update
```python
async def retrieve_context(state: RuntimeState) -> RuntimeState:
    factory = getattr(state, "session_factory", None)
    svc = RetrievalService(session_factory=factory)
    if factory:
        chunks = await svc.async_search(state.turn_request.session_id, query, top_k=5)
    else:
        chunks = svc.search(query, top_k=5)   # in-memory fallback
    state.retrieved_chunks = [c.content for c in chunks]
```
The node becomes `async def` (matching the pattern set by `hydrate_memory`).

### 5. `_run_sequential` in `graph.py`
`retrieve_context` is already called conditionally; update the call site:
```python
state = await retrieve_context(state)
```

## Files changed

| File | Change |
|---|---|
| `packages/retrieval/retrieval/service.py` | Add `session_factory` param, `_archival_entry_to_corpus_dict`, `async_search` |
| `packages/orchestrator/orchestrator/nodes/retrieve_context.py` | `async def`, uses `async_search` when factory set |
| `packages/orchestrator/orchestrator/graph.py` | `await retrieve_context(state)` |
| `packages/retrieval/tests/test_retrieval.py` | New async tests with `AsyncMock` repo |

## No schema migrations needed
`ArchivalRepository.search()` already exists and queries the `archival_entries`
table. No new ORM models or columns required.
