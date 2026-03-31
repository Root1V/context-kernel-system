# Architecture: Storage Model

## Purpose
This document defines the **Persistence Architecture** of the *Context Kernel* system. It establishes the architectural model for what kinds of data the system stores, how they are logically separated by ownership, and which invariants govern data integrity.

It does **NOT** define exact SQL column names, final table schemas, ORM strategies, or migration scripts. Those belong to `packages/storage/`.

---

## Core Persistence Principles
These rules are non-negotiable across all storage implementations:

1. **PostgreSQL is the exclusive Source of Truth** (As per ADR-002).
2. **State must be explicit and queryable** — not inferred from raw chat histories.
3. **Memory layers must be stored in distinct, purpose-specific entities**.
4. **Context assemblies must be persisted** for every turn (full audit trail).
5. **Large binary artifacts** may live in Object Storage (S3/MinIO), but ALL metadata linkages must reside in PostgreSQL.
6. **Storage layers must not embed policy logic** — they persist; they do not decide.

---

## High-Level Storage Topology

```text
+-----------------------------------------------+
|             POSTGRESQL (Source of Truth)       |
|                                                |
|  [Runtime]       [Memory]       [Execution]   |
|  sessions        memory_blocks  messages       |
|  session_state   mem_versions   context_asm    |
|  task_state      recall_events  tool_calls     |
|  open_files      archival       model_calls    |
|                                                |
|  [Knowledge]     [Offline]      [Evaluation]  |
|  documents       sleep_jobs     eval_runs      |
|  doc_chunks      sleep_results  eval_results   |
+-----------------------------------------------+

+----------------------------+      +--------------------+
| OBJECT STORAGE (S3/MinIO)  |      | VECTOR LAYER       |
| Raw Files / Large Artifacts|      | pgvector (initial) |
+----------------------------+      | Qdrant (optional)  |
                                    +--------------------+
```

---

## Entity Groups

### Group 1: Runtime Entities (Explicit State)
Represent the live, turn-by-turn operational state of the system.

| Entity | Owner | Purpose |
|---|---|---|
| `sessions` | `packages/state` | Root container for a conversation thread. |
| `session_state` | `packages/state` | Transient mode, active profile, and session pointers. |
| `task_state` | `packages/state` | Current goal, subtasks, blockers, and progress markers. |
| `open_files_state` | `packages/state` | Open artifact handles and read-mode status. |

**Key Fields:**
- `sessions`: `id`, `created_at`, `updated_at`, `status`, `owner_id`, `config_ref`
- `session_state`: `session_id`, `current_mode`, `active_profile`, `summary_pointer`, `selected_tools`
- `task_state`: `session_id`, `active_goal`, `subtasks (jsonb)`, `blockers (jsonb)`, `progress_markers`
- `open_files_state`: `session_id`, `file_ids (jsonb)`, `focus_order`, `artifact_type`, `summary_pointer`

**Invariant**: `task_state` is NOT equivalent to chat history. It is an explicit JSON schema representing the agent's current goal; it must be independently readable without scanning raw messages.

---

### Group 2: Memory Entities (Layered Memory)
Represent the three-tier layered memory architecture.

| Entity | Owner | Purpose |
|---|---|---|
| `memory_blocks` | `packages/memory` | Active Core Memory blocks pinned on every turn. |
| `memory_block_versions` | `packages/memory` | Full audit trail of block mutations with `changed_by` and `reason`. |
| `recall_events` | `packages/memory` | Short-term structured interaction log, queryable but not always injected. |
| `archival_entries` | `packages/memory` | Long-term distilled facts, semantic notes, and stable summaries. |

**Key Fields:**
- `memory_blocks`: `id`, `session_id`, `label`, `value (text/jsonb)`, `size_limit`, `is_mutable`, `updated_at`
- `memory_block_versions`: `block_id`, `previous_value`, `new_value`, `reason`, `changed_by`, `timestamp`
- `recall_events`: `session_id`, `event_type`, `content`, `timestamp`, `metadata (jsonb)`
- `archival_entries`: `id`, `title`, `type`, `content`, `source_refs (jsonb)`, `tags (jsonb)`, `created_from`, `created_at`

**Invariant**: `memory_blocks` must enforce a bounded `size_limit` at write time. Unbounded growth violates the Token Economy Invariant (Invariant 4).

---

### Group 3: Execution Traceability Entities
Represent the per-turn execution footprint, enabling the system to answer "What happened in Turn X?".

| Entity | Owner | Purpose |
|---|---|---|
| `messages` | `packages/state` | Raw turn event log per role (`user`, `assistant`, `tool`). |
| `context_assemblies` | `packages/context_assembler` (via storage) | Exact structured snapshot of the final prompt payload sent to the LLM. |
| `tool_calls` | `packages/tool_runtime` (via storage) | Input, output, latency, and status per MCP tool invocation. |
| `model_calls` | `packages/model_adapter` (via storage) | Provider, model, token usage, latency, and stop code per LLM inference. |

**Key Fields:**
- `messages`: `id`, `session_id`, `role`, `content`, `timestamp`, `turn_id`
- `context_assemblies`: `id`, `session_id`, `turn_id`, `model_used`, `token_budget`, `included_sections (jsonb)`, `retrieved_refs (jsonb)`, `compacted_summary`, `serialized_payload`, `created_at`
- `tool_calls`: `id`, `turn_id`, `tool_name`, `input (jsonb)`, `output_summary`, `status`, `latency_ms`, `trace_metadata (jsonb)`
- `model_calls`: `id`, `turn_id`, `assembly_id`, `provider`, `model_name`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `stop_code`, `status`

**Invariant**: `context_assemblies` is the most critical audit entity. If the system cannot reconstruct "what the model saw", it has violated Invariant 13 (Traceability).

---

### Group 4: Knowledge Entities (RAG & Documents)
Represent the ingested external knowledge base and its vector retrieval layer.

| Entity | Owner | Purpose |
|---|---|---|
| `documents` | `packages/retrieval` | Metadata for all ingested files, URLs, or corpora. |
| `document_chunks` | `packages/retrieval` | Retrieval-unit granularity text blocks with embedding references. |

**Key Fields:**
- `documents`: `id`, `source_uri`, `title`, `type`, `owner_scope`, `ingest_status`, `ingest_metadata (jsonb)`, `created_at`
- `document_chunks`: `id`, `document_id`, `chunk_text`, `chunk_index`, `metadata (jsonb)`, `embedding vector`, `source_offsets`

**Invariant**: Full raw documents NEVER enter the Active Context. Only `document_chunks` are surfaced by the Retriever, always decorated with `origin_id` and `timestamp` for traceability.

---

### Group 5: Offline / Evaluation Entities
Represent the administrative and quality assurance processes running outside the synchronous Turn loop.

| Entity | Owner | Purpose |
|---|---|---|
| `sleep_jobs` | `apps/worker` | Scheduled compaction, merge, and knowledge promotion tasks. |
| `sleep_job_results` | `apps/worker` | Outcome diff and audit log of each offline job. |
| `eval_runs` | `packages/observability` | Test execution container with target scope and metrics. |
| `eval_results` | `packages/observability` | Structured metric outputs per evaluation run. |

**Key Fields:**
- `sleep_jobs`: `id`, `type`, `scope`, `input_refs (jsonb)`, `status`, `started_at`, `finished_at`, `result_pointer`
- `sleep_job_results`: `job_id`, `status`, `diff_summary (jsonb)`, `audit_trail (jsonb)`, `completed_at`
- `eval_runs`: `id`, `suite_name`, `target_scope`, `status`, `started_at`, `metrics (jsonb)`, `artifacts (jsonb)`
- `eval_results`: `run_id`, `metric_name`, `value`, `threshold`, `passed`, `recorded_at`

---

## Entity Relationship Map

```text
session
 ├── session_state          (1:1)
 ├── task_state             (1:1)
 ├── open_files_state       (1:1)
 ├── messages               (1:N)
 ├── memory_blocks          (1:N)
 │    └── memory_block_versions (1:N per mutation)
 ├── recall_events          (1:N)
 ├── context_assemblies     (1:N, one per turn)
 ├── tool_calls             (1:N, per turn)
 └── model_calls            (1:N, per turn)

documents
 └── document_chunks        (1:N)

sleep_jobs
 └── sleep_job_results      (1:1)
      └── (reads/writes) memory_blocks, archival_entries, recall_events
```

---

## Module → Storage Ownership Matrix

| Module | Writes to | Reads from |
|---|---|---|
| `packages/state` | `sessions`, `session_state`, `task_state`, `open_files_state`, `messages` | All runtime entities |
| `packages/memory` | `memory_blocks`, `memory_block_versions`, `recall_events`, `archival_entries` | All memory entities |
| `packages/retrieval` | `documents`, `document_chunks` | `archival_entries` |
| `packages/context_assembler` | *(no direct writes — pure consumer via storage boundary)* | All entity groups |
| `packages/model_adapter` | `model_calls` | `context_assemblies` |
| `packages/tool_runtime` | `tool_calls` | `session_state`, `task_state` |
| `apps/worker` | `sleep_jobs`, `sleep_job_results` | All memory and state entities |
| `packages/observability` | `eval_runs`, `eval_results` | All entity groups (read-only) |

**Invariant**: `packages/context_assembler` does NOT own any database writes. It is a pure read-aggregating consumer.

---

## Versioning Expectations
The system must support immutable versioning for at least:
- **`memory_block_versions`** — every mutation to Core Memory must be immutably logged with reason and author.
- **`context_assemblies`** — assembly format schema versions must be tracked if the payload structure evolves.
- **`archival_entries`** — if a stable summary is overwritten, the previous version must be retained in an append-only log.

---

## Traceability Queryability Gate (The Evaluator's Audit)

The storage model is considered **compliant** only if the system can natively answer these queries via direct DB access at any time:

| # | Question | Answered by |
|---|---|---|
| 1 | What exactly did the model see in turn `T`? | `context_assemblies.serialized_payload` |
| 2 | Which `memory_blocks` were pinned in turn `T`? | `context_assemblies.included_sections` |
| 3 | Which `document_chunks` were retrieved? | `context_assemblies.retrieved_refs` |
| 4 | Which MCP Tools were called and what did they return? | `tool_calls` |
| 5 | What changed in memory after turn `T`? | `memory_block_versions` |
| 6 | Which background job compacted or promoted this fact? | `sleep_job_results.audit_trail` |

> *If ANY of the above cannot be answered via a direct DB query, the storage schema is architecturally incomplete and must be revised before merging.*

---

## Initial Minimal Viable Table Checklist

The absolute baseline required before the system can run an end-to-end Turn:

- [ ] `sessions`
- [ ] `session_state`
- [ ] `task_state`
- [ ] `messages`
- [ ] `memory_blocks`
- [ ] `memory_block_versions`
- [ ] `recall_events`
- [ ] `archival_entries`
- [ ] `documents`
- [ ] `document_chunks`
- [ ] `context_assemblies`
- [ ] `tool_calls`
- [ ] `model_calls`
- [ ] `sleep_jobs`
- [ ] `eval_runs`

---

## Non-Goals
This document does **NOT** define:
- Exact DDL SQL schemas or final column names.
- ORM strategy (`SQLAlchemy` vs raw `asyncpg` — see ADR-002 Follow-up).
- Migration toolchain (`Alembic` configuration).
- Exact indexing, partitioning, or sharding policy.
- Final choice of Object Storage provider (S3 vs MinIO).

All of the above are governed by `packages/storage/` module boundaries and the repository's migration files.
