## ADDED Requirements

### Requirement: Memory is organized in four explicit layers
The memory service SHALL expose four distinct layers — message buffer, core memory, recall memory, and archival memory — each with separate read/write operations. No layer SHALL be a raw text blob.

#### Scenario: Each layer returns typed objects
- **WHEN** `memory_service.get_core_memory(session_id)` is called
- **THEN** it returns a list of `CoreMemoryBlock` Pydantic model instances, never a raw string

#### Scenario: Layers are independently readable
- **WHEN** a caller reads archival memory
- **THEN** it MUST NOT trigger a read or mutation of core memory or the message buffer

### Requirement: Core memory blocks have a token footprint limit
The memory service SHALL enforce a maximum total token count for all core memory blocks combined per session. Attempting to add a block that exceeds the limit SHALL trigger eviction of the lowest-scored existing block.

#### Scenario: New block fits within budget
- **WHEN** adding a `CoreMemoryBlock` and the total token count after addition is within the configured limit
- **THEN** the block is persisted and returned in subsequent `get_core_memory` calls

#### Scenario: New block causes overflow — lowest-scored block is evicted
- **WHEN** adding a `CoreMemoryBlock` would exceed the core memory token limit
- **THEN** the block with the lowest `importance_score` is removed and the new block is inserted

### Requirement: Archival memory uses vector similarity for retrieval
The archival memory layer SHALL store entries as embeddings and expose a `search_archival(query, top_k)` method that returns the top-k semantically similar entries.

#### Scenario: Search returns ranked results
- **WHEN** `search_archival(query="user's coding preferences", top_k=5)` is called
- **THEN** the service returns up to 5 `ArchivalEntry` objects ordered by cosine similarity descending

### Requirement: Message buffer is bounded by recency
The message buffer SHALL retain only the N most recent conversation turns, configurable via `message_buffer_size`. Older turns are automatically dropped from the buffer (not deleted — they are candidates for recall/archival promotion).

#### Scenario: Buffer overflow drops oldest turn
- **WHEN** a new message is appended and the buffer is at capacity
- **THEN** the oldest message is removed from the buffer and a compaction event is emitted

### Requirement: Recall memory is a structured log of recent events
The recall memory layer SHALL store structured `RecallEntry` objects (tool calls, key decisions, citations) that occurred within a configurable recency window.

#### Scenario: Recall entries expire after window
- **WHEN** a `RecallEntry` timestamp is older than `recall_window_hours`
- **THEN** it SHALL NOT be returned by `get_recall_entries` and is eligible for archival promotion
