# ADR-002: PostgreSQL as Primary State Store, pgvector as Initial Vector Layer

- **Status**: Accepted
- **Date**: 2026-03-24
- **Impacts**: Storage Models, Layered Memory Pipelines, Retrieval Engines, Background Workers

## 1. Context

The *Context Kernel* system requires a robust persistence layer capable of tracking:
- Ephemeral and long-term multi-turn conversational sessions.
- Explicit Task State constraints and DAG workflows.
- Segmented Memory Blocks (Core, Recall, Archival).
- Traceable Retrieval Results with rich metadata.
- Context Assemblies and raw document ingestion mapping.
- Semantic Vector Embeddings for Hybrid Search.

We require a primary database that acts as an absolute "Source of Truth", supports the "Explicit State" invariant natively, minimizes infrastructural complexity during the initial build out, and natively enables hybrid capabilities (relational + semantic search).

## 2. Decision

We formally adopt:
- **PostgreSQL** as the singular, primary relational database for all Application State and Explicit Memory tracking.
- **pgvector** as the native operational layer inside PostgreSQL for Initial Vector Search and Embeddings.

## 3. Rationale (Why)

### PostgreSQL (The Source of Truth)
PostgreSQL inherently satisfies the *Context Kernel* invariants because:
- **Explicit State Support**: The `jsonb` column type acts as the perfect transport mechanism for unstructured explicit context payloads. The `@sleep-time-worker` and `@memory-architect` can read and mutate serialized `Pydantic` states seamlessly without strict schema migrations.
- **ACID Stability**: Guaranteed consistency when updating critical Agent bounds and session context graphs.
- **Simplicity**: Consolidates the operational stack, avoiding the "distributed system" problem across multiple disparate engines early in the lifecycle.

### pgvector (The Semantic Layer)
`pgvector` is chosen over an immediate standalone vector store because:
- **Traceability Metadata Constraint**: Our `retrieval` subagent rules demand strict traceability (e.g., `origin_id`, `timestamp`) for all facts. `pgvector` allows embeddings to reside on the exact same row as their origin text, eliminating sync issues and enabling flawless metadata + vector proximity lookups.
- **Lexical/Semantic Hybridization**: Enables exact SQL filtering (keyword search capabilities) combined with cosine distance evaluations in the exact same query, satisfying the Hybrid Search invariant.

## 4. Consequences

### Positive
- **Single Source of Truth**: Eliminates external sync pipelines for memory blocks and context storage during the critical R&D phases.
- **Operational Speed**: Dramatically lowers cognitive load for the `@backend-builder` managing CI/CD setups and local developer environments.
- **Unified Transactions**: When a session closes, the context summaries and embeddings are written or rolled back synchronously.

### Negative / Risks
- **Vector Scale Limitations**: `pgvector` is not historically optimized for billions of dense embeddings compared to highly specialized engines.
- **Resource Contention**: Mixing high-frequency transactional data (`State`) with heavy analytical reads (`Semantic Reranking`) can stress PostgreSQL compute metrics under heavy load.
- **Index Latencies**: Vector indexing operations inside Postgres can lock or strain standard processes if not tuned.

## 5. Alternatives Considered

- **PostgreSQL + Qdrant (Day 1)**: Superior specialized retrieval performance. **Cons:** Introduces extreme operational friction, requires complex synchronization polling, and injects unnecessary failure points before the core orchestration DAG is mathematically proven.
- **Polyglot Persistence (SQL + Vector DB + Graph DB)**: Theoretical perfect architecture. **Cons:** Severe over-engineering for an early cognitive system.
- **No Vector Search (BM25 Only)**: Heavily simplifies DB configuration. **Cons:** Paralyzes the AI system's ability to execute fuzzy semantic matches against Archival memory out-of-the-box, breaking the Layered Memory design completely.

## 6. Migration Path & Boundaries
This ADR mandates that PostgreSQL is the *Source of Truth*, and pgvector is the *Initial Solution*. 
- If Retrieval demands exceed pgvector limits:
  1. PostgreSQL **retains** the Source of Truth, keeping original texts and core metadata.
  2. Embeddings are exported and migrated to an external Vector DB (e.g., Qdrant, Pinecone).
  3. The `packages/retrieval` module's Adapter pattern is updated without affecting downstream nodes.

## 7. Follow-up Actions
- Design the baseline ERD schema for Core, Recall, and Archival memory tables.
- Establish the `packages/storage` repository boundaries (Abstract Base Classes) to decouple raw SQL from the internal domain logic.
- Standardize the Database Interface driver (e.g., `asyncpg` / `SQLAlchemy`) and migration toolchain (e.g., `Alembic`).
