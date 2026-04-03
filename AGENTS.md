# Context Kernel System — Agent Guide

## Project Overview
Python monorepo that implements a context-aware AI kernel system. It manages conversation memory, retrieval, orchestration, and model adapters for LLM-powered agents.

## Repository Layout
```
packages/          # Importable Python packages (each has its own tests/)
  memory/          # Core, recall, and archival memory layers
  model_adapter/   # LLM provider abstraction (OpenAI, Anthropic, llama)
  state/           # Session, task, and open-files state
  storage/         # DB access layer (SQLAlchemy + pgvector)
  retrieval/       # Hybrid search (BM25 + vector), chunking, rerank
  tool_runtime/    # MCP gateway, tool registry, safety layer
  context_assembler/ # Token-budget-aware context assembly
  orchestrator/    # LangGraph-style turn DAG
  observability/   # Structured logging, tracing spans, metrics, evals
apps/
  api/             # FastAPI server (chat, sessions, health)
  worker/          # Background job worker (compaction, memory cleanup)
prompts/           # System prompts and summary templates
openspec/          # Spec-driven change management (changes/, specs/, archive/)
docs/              # ADRs, architecture docs, task tracking
```

## Tech Stack
- **Python 3.9** (system) for tests; **Python 3.13** (`.venv/`) for lint/type tools
- **FastAPI** + Uvicorn for the API
- **Pydantic v2** for all models — use `Optional[X]` not `X | None` (3.9 compat)
- **ruff** (lint + format), **mypy** (type checking), **pytest** (tests)
- **PostgreSQL** + pgvector for storage (mocked in tests)

## Git Workflow
- **`main`** — production-ready, protected. Never commit directly.
- **`develop`** — integration branch. All feature branches merge here via PR.
- **`feature/<name>`** — one branch per feature/spec. Branch from `develop`.
- **`fix/<name>`** — hotfix branches. Branch from `develop` (or `main` if urgent).

### Branch naming
```
feature/my-feature-name
fix/bug-description
chore/task-description
```

### Commit convention (Conventional Commits)
```
feat: add new capability
fix: correct a bug
chore: tooling, config, deps
refactor: restructure without behavior change
test: add or update tests
docs: documentation only
```

### PR rules
- PRs always target `develop` (not `main`)
- Title follows Conventional Commits format
- Run pre-push hook before pushing: `bash .git/hooks/pre-push`
- Merge strategy: **merge commit** (not squash, not rebase) to preserve history

## Quality Gate (pre-push hook)
The `.git/hooks/pre-push` script runs 3 phases before every push:
1. `ruff check` + `ruff format --check`
2. `mypy packages/`
3. 10 pytest suites (one per package + integration)

All must pass. Run manually: `bash .git/hooks/pre-push`

## Running Tests
```bash
# Single package
python3 -m pytest packages/memory/tests/ -v

# All via hook
bash .git/hooks/pre-push
```

## Running the API
```bash
cd apps/api
PYTHONPATH=../../packages uvicorn app.main:app --reload --port 8000
```

## Spec-Driven Changes (openspec/)
New features start as a spec in `openspec/changes/<name>/`. Use the available skills:
- `opsx:propose` — create a new change proposal
- `opsx:apply` — implement tasks from a spec
- `opsx:archive` — archive a completed change

## Package Import Rules
- Packages may only import from other packages' top-level `__init__`, never from internal submodules.
- `from memory import MemoryService` ✅
- `from memory.models import X` ❌ (cross-package internal import)
