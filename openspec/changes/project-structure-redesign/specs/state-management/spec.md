## ADDED Requirements

### Requirement: Session state is schema-backed and persisted
The state service SHALL expose `get_session_state(session_id) -> SessionState` and `update_session_state(session_id, patch: SessionStatePatch)`. `SessionState` MUST be a Pydantic model and MUST be persisted to the database.

#### Scenario: State survives process restart
- **WHEN** `update_session_state` is called and the process is restarted
- **THEN** `get_session_state` with the same `session_id` returns the previously saved state

#### Scenario: Partial update does not overwrite unrelated fields
- **WHEN** `update_session_state` is called with a patch containing only `active_task_id`
- **THEN** all other `SessionState` fields retain their previous values

### Requirement: Task state tracks execution progress
The state service SHALL expose `get_task_state(task_id) -> TaskState` with fields: `status` (enum: pending, running, blocked, complete, failed), `current_step`, `metadata`. Task state MUST be schema-backed.

#### Scenario: Task status transitions are valid
- **WHEN** `update_task_state` is called with `status="complete"` for a task currently in `"running"`
- **THEN** the transition is accepted and persisted

#### Scenario: Invalid status transition is rejected
- **WHEN** `update_task_state` is called with `status="running"` for a task already in `"complete"`
- **THEN** the service raises a `StateTransitionError`

### Requirement: Open files state tracks active artifacts
The state service SHALL maintain a list of open file handles per session via `OpenFilesState`. Each entry contains `file_path`, `summary`, and `last_modified`.

#### Scenario: Open file summary is retrievable
- **WHEN** a file is added via `add_open_file(session_id, file_path, summary)`
- **THEN** `get_open_files(session_id)` returns an entry with matching path and summary

### Requirement: State is never inferred from message history
The state service SHALL be the sole source of truth for all system states. No module may infer task or session state by reading raw message content.

#### Scenario: State query goes to state service, not messages
- **WHEN** the orchestrator needs to know `is_compiling`
- **THEN** it reads `session_state.is_compiling` (bool) from the state service, not from scanning message text
