# Context Kernel System — Agent Guide

> **This file targets any AI coding agent** (Claude Code, OpenCode, and similar tools).
> GitHub Copilot-specific configuration lives in `.github/copilot-instructions.md`.

---

## Mission

This repository implements the **Context Kernel**: a modular runtime for stateful AI systems.
It manages layered conversational memory, token-budget-aware context assembly, hybrid retrieval
(BM25 + pgvector), MCP-based tool orchestration, and background consolidation.

Prioritize **small, safe, and verifiable changes**. Every change must pass the full quality gate
before merging.

---

## Repository Layout

```
packages/
  memory/            # Memory layers: core, recall, archival
  model_adapter/     # LLM provider abstraction (OpenAI, Anthropic, Axonium)
  state/             # Session, task, and open-files state
  storage/           # Data access layer: SQLAlchemy + pgvector
  retrieval/         # Hybrid BM25 + vector search, chunking, rerank
  tool_runtime/      # MCP gateway, tool registry, safety layer
  context_assembler/ # Token-budget-aware context assembly
  orchestrator/      # LangGraph-style turn DAG
  observability/     # Structured logging, traces, metrics, evals
apps/
  api/               # FastAPI (chat, sessions, health) — port 8000
  worker/            # Background worker (compaction, memory cleanup)
prompts/             # System prompts and summary templates
openspec/            # Spec-driven change management (changes/, archive/)
docs/                # ADRs, architecture, backlog
```

Each package under `packages/` has its own `AGENTS.md` with package-specific context.
Read the relevant package's `AGENTS.md` before modifying code inside it.

---

## Architecture

### Turn-Time Flow (DAG)

```
receive_request → load_state → hydrate_memory → [retrieve_context]
  → assemble_context → infer → [tool_loop] → persist_state
```

### Architectural Invariants — Non-Negotiable

| Rule | Rationale |
|------|-----------|
| The model reads **only** the assembled `Context` for that turn. Never raw DB. | Prevents data leaks across sessions. |
| Memory layers are strictly ordered: `message_buffer → core → recall → archival`. | Maintains memory lifecycle integrity. |
| Only `tool_runtime` makes external HTTP calls. | Single security boundary for outbound traffic. |
| Only `model_adapter` imports `openai` or `anthropic`. | Single abstraction layer for LLM providers. |
| Only `storage/repositories/` writes to the database. No raw SQL elsewhere. | Enforces a consistent data access layer. |
| `context_assembler` is a **pure consumer** — it never writes to the DB or executes tools. | Keeps assembly deterministic and side-effect-free. |
| All memory mutations must be auditable via `memory_block_versions`. | Required for replay and debugging. |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| API | FastAPI + Uvicorn |
| Data models | Pydantic v2 |
| Async ORM / DB | SQLAlchemy 2.x async + asyncpg |
| Storage | PostgreSQL 15 + pgvector |
| Vector DB | pgvector (initial); Qdrant as future migration (ADR-002) |
| Orchestration | LangGraph (fallback: `_run_sequential` async) |
| External tools | MCP Protocol via `packages/tool_runtime` (ADR-004) |
| LLM providers | OpenAI, Anthropic, Axonium (local llama-server) |
| Lint / format | ruff (line-length=100, target=py313) |
| Types | mypy (python_version=3.13, strict=false) |
| Tests | pytest + pytest-asyncio (asyncio_mode=strict) |
| Dependencies | **`uv` exclusively** — never pip, pip-tools, or poetry |
| Local infra | Docker Compose (`packages/storage/docker-compose.yml`) — port 5433 |

---

## Naming Conventions

### Files and modules

| Artifact | Filename |
|----------|----------|
| Pydantic models | `models.py` inside the package |
| Business logic | `service.py` |
| DB access | `storage/repositories/<entity>.py` |
| Orchestrator nodes | `orchestrator/nodes/<name>.py` |
| Tests | `packages/<pkg>/tests/test_<module>.py` |

### Cross-package imports

```python
from memory import MemoryService      # ✅ top-level __init__ only
from memory.models import MemoryBlock # ❌ cross-package internal import
```

### Branch naming

```
feature/<name>   # new functionality
fix/<desc>       # bug fix
chore/<task>     # tooling, config, docs, DX
```

### Commits (Conventional Commits)

```
feat(scope): description
fix(scope): description
chore(scope): description
refactor(scope): description
test(scope): description
docs(scope): description
```

---

## Spec-Driven Workflow — MANDATORY

> **No production code may be written or modified without an active OpenSpec.**
> Permitted exceptions: bug fixes, chores (tooling, config, docs).

Mandatory cycle:

1. **Propose** — define the change before writing any code.
2. **Apply** — implement only the tasks listed in the spec.
3. **Verify** — confirm deliverables and pass the quality gate.
4. **Document** — update ADRs, README, architecture docs.
5. **Archive** — archive the spec, commit, push, and open the PR.

Specs live in `openspec/changes/<name>/`. Each spec contains:
- `proposal.md` — motivation, scope, risks
- `design.md` — technical design and contracts
- `tasks.md` — checklist of implementation tasks

---

## Quality Gate

Run before every push:

```bash
bash .git/hooks/pre-push
```

The hook runs three phases:
1. `uv run ruff check packages/ apps/ tests/` + `uv run ruff format --check packages/ apps/ tests/`
2. `uv run mypy packages/`
3. 10 pytest suites (one per package + integration)

All must pass. Fix every failure before pushing.

---

## Common Commands

```bash
# Full quality gate
bash .git/hooks/pre-push

# Lint
uv run ruff check packages/ apps/ tests/

# Format check
uv run ruff format --check packages/ apps/ tests/

# Type check
uv run mypy packages/

# Tests — single package
uv run pytest packages/<pkg>/tests/ -v

# Tests — integration / smoke
uv run pytest tests/ -v

# Add a dependency
uv add <package>

# Sync environment
uv sync

# Start local DB (PostgreSQL + pgvector on port 5433)
docker compose -f packages/storage/docker-compose.yml up -d

# Start API (port 8000)
cd apps/api && PYTHONPATH=../../packages uvicorn app.main:app --reload --port 8000
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
DATABASE_URL=postgresql+asyncpg://kernel:kernel@localhost:5433/context_kernel
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LLM_BASE_URL=http://localhost:8080
LLM_USERNAME=
LLM_PASSWORD=
CHAT_RATE_LIMIT=60/minute
```

Never hardcode credentials, API keys, or production URLs in source code.

---

## Git & PR Rules

```bash
git add -A && git commit -m 'feat(scope): description'
git push origin <branch>
gh pr create --base develop --head <branch> --title '...' --body-file /tmp/pr_body.md
gh pr merge <n> --merge
git checkout develop && git pull
```

- PRs **always** target `develop`, never directly to `main`.
- Promote to `main` only from `develop` via a separate PR.
- Merge strategy: **merge commit** (no squash, no rebase).

---

## Security Rules

- Never hardcode credentials, API keys, or production URLs. Use `.env`.
- All external input (user messages, tool outputs) is untrusted — validate with Pydantic.
- External tools must pass through `packages/tool_runtime/safety.py` before execution.
- Rate limiting on `/chat` is mandatory (ADR-005); do not disable `slowapi`.
- Never use `eval()`, `exec()`, or deserialization without Pydantic validation.

---

## Technology Restrictions

| Forbidden | Use instead |
|-----------|------------|
| `pip`, `pip-tools`, `poetry` | `uv` |
| `import openai` / `import anthropic` outside `model_adapter` | `from model_adapter import ...` |
| Raw SQL outside `storage/repositories/` | Repository classes |
| Cross-package internal imports | Top-level `__init__` only |
| External HTTP calls outside `tool_runtime` | `packages/tool_runtime` |
| `asyncio.run()` inside async context | Only at sync entry points |
| `X \| None` in Pydantic models (Python < 3.10 compat needed) | `Optional[X]` |

---

## Definition of Done

A change is **done** when:

- [ ] `bash .git/hooks/pre-push` → ✅ All checks passed
- [ ] All new behaviors have tests (unit or integration)
- [ ] No cross-package internal imports (top-level `__init__` only)
- [ ] No credentials or secrets in the code
- [ ] ADRs and architecture docs updated if a contract, flow, or decision changed
- [ ] OpenSpec has all tasks marked `[x]` and is archived (for features/refactors)
- [ ] PR merged into `develop`, then promoted to `main`
