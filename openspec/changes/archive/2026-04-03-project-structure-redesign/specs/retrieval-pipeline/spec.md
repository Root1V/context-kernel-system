## ADDED Requirements

### Requirement: Hybrid search combines BM25 and vector similarity
The retrieval service SHALL execute BM25 keyword search and vector cosine similarity search in parallel for every `search(query, top_k, filters)` call and return a merged, deduplicated result list.

#### Scenario: Hybrid search returns top_k results
- **WHEN** `retrieval_service.search(query="Python async patterns", top_k=10)` is called
- **THEN** the service returns up to 10 `DocumentChunk` objects ranked by the fusion score

#### Scenario: Results from both sources are deduplicated
- **WHEN** a chunk appears in both BM25 and vector results
- **THEN** it appears exactly once in the final result list with a merged score

### Requirement: Reranker applies cross-encoder scoring to top candidates
After initial retrieval, the service SHALL apply a cross-encoder reranker to the top-N candidates and re-order them by relevance before returning.

#### Scenario: Reranker improves ordering
- **WHEN** a query strongly matches a chunk semantically but the chunk ranked low in BM25
- **THEN** after reranking, the chunk's final rank MUST reflect cross-encoder score, not only BM25 rank

### Requirement: Metadata filters narrow the candidate set
The retrieval service SHALL accept a `filters: dict` parameter and apply pre-filtering to exclude document chunks not matching the filter criteria before vector search and BM25.

#### Scenario: Source type filter applied
- **WHEN** `search` is called with `filters={"source_type": "codebase"}`
- **THEN** only chunks with `source_type == "codebase"` are considered regardless of their relevance scores

### Requirement: Chunking produces fixed-overlap segments
The chunking module SHALL split raw documents into overlapping text windows of configurable `chunk_size` and `chunk_overlap` tokens.

#### Scenario: All content is covered with overlap
- **WHEN** a 1000-token document is chunked with `chunk_size=200` and `chunk_overlap=50`
- **THEN** all tokens appear in at least one chunk and adjacent chunks share 50 tokens at their boundary

### Requirement: Retrieval enters the system only through this package
No other package SHALL perform direct database queries for document chunks or call embedding APIs. All retrieval operations MUST go through `retrieval_service.search()`.

#### Scenario: Orchestrator retrieves via retrieval service
- **WHEN** the orchestrator DAG's `retrieve_context` node runs
- **THEN** it calls `retrieval_service.search()` and MUST NOT call any embedding model or DB query directly
