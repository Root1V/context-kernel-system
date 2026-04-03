## ADDED Requirements

### Requirement: Assemble Active Context payload per turn
The Context Assembler SHALL produce a single `ActiveContext` object containing the ordered, token-budget-constrained prompt payload for a given turn. It MUST be the exclusive composer — no other module may format prompt sections.

#### Scenario: Full assembly within budget
- **WHEN** all input sections (system instructions, tool schemas, core memory, state summary, message buffer, retrieved chunks) total fewer tokens than the model budget
- **THEN** the assembler includes all sections in canonical priority order and returns an `ActiveContext` with `truncated=False`

#### Scenario: Assembly exceeds token budget — low-priority sections truncated
- **WHEN** the combined token count of all sections exceeds the model's context window limit
- **THEN** the assembler drops or truncates sections in reverse-priority order (retrieved chunks first, message buffer second) until the payload fits, and returns `ActiveContext` with `truncated=True` and a list of `truncated_sections`

#### Scenario: Pinned core memory always survives truncation
- **WHEN** the token budget is critically tight
- **THEN** sections marked `pinned=True` (core memory blocks, system instructions) SHALL never be removed or truncated

#### Scenario: Section ordering is deterministic
- **WHEN** assembly is called twice with identical inputs
- **THEN** the resulting payload byte string MUST be identical

### Requirement: Token budget is model-aware
The assembler SHALL accept a `model_id` parameter and delegate all token counting to the `model_adapter` tokenizer. It MUST NOT hardcode token limits.

#### Scenario: Budget derived from model adapter
- **WHEN** assembly is requested with `model_id="gpt-4o"`
- **THEN** the assembler queries `model_adapter.get_context_limit(model_id)` to determine the available budget

### Requirement: Assembly is stateless
The assembler SHALL NOT hold internal state between calls. All inputs required for assembly MUST be passed explicitly as parameters.

#### Scenario: Concurrent assembly calls do not interfere
- **WHEN** two assembly calls are made concurrently with different session data
- **THEN** each returns its own `ActiveContext` without cross-contamination
