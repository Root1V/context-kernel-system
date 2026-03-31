# Architecture: Context Map

## Purpose
This document defines the **Conceptual Context Map** of the *Context Kernel* system. It is the definitive answer to:

> **"What types of context exist, where do they live, and how do they flow into the model?"**

Every subagent (`@planner`, `@context-architect`, `@backend-builder`) must consult this document before designing data flows or prompt payload decisions.

---

## The Core Observation

The LLM does NOT see "everything the system knows."
It sees ONLY the **Active Context** — a deterministically assembled, bounded payload constructed specifically for the current turn.

This creates the fundamental engineering challenge: how to bridge the gap between **Total System Knowledge** and **Optimal Minimal Context**.

```text
[ TOTAL SYSTEM KNOWLEDGE ]
  Explicit State, Layered Memory, RAG Documents, Tools, History
                     │
                     │  select / compress / retrieve / pin
                     ▼
          [ CONTEXT ASSEMBLER ]
          (The Only Authorized Composer)
                     │
                     ▼
          [ ACTIVE CONTEXT PAYLOAD ]
          (What the model strictly sees)
                     │
                     ▼
          [ MODEL INFERENCE ]
          (Stateless local reasoning)
```

---

## The 4-Layer Knowledge Architecture

### Layer 1: Model (The Reasoner)
The inference engine. Stateless between calls — it only has access to what is injected in the current active context.

| Property | Value |
|---|---|
| **Scope** | Single inference call |
| **Owner** | `packages/model_adapter` |
| **Memory** | None — fully stateless |
| **Input** | Active Context only |

**What the model explicitly CANNOT access:**
- The full database.
- All memory blocks in the system.
- The uncompressed raw chat history.
- All tools, unless their schema is explicitly included in the Active Context.

---

### Layer 2: Active Context (The Working Memory)
The final assembled payload for a single turn. Constructed exclusively by `packages/context_assembler`.

| Property | Value |
|---|---|
| **Scope** | Single turn, ephemeral |
| **Owner** | `packages/context_assembler` |
| **Max Size** | Governed by model token budget |
| **Rebuilt** | Fresh every turn |

**Canonical Composition (ordered by priority):**
1. System Instructions & Behavioral Invariants
2. MCP Tool Schemas (available tools for this turn)
3. Pinned Core Memory Blocks
4. Session State & Task State summary
5. Recent Message Buffer
6. Retrieved External Context (`document_chunks`, `archival_entries`)
7. Open Files / Active Artifact Summaries

**Invariant**: Active Context is ALWAYS smaller than Total System Knowledge. This is not a limitation — it is the design.

---

### Layer 3: Core Memory (The Persistent Signal)
High-signal, durable information that is either always pinned in the Active Context or trivially injectable.

| Property | Value |
|---|---|
| **Scope** | Cross-session persistent |
| **Owner** | `packages/memory` |
| **Storage** | `memory_blocks` table |
| **Size Constraint** | Strictly bounded by `size_limit` per block |

**Examples of valid Core Memory content:**
- User identity profile and stated preferences.
- Durable behavioral constraints for the session.
- Current task high-level goal and status.
- Stable system persona configuration.

**Design Rule**: Core Memory MUST remain small and highly curated. It is not a catch-all. Promotion into Core Memory requires explicit policy justification.

---

### Layer 4: External Memory (The Retrievable Void)
All information outside the Active Context that *can* be brought in on demand via retrieval.

| Property | Value |
|---|---|
| **Scope** | Cross-session, potentially infinite |
| **Owner** | `packages/memory` + `packages/retrieval` |
| **Storage** | `recall_events`, `archival_entries`, `document_chunks` |

**Sub-tiers:**

| Sub-tier | Contents | How it enters Active Context |
|---|---|---|
| **Recall Memory** | Past turn events, tool outputs, conversation history | Semantic or recency-based lookup |
| **Archival Memory** | Stable summaries, architecture decisions, curated notes | Vector similarity search |
| **Document Index** | Ingested external corpora | Hybrid BM25 + Vector search |

**Design Rule**: External Memory exists to scale total knowledge infinitely. It never enters Active Context automatically — it MUST be explicitly requested by the Retrieval Plan.

---

## Supporting Context Sources
Beyond the 4 layers, these transient data objects complement Assembly:

| Source | Owner | Contents |
|---|---|---|
| **Session State** | `packages/state` | Current mode, active profile, pointers |
| **Task State** | `packages/state` | Active goal, subtasks, blockers, progress |
| **Open Files / Artifacts** | `packages/state` | Read handles for active working files |
| **Tool Metadata** | `packages/tool_runtime` | Available MCP tool schemas and constraints |

---

## The Context Boundary (The Core Engineering Problem)

```text
┌─────────────────────────────────────────────┐
│           TOTAL SYSTEM KNOWLEDGE            │
│  core memory  │  external memory            │
│  session state│  task state                 │
│  documents    │  tool data                  │
└─────────────────────────────────────────────┘
                │
                │  ← The Context Engineering Boundary
                │     (selection, compression, retrieval, pinning)
                ▼
┌─────────────────────────────────────────────┐
│            ACTIVE CONTEXT PAYLOAD           │
│  (The only thing the model can reason over) │
└─────────────────────────────────────────────┘
```

The act of crossing this boundary — collapsing unlimited knowledge into minimum high-signal tokens — **is the core problem this system exists to solve**.

---

## Context Source → Module Ownership Table

| Context Source | Primary Owner Module | Storage Entity |
|---|---|---|
| System Instructions | `packages/context_assembler` / `prompts/` | N/A (template) |
| Tool Schemas | `packages/tool_runtime` | N/A (runtime registry) |
| Message Buffer | `packages/memory` | `messages` |
| Core Memory Blocks | `packages/memory` | `memory_blocks` |
| Recall Memory | `packages/memory` / `packages/retrieval` | `recall_events` |
| Archival Memory | `packages/memory` / `packages/retrieval` | `archival_entries` |
| Session State | `packages/state` | `session_state` |
| Task State | `packages/state` | `task_state` |
| Files / Artifacts | `packages/state` / `packages/retrieval` | `open_files_state` |
| Final Assembly Payload | `packages/context_assembler` | `context_assemblies` |

---

## The 6 Context Transformation Operations
Context is not only stored — it is transformed through these discrete, testable operations:

| # | Operation | Description | Owner |
|---|---|---|---|
| 1 | **Selection** | Choose WHAT enters the active context. | `context_assembler` |
| 2 | **Ordering** | Decide the SEQUENCE sections appear in the prompt. | `context_assembler` |
| 3 | **Compaction** | Summarize or compress verbose content to fit the budget. | `context_assembler` / `memory` |
| 4 | **Retrieval** | Fetch relevant chunks from External Memory on demand. | `retrieval` |
| 5 | **Promotion** | Escalate raw context into a more durable memory tier. | `memory` (Sleep-Time) |
| 6 | **Cleanup** | Remove duplicates, expired entries, and noise. | `memory` (Sleep-Time) |

---

## Raw Context vs. Distilled Context

| Type | Description | Examples |
|---|---|---|
| **Raw Context** | Unprocessed, uncompressed information. High noise, low density. | Long uncompressed chat, raw tool outputs, full documents. |
| **Distilled Context** | Semantically processed, curated knowledge. High signal, low tokens. | Stable summaries, clean memory blocks, archived decisions. |

**Design Rule**: The system's job is to continuously convert Raw Context into Distilled Context via Sleep-Time operations. Sleeping on raw context is an anti-pattern.

---

## Context Pollution: Risk Patterns

Context Pollution occurs when too many irrelevant or redundant tokens enter the Active Context, degrading model reasoning quality.

**Warning Signs:**
- Dozens of redundant or near-duplicate tool schemas in the active context.
- Uncompressed raw conversation history exceeding 2K tokens.
- Duplicate evidence from both Recall and Retrieval appearing simultaneously.
- Full raw documents when only a 3-sentence chunk was needed.
- Core Memory blocks that have grown past their `size_limit`.

**Mitigations (all enforced by `context_assembler`):**
- Strict token budgets per context section.
- Deduplication pass before payload finalization.
- Just-in-time retrieval (never pre-load).
- Conservative Core Memory promotion policies.

---

## The Golden Optimization Rule

> **The system MUST NOT optimize for maximum token injection.**
> **It MUST optimize for minimum high-signal tokens per task.**

This is Invariant 5 of the global system contract.

---

## Quick Reference Card

| Concept | Definition |
|---|---|
| `Model` | Stateless local reasoner. Sees only Active Context. |
| `Active Context` | The exact-per-turn assembled payload. Always bounded. |
| `Core Memory` | Pinned, durable high-signal facts. Must stay small. |
| `Recall Memory` | Recent history. Queryable, not always injected. |
| `Archival Memory` | Distilled long-term facts. Retrieved via semantic search. |
| `State` | Explicit system continuity (Session + Task + Files). |
| `Sleep-Time` | Background process improving memory between turns. |
| `Context Assembly` | The act of building the payload. One module owns it. |
