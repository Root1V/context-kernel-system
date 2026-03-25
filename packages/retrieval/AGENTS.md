# Modular Domain: Retrieval Package

This file establishes the strict subagent rules, invariants, and boundaries for the `packages/retrieval` module. Any subagent (e.g., `@backend-builder`, `@retrieval-architect`) operating within this directory MUST adhere to these local protocols.

## Domain Mission
The `retrieval` package is exclusively responsible for fetching, filtering, chunking, and post-processing "High-Signal Context" from raw unstructured data, embeddings, or external memory stores using Hybrid Search (Semantic + Lexical) methodologies.

## Strict Boundaries (Separation of Concerns)

### What this Module BUILDS:
- Vector/Embedding search adapters and semantic clients.
- Keyword (BM25) lexical index search logic.
- Context filtering and metadata mapping rules.
- Document Chunking strategies.
- Post-search Attention Reranking algorithms (e.g., MRR/Cosine Similarity enforcement).

### What this Module MUST NEVER BUILD:
- **No Context Assembly**: This module fetches data, but it `NEVER` decides how that data is structured into the final LLM prompt. That is the exclusive domain of `packages/context_assembler`.
- **No State Persistence**: This module queries data but `NEVER` saves explicit conversational state or manages core session lifecycles. That belongs to `packages/state` and `packages/memory`.
- **No Storage Migrations**: Do not build base persistence ORMs here. Delegate native database schemas to `packages/storage`.

## Architectural Invariants (Never Violate)
1. **DAG Pipeline Execution**: All retrieval requests returning context must follow a strict internal pipeline: `Filter -> Search -> Rerank`.
2. **Chunk Deduping**: Never return redundant or duplicate text chunks. They must be mathematically fused or deduped before exiting this module.
3. **Traceable Metadata Required**: Every piece of retrieved context returned from this module MUST include mandatory traceability metadata (e.g., `origin_id`, `timestamp`, `chunk_index`). "Naked" unreferenced strings are forbidden.
4. **Attention Cutoffs**: Raw retrieval lists must always pass through an attention threshold (e.g., similarity score > 0.8) before being served to the host caller.

## Testing Standards
- All chunking, aggregation, and reranking policies REQUIRE strict **Unit Tests** verifying logic limits.
- Any adapter calling a vector database or external semantic source REQUIRES **Mocked Fixtures**. No live DB calls in CI.
