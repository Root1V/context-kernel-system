## ADDED Requirements

### Requirement: Orchestrator exposes a single async entry point
The orchestrator SHALL expose `orchestrate(turn_request: TurnRequest) -> TurnResponse` as its sole public function. All internal DAG steps are hidden behind this contract.

#### Scenario: Happy-path turn completes without tool calls
- **WHEN** `orchestrate` is called with a valid `TurnRequest` and the LLM response requires no tool calls
- **THEN** a `TurnResponse` is returned containing the assistant message, session_id, and persisted state metadata

#### Scenario: Tool-call loop executes and resolves
- **WHEN** the LLM response contains tool call requests
- **THEN** the orchestrator executes the tool loop, appends tool results to the message buffer, and re-runs inference until no further tool calls are requested or `max_tool_iterations` is reached

#### Scenario: Max tool iterations reached — returns partial response
- **WHEN** the tool call loop reaches `max_tool_iterations` without resolving
- **THEN** the orchestrator returns a `TurnResponse` with `status="tool_limit_reached"` and the last available assistant content

### Requirement: Each DAG node owns a single responsibility
The Turn-Time DAG SHALL contain the following nodes in order: `receive_request`, `load_state`, `hydrate_memory`, `retrieve_context`, `assemble_context`, `infer`, `tool_loop` (conditional), `persist_state`. Each node MUST delegate to the appropriate package and MUST NOT contain context-assembly, memory-management, or retrieval logic directly.

#### Scenario: FastAPI triggers orchestrator without assembly logic
- **WHEN** the `/chat` API endpoint receives a request
- **THEN** it MUST call `orchestrate()` and SHALL NOT invoke any `context_assembler`, `memory`, or `retrieval` functions directly

### Requirement: State is checkpointed after each node
The orchestrator SHALL persist the `RuntimeState` after each DAG node completes, using the storage layer. If the process crashes mid-turn, a retry SHALL resume from the last checkpoint.

#### Scenario: Resume from checkpoint after failure
- **WHEN** a process restart occurs after `hydrate_memory` node completed but before `assemble_context`
- **THEN** replaying the DAG for the same `turn_id` SHALL skip `receive_request`, `load_state`, and `hydrate_memory` and resume from `retrieve_context`

### Requirement: Retrieval node is conditional
The orchestrator SHALL skip the `retrieve_context` node when the `RuntimeState.retrieval_needed` flag is `False`.

#### Scenario: Simple conversational turn skips retrieval
- **WHEN** `RuntimeState.retrieval_needed == False`
- **THEN** the `retrieve_context` node is bypassed and `assemble_context` receives an empty `retrieved_chunks` list
