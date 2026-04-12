# Context Kernel System

A modular runtime for stateful AI systems. It manages layered memory, hybrid retrieval, token-budget-aware context assembly, tool orchestration, and sleep-time consolidation — exposing everything through a FastAPI chat endpoint backed by PostgreSQL + pgvector.

---

## Architecture

### Packages (`packages/`)

| Package | Responsibility |
|---|---|
| `memory` | Core, recall, and archival memory layers; consolidation and summarization |
| `model_adapter` | Provider boundary for OpenAI, Anthropic, and local LLMs via Axonium |
| `state` | Session, task, and open-files state management |
| `storage` | SQLAlchemy + pgvector DB access layer and repositories |
| `retrieval` | Hybrid search (BM25 + vector), chunking, and reranking |
| `tool_runtime` | MCP gateway, tool registry, and safety layer |
| `context_assembler` | Token-budget-aware context assembly with pluggable policies |
| `orchestrator` | LangGraph-style turn DAG connecting all packages |
| `observability` | Structured logging, tracing spans, metrics, and evals |

### Apps (`apps/`)

| App | Responsibility |
|---|---|
| `api` | FastAPI server — `/chat`, `/sessions`, `/health` endpoints |
| `worker` | Background job worker — memory compaction and cleanup |

---

## Prerequisites

- **Python 3.13** (for the virtual environment and tooling)
- **Python 3.9+** (system install, used by the test runner)
- **[uv](https://github.com/astral-sh/uv)** — the only allowed package manager
- **Docker** (for PostgreSQL + pgvector)

> **Note:** All dependency operations must use `uv`. Never use `pip`, `pip-tools`, or `poetry`.

---

## Quick Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd context-kernel-system

# 2. Sync the virtual environment
uv sync

# 3. Copy and fill in the environment file
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL and at least one LLM API key

# 4. Start PostgreSQL + pgvector
docker compose -f packages/storage/docker-compose.yml up -d

# 5. Run the example scripts (read-only, no server needed for most)
PYTHONPATH=packages uv run python3 examples/01_storage_state_smoke.py
```

### Environment Variables (`.env`)

```dotenv
DATABASE_URL=postgresql+asyncpg://kernel:kernel@localhost:5433/context_kernel
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LLM_BASE_URL=http://localhost:8080   # local llama-server endpoint
LLM_USERNAME=
LLM_PASSWORD=
CHAT_RATE_LIMIT=60/minute
```

---

## Example Scripts

Each script is self-contained and exercises one layer of the stack:

| Script | Layer |
|---|---|
| `examples/01_storage_state_smoke.py` | Storage + State — ORM table listing, `SessionState` reads/writes |
| `examples/02_memory_retrieval_smoke.py` | Memory + Retrieval — seeds and queries PostgreSQL |
| `examples/03_context_observability_smoke.py` | Context Assembler + Observability |
| `examples/04_model_tool_runtime_smoke.py` | Model Adapter + Tool Runtime — provider calls and tool registry |
| `examples/05_orchestrator_direct.py` | Full orchestrator DAG — exercises all 9 packages in one call |
| `examples/06_api_worker_e2e.py` | API E2E + Worker — HTTP round-trip through FastAPI and the background worker |

Run any script:

```bash
PYTHONPATH=packages uv run python3 examples/<script>.py
```

---

## Running the API

```bash
cd apps/api
PYTHONPATH=../../packages uvicorn app.main:app --reload --port 8000
```

Endpoints:
- `POST /chat` — chat turn (rate-limited, 60 req/min by default)
- `GET /sessions` — list sessions
- `GET /health` — health check

---

## Local LLM with Axonium

The `model_adapter` package supports local models served by **llama-server** via the **Axonium SDK**.

Supported model IDs (use the `local/` prefix):
- `local/mistral-7b-instruct`
- `local/llama3-8b` (32 768-token context)

### Install the Axonium SDK

The SDK wheel must be built from source and linked locally (Python 3.13 venv only):

```bash
# Clone and build the wheel
git clone https://github.com/axonium-ai/axonium-sdk /tmp/axonium-sdk
cd /tmp/axonium-sdk && python3 setup.py bdist_wheel

# Install into the project venv
cd <repo-root>
uv add --find-links /tmp/axonium-sdk/dist axonium
```

Start llama-server, set `LLM_BASE_URL` in `.env`, then call the API with model `local/mistral-7b-instruct`.

> The `axonium` dependency carries a `python_full_version >= '3.13'` marker — it is skipped automatically on older Pythons.

---

## Testing

Tests use **system Python 3.9**. Each package has its own test suite:

```bash
# Single package
python3 -m pytest packages/memory/tests/ -v

# All suites + lint + type checks (same as the pre-push hook)
bash .git/hooks/pre-push
```

Lint and type checking use the `.venv` (Python 3.13):

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy packages/
```

---

## Branch Workflow

| Branch | Purpose |
|---|---|
| `main` | Production-ready, protected. Never commit directly. |
| `develop` | Integration branch. All PRs target here. |
| `feature/<name>` | One branch per feature/spec. Branch from `develop`. |
| `fix/<name>` | Bug fixes. Branch from `develop`. |
| `chore/<name>` | Tooling, config, docs. Branch from `develop`. |

Commit style follows [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.

---

## Documentation

### Architecture Decision Records (`docs/adr/`)

| ADR | Decision |
|---|---|
| [ADR-001](docs/adr/ADR-001-python-fastapi.md) | Python + FastAPI as the runtime foundation |
| [ADR-002](docs/adr/ADR-002-postgres-pgvector.md) | PostgreSQL + pgvector for storage |
| [ADR-003](docs/adr/ADR-003-langgraph-orchestrator.md) | LangGraph-style orchestrator DAG |
| [ADR-004](docs/adr/ADR-004-mcp-boundary.md) | MCP as the tool-runtime boundary |
| [ADR-005](docs/adr/ADR-005-rate-limiting-chat.md) | Rate limiting on the chat endpoint |
| [ADR-006](docs/adr/ADR-006-local-llm-axonium-adapter.md) | Local LLM support via Axonium adapter |

### Other docs

- [`docs/architecture/`](docs/architecture/) — context map, module boundaries, runtime flows, storage model
- [`docs/tasks/`](docs/tasks/) — backlog, milestones, roadmap
- [`docs/vision/`](docs/vision/) — glossary, invariants, system overview

---

## Spec-Driven Workflow (OpenSpec)

All non-trivial feature work follows the OpenSpec cycle:

1. **Propose** — create a spec in `openspec/changes/<name>/` before writing any code
2. **Apply** — implement only the tasks listed in the spec
3. **Verify** — cross-check deliverables and run the quality gate
4. **Document** — update ADRs, README, and architecture docs
5. **Archive** — move the spec to `openspec/changes/archive/`, push the branch, open a PR to `develop`

Active specs live in `openspec/specs/`. Completed changes are in `openspec/changes/archive/`.

> Bug fixes and chore tasks (tooling, config, docs) are exempt from this rule.
