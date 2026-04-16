# Proposal: retrieval-db-wiring

## What

Wire `RetrievalService` to `ArchivalRepository` (pgvector) so the `retrieve_context`
orchestrator node returns real document chunks from the database instead of always
returning an empty list.

## Why

Currently `RetrievalService` is purely in-memory: it requires a corpus to be passed
at construction time via `load_corpus()`. The `retrieve_context` node instantiates it
with no corpus, so retrieval always silently falls back to `[]`. The pgvector database
(`archival_entries` table) is already running and has an `embedding` column with
`l2_distance` search via `ArchivalRepository.search()` — it just isn't connected to
`RetrievalService` at all.

## Goal

After this change:
1. `RetrievalService` accepts an optional `session_factory` parameter.
2. When `session_factory` is set, `search()` queries `ArchivalRepository` for
   vector-similar entries and loads them as corpus before running hybrid scoring.
3. The `retrieve_context` node passes `session_factory` from `RuntimeState` to
   `RetrievalService` when available.
4. `RetrievalService` exports `async_search()` — async variant used by the node.
5. All existing sync tests remain green (in-memory fallback unchanged).

## Affected packages

- `packages/retrieval/` — core change: `service.py`, `hybrid_search.py`
- `packages/orchestrator/orchestrator/nodes/retrieve_context.py` — passes factory
- `packages/retrieval/tests/` — new async tests

## Out of scope

- Embedding generation for user queries (query_embedding remains optional/None for now)
- Indexing new documents into archival_entries (that is the worker's job)
- Changes to `ArchivalRepository` (already has `search()` method)
