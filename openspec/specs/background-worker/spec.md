## ADDED Requirements

### Requirement: Worker executes compaction jobs asynchronously
The background worker SHALL poll for pending compaction jobs and process each by summarizing the message buffer and promoting high-value content to recall and archival memory layers. Jobs MUST be processed outside the turn-time synchronous path.

#### Scenario: Compaction job summarizes old buffer turns
- **WHEN** a compaction job runs for a session with N messages exceeding the buffer window
- **THEN** the worker summarizes the oldest messages into a `RecallEntry` and removes them from the message buffer

#### Scenario: Worker processes jobs without blocking the API
- **WHEN** 10 compaction jobs are pending
- **THEN** the worker processes them without affecting API response latency

### Requirement: Archival promotion moves aged recall entries to vector store
The worker SHALL periodically scan recall entries that have exceeded `recall_window_hours` and promote them to archival memory by generating embeddings and inserting into the pgvector store.

#### Scenario: Aged recall entry is archived
- **WHEN** a `RecallEntry` timestamp is older than `recall_window_hours`
- **THEN** the worker generates an embedding for its content and inserts an `ArchivalEntry` into the vector store, then removes the recall entry

#### Scenario: Archival promotion is idempotent
- **WHEN** the worker re-processes a recall entry that was already promoted (e.g., due to a retry)
- **THEN** no duplicate `ArchivalEntry` is created

### Requirement: Jobs are schema-backed and persisted before execution
Each job SHALL be represented as a Pydantic `Job` model and persisted to the database before the worker picks it up. The orchestrator dispatches jobs by writing a `Job` row; the worker reads and claims it.

#### Scenario: Job survives worker crash
- **WHEN** the worker crashes mid-job
- **THEN** the job remains in `status="pending"` in the database and is retried on the next polling cycle

#### Scenario: Completed job is marked done
- **WHEN** a worker successfully processes a job
- **THEN** `Job.status` is updated to `"complete"` with a `completed_at` timestamp

### Requirement: Compaction uses the summarization prompt template
The worker SHALL use the `prompts/summaries/compaction_template.md` prompt to generate summaries. The template is the canonical format and MUST NOT be hardcoded inline in the worker logic.

#### Scenario: Template is loaded from file at job execution
- **WHEN** a compaction job runs
- **THEN** the summarization prompt is loaded from `prompts/summaries/compaction_template.md`, not from a hardcoded string in the worker code
