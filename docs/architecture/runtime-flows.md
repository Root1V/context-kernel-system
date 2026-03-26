# Architecture: Runtime Flows

## Purpose
This document strictly defines the execution runtimes and flow topologies across the *Context Kernel* system. It operates as the "map" for the LangGraph DAG paths and offline background workers.

It does **not** define internal Python implementation details per class; its sole objective is to formally state:
- What sequences execute during an active User Turn.
- What background processes occur Between Turns (Sleep-Time).
- Which modular packages `OWN` each responsibility.
- The explicit **Inputs and Outputs** transported between nodes.

---

## High-Level Topology Overview

The system runs on two entirely physically separated runtimes:
1. **Turn-Time Flow (The Synchronous DAG)**: The immediate, stateful LangGraph execution resolving a user's prompt.
2. **Between-Turn Flow (The Asynchronous Worker)**: The offline computation resolving memory compaction and knowledge promotion via generic task queues.

```text
               +----------------------+
               |  TURN-TIME FLOW      |
               |  (request -> answer) |
               +----------+-----------+
                          |
                          v
               +----------------------+
               | BETWEEN-TURN FLOW    |
               | (memory improvement) |
               +----------------------+
```

---

## 1. Turn-Time Flow (LangGraph Orchestration)

**Objective**: Convert a stateless user request into a state-aware, perfectly assembled response using Layered Memory, Context Assembly, and orchestrated Sub-Tools.

### High-Level DAG Pipeline
```text
[1] User Request
     │
[2] API validates & Orchestrator receives
     │
[3] Load Session/Task State
     │
[4] Hydrate Memory Layers
     │
[5] Retrieve External Context (Conditional)
     │
[6] Assemble Active Context Budget
     │
[7] Execute LLM Inference
     │
[8] Optional MCP Tool Loop (Conditional)
     │
[9] Return Response Payload
     │
[10] Persist State & Traces
```

---

### Node 1.1: Receive Request
- **Owner**: `apps/api` (FastAPI) -> `packages/orchestrator` (LangGraph)
- **Input**: `session_id`, `user_message`, `execution_profile`.
- **Output**: Normalized `TurnRequest` Pydantic object.
- **Invariant**: The FastAPI layer MUST NOT contain any context-assembly logic. It exclusively validates auth/payloads and triggers the asynchronous LangGraph orchestrator.

### Node 1.2: Load State
- **Owner**: `packages/state`
- **Reads**: Current explicit `session_profile`, active workflow `task_status`, open artifact handles.
- **Output**: `RuntimeState` Schema.
- **Invariant**: State must be explicit. System behaviors must rely on parsed JSON attributes (e.g., `is_compiling=True`), never "guessing" state from reading raw chat histories.

### Node 1.3: Hydrate Memory Layers
- **Owner**: `packages/memory`
- **Reads**: Core Memory blocks, short-term message buffers, queued recall pointers.
- **Output**: `MemorySnapshot`.
- **Invariant**: This node does NOT format text for the prompt. It only gathers the structured memory blocks required by the Assembler.

### Node 1.4: Decide Retrieval (Conditional Router)
- **Owner**: `packages/orchestrator` / `packages/retrieval`
- **Decisions**: Does the prompt require semantic lookup? External API hit? Document loading?
- **Output**: `RetrievalPlan`.
- **Invariant**: Retrieval must NEVER be "always-on" by default. It inherently consumes time and tokens, so must be triggered intentionally.

### Node 1.5: Retrieve External Context
- **Owner**: `packages/retrieval`
- **Sources**: Indexed documents, archival memory blocks.
- **Output**: `List[RetrievedContext]` with strict traceability metadata.
- **Invariant**: Unfiltered document dumps are forbidden. Retrieval returns ranked chunks isolated to the exact query footprint.

### Node 1.6: Assemble Active Context (The Bottleneck)
- **Owner**: `packages/context_assembler`
- **Inputs**: `[RuntimeState, MemorySnapshot, RetrievedContext, ToolSchema]`
- **Responsibilities**: Token budgeting, duplicate deduction, prompt templating, section ordering.
- **Output**: `ContextAssembly` (The final raw string or structured payload for the LLM).
- **Invariant**: This is the ONLY domain authorized to build the final payload.

### Node 1.7: Model Inference (Call Model)
- **Owner**: `packages/model_adapter`
- **Input**: `ContextAssembly`, provider configs (OpenAI vs Anthropic parameters).
- **Output**: `RawModelResponse`, usage statistics, stop codes.
- **Invariant**: Vendor-specific abstractions exist exclusively here. No upstream node should ever reference target LLM prompt schemas directly.

### Node 1.8: MCP Tool Loop (Conditional Edge)
- **Owner**: `packages/orchestrator` -> `packages/tool_runtime`
- **Trigger**: The model generated a `tool_call` request.
- **Loop Flow**:
```text
  [Orchestrator Detects Tool Call]
              │
      [Tool Runtime Executes via MCP]
              │
    [Result is Validated & Normalized]
              │
  [Context Assembler Re-runs to append result]
              │
    [Model Call repeats with new Context]
```
- **Invariant**: Tools NEVER govern flow routing. The Orchestrator dictates the execution edge.

### Node 1.9: Persist Outcome
- **Owner**: `packages/state`, `packages/storage`
- **Persists**: Appends conversation events, writes new task state, logs full tool-call JSON traces.

---

## 2. Between-Turn Flow (Sleep-Time Computation)

**Objective**: Asynchronously optimize the system's memory and state payloads while the user is idle, ensuring the *Turn-Time* execution remains fast and high-signal.

```text
[ New Sessions / Events / Dead Turns ]
                  │
        [ Sleep-Time Worker Schedule ]
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
[ Compact ]   [ Clean ]    [ Promote ]
    │             │             │
    └─────────────┼─────────────┘
                  ▼
    [ Improved Persistent State DB ]
```

### Phase 2.1: Gather Raw Material
- **Owner**: `apps/worker`
- **Sources**: Stale memory buffers, verbose tool outputs, completed workflows.

### Phase 2.2: Compaction
- **Goal**: Algorithmic reduction of token footprint without losing signal.
- **Preserves**: Decisions made, explicit constraints, unresolved issues.
- **Garbage Collects**: "Thinking" tokens, repetitive tool failures, small talk.

### Phase 2.3: Cleanup & Merge
- **Goal**: Hard-delete or fuse database entries.
- **Resolves**: Duplicated Archival entries or merged Core profile traits.
- **Invariant**: Irrecoverable destruction of traceability is strictly forbidden.

### Phase 2.4: Knowledge Promotion
- **Goal**: Escalate implicit context into Explicit State.
- **Examples**: 
  - *Extracting* a user's framework preference from the chat buffer -> *Writing* it to `Core Memory`.
  - *Distilling* a long debugging session -> *Vectorizing* an `Archival Memory` post-mortem.

---

## 3. Error Fallback Topologies

### 3.1: Token Budget Overflow
```text
[ Assembler Detects Max Context Breach ]
                  │
      [ Trigger Aggressive Compaction ]
                  │
        ( If Still Breached )
                  │
      [ Fail Safe: Reject Request Early ]
```

### 3.2: Retrieval / RAG Failure
```text
[ Retrieval Node Fails (DB down, timeout) ]
                  │
[ Trap Exception in Orchestrator ]
                  │
[ Fallback: Pass to Assembler with flag ]
                  │
[ Model dynamically replies error reason ]
```

### 3.3: Tool Execution Failure
```text
[ Tool Runtime Error (e.g. 404, bad schema) ]
                  │
      [ Normalize Error to String ]
                  │
 [ Inject "TOOL_FAILED: <reason>" into Assembler ]
```

---

## 4. Universal Observability Trace Skeleton
Every request MUST natively output a structured execution trace mirroring the DAG path:
1. `TURN_ID` generated.
2. `state_hydrated_ms`
3. `memory_snapshot_tokens`
4. `retrieval_chunks_injected`
5. `assembler_final_context_size`
6. `model_inference_ms` & `prompt_tokens`
7. `tool_calls[]` (if triggered)
8. `state_persisted_ms`

---

## 5. Summary Non-Goals
This document does **NOT** define:
- Exact ERD Database schemas (`packages/storage` boundary).
- Exact REST API payloads (`apps/api` boundary).
- Individual Python Class boundaries (`packages/*` logic).s documentos y en los módulos correspondientes.
