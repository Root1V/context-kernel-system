## ADDED Requirements

### Requirement: Scripts have a run comment on the first line
Every script in `examples/` SHALL have a comment on its first line showing the exact command to run it from the repository root, e.g. `# Run: PYTHONPATH=packages python3 examples/01_storage_state_smoke.py`.

#### Scenario: Comment present in all scripts
- **WHEN** any of the 6 scripts is opened
- **THEN** the first line is a `#` comment with the run command

### Requirement: Scripts are numbered and ordered by system depth
The 6 scripts SHALL be named `01_storage_state_smoke.py` through `06_api_worker_e2e.py`. The numbering SHALL reflect increasing depth: foundation layer → data services → assembly/observability → LLM/tools → orchestrator → entry points.

#### Scenario: Files exist with correct names
- **WHEN** `ls examples/*.py` is run from the repo root
- **THEN** six files appear: `01_storage_state_smoke.py`, `02_memory_retrieval_smoke.py`, `03_context_observability_smoke.py`, `04_model_tool_runtime_smoke.py`, `05_orchestrator_direct.py`, `06_api_worker_e2e.py`

### Requirement: Every package is explicitly exercised by at least one script
All 9 packages (`storage`, `state`, `memory`, `retrieval`, `context_assembler`, `observability`, `model_adapter`, `tool_runtime`, `orchestrator`) and both entry points (`apps/api`, `apps/worker`) SHALL be explicitly imported and called in at least one script.

#### Scenario: Package coverage is complete
- **WHEN** all 6 scripts are reviewed
- **THEN** each of the 9 packages and 2 entry points appears as an import in exactly the scripts specified in the design

### Requirement: Each script uses hardcoded realistic data
Every script SHALL use realistic input data (not empty strings or `"test"`) so the output is meaningful. For example, `session_id = "demo-session-001"`, `user_message = "Explain how context assembly works in this system"`.

#### Scenario: Scripts print meaningful output
- **WHEN** any script runs and the underlying service is available
- **THEN** the printed data reflects the hardcoded input, not placeholder strings

### Requirement: Scripts print structured, labeled output
Each script SHALL print `--- <Section Name> ---` headers before each package's output so the developer knows what they are seeing.

#### Scenario: Output has labeled sections
- **WHEN** any script runs
- **THEN** stdout contains at least one `---` section header per package covered
