# Repository Operating Rules — Context Kernel System

## Mission
This repository implements the **Context Kernel**: a modular runtime for stateful AI systems. It manages layered conversational memory, token-budget-aware context assembly, hybrid retrieval (BM25 + pgvector), MCP-based tool orchestration, and background consolidation.

Prioritize **small, safe, and verifiable changes**. Every change must pass the full quality gate before merging.

---

## Architecture

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

### Turn-Time Flow (DAG)
```
receive_request → load_state → hydrate_memory → [retrieve_context]
  → assemble_context → infer → [tool_loop] → persist_state
```

### Architectural Invariants (non-negotiable)
- The model **only** reads the `Context Assembly` built for that turn. It never accesses the raw database.
- Memory layers are strictly separated: `message_buffer` → `core` → `recall` → `archival`.
- **Only `tool_runtime`** may execute external tools. No other package makes direct HTTP calls.
- **Only `model_adapter`** calls LLM providers. No other package imports `openai` or `anthropic`.
- **Only `storage/repositories/`** accesses the database. Services never write raw SQL.
- `context_assembler` is a pure consumer — it never writes to the DB or executes tools.
- All memory mutations must be auditable via `memory_block_versions`.

---

## Official Stack

| Layer | Technology |
|---|---------|
| Language | Python 3.13 |
| API | FastAPI + Uvicorn |
| Data models | Pydantic v2 |
| Async ORM / DB | SQLAlchemy 2.x async + asyncpg |
| Storage | PostgreSQL 15 + pgvector (source of truth) |
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
- Pydantic models → `models.py` inside the package
- Business logic → `service.py`
- DB access → `storage/repositories/<entity>.py`
- Orchestrator nodes → standalone functions in `orchestrator/nodes/<name>.py`
- Tests → `packages/<pkg>/tests/test_<module>.py`

### Cross-package imports
```python
from memory import MemoryService          # ✅ top-level __init__ only
from memory.models import MemoryBlock     # ❌ cross-package internal import
```

### Branches
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

## Mandatory Workflow

### Before editing
1. Locate impacted modules and their dependencies.
2. Verify there is no conflicting open spec in `openspec/changes/`.
3. For non-trivial features and refactors: create a spec with `opsx:propose` **before writing any code**.

### After editing
1. Run the full quality gate: `bash .git/hooks/pre-push`
2. Fix all failures before pushing.
3. Do not introduce new dependencies without explicit justification (`uv add <pkg>`).
4. Do not modify `.git/hooks/`, `pyproject.toml` (`[tool.*]` sections), or secrets unless explicitly requested.

### Spec-Driven (BLOCKING for features and refactors)

> **BLOCKING RULE: No production code may be written or modified without an active OpenSpec.**
> Permitted exceptions without a spec: bug fixes, chores (tooling, config, docs).

Mandatory cycle:
1. **Propose** (`opsx:propose`) — define the change before coding.
2. **Apply** (`opsx:apply`) — implement only the tasks listed in the spec.
3. **Verify** (`opsx:verify`) — confirm deliverables and pass the quality gate.
4. **Document** (`opsx:document`) — update ADRs, README, architecture docs.
5. **Archive** (`opsx:archive`) — archive the spec, commit, push, and open the PR.

Available skills (read the SKILL.md before invoking):
- `.github/skills/openspec-propose/SKILL.md`
- `.github/skills/openspec-apply-change/SKILL.md`
- `.github/skills/openspec-verify/SKILL.md`
- `.github/skills/openspec-document/SKILL.md`
- `.github/skills/openspec-archive-change/SKILL.md`
- `.github/skills/openspec-explore/SKILL.md`

---

## Validation Commands

```bash
# Full quality gate (ruff + mypy + 10 test suites) — ALWAYS run before push
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

# Dependencies
uv add <package>        # add
uv sync                 # sync environment
uv run <command>        # run a tool

# Local API
cd apps/api && PYTHONPATH=../../packages uvicorn app.main:app --reload --port 8000

# Local DB
docker compose -f packages/storage/docker-compose.yml up -d
```

---

## Security Rules (Cross-cutting)

- **Never** hardcode credentials, API keys, or production URLs. Use `.env` (see `.env.example`).
- **Never** expose `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `LLM_PASSWORD` in logs, outputs, or comments.
- All external input (user messages, tool outputs) must be treated as untrusted.
- External tools **must** go through `packages/tool_runtime/safety.py` before execution.
- Rate limiting on the `/chat` endpoint is mandatory (ADR-005); do not disable `slowapi`.
- Changes to the MCP gateway require explicit review against ADR-004 before merging.
- Do not use `eval()`, `exec()`, or deserialization without Pydantic validation.

---

## Technology Restrictions

- **Forbidden**: `pip`, `pip-tools`, or `poetry` — use `uv` only.
- **Forbidden**: importing `openai` or `anthropic` outside `packages/model_adapter/`.
- **Forbidden**: writing raw SQL outside `packages/storage/repositories/`.
- **Forbidden**: importing internal submodules of another package (top-level `__init__` only).
- **Forbidden**: making external HTTP calls outside `packages/tool_runtime/`.
- **Forbidden**: `X | None` in Pydantic models — use `Optional[X]` only if targeting Python < 3.10; prefer `X | None` with Python 3.13.
- **Forbidden**: calling `asyncio.run()` inside an already-async context — only at sync entry points.
- LangGraph is the orchestration runtime; `_run_sequential` is the fallback for tests/local.

---

## Git & PR Rules

### Commit + push + PR sequence
```bash
git add -A && git commit -m 'feat(scope): description'
git push origin <branch>
# Write PR body to a temp file to avoid shell quoting issues:
gh pr create --base develop --head <branch> --title '...' --body-file /tmp/pr_body.md
gh pr merge <n> --merge
git checkout develop && git pull
```

### PR rules
- PRs **always** target `develop`, never directly to `main`.
- Promote to `main` only from `develop` via a separate PR after validating on develop.
- Merge strategy: **merge commit** (no squash, no rebase) to preserve history.
- Title follows Conventional Commits format.
- PR body must include:
  - **Root cause / motivation**
  - **Impact** (which modules change and why)
  - **Identified risks**
  - **Validations executed** (quality gate output)

---

## Definition of Done

A change is **done** when:

- [ ] Full quality gate passes: `bash .git/hooks/pre-push` → ✅ All checks passed
- [ ] All new behaviors have tests (unit or integration)
- [ ] No cross-package internal imports (top-level `__init__` only)
- [ ] No credentials or secrets in the code
- [ ] ADRs and architecture docs are updated if a contract, flow, or decision changed
- [ ] The OpenSpec has all tasks marked `[x]` and is archived (for features/refactors)
- [ ] PR is merged into `develop` and subsequently into `main`

---

## Architecture

```
packages/
  memory/            # Capas de memoria: core, recall, archival
  model_adapter/     # Abstracción de proveedores LLM (OpenAI, Anthropic, Axonium)
  state/             # Estado de sesión, tarea y archivos abiertos
  storage/           # Capa de acceso a datos: SQLAlchemy + pgvector
  retrieval/         # Búsqueda híbrida BM25 + vector, chunking, rerank
  tool_runtime/      # MCP gateway, registro de tools, capa de seguridad
  context_assembler/ # Ensamble de contexto con presupuesto de tokens
  orchestrator/      # DAG de turno estilo LangGraph
  observability/     # Logging estructurado, trazas, métricas, evals
apps/
  api/               # FastAPI (chat, sessions, health) — puerto 8000
  worker/            # Worker de background (compactación, limpieza de memoria)
prompts/             # System prompts y plantillas de resumen
openspec/            # Gestión de cambios spec-driven (changes/, archive/)
docs/                # ADRs, arquitectura, backlog
```

### Flujo de Turn-Time (DAG)
```
receive_request → load_state → hydrate_memory → [retrieve_context]
  → assemble_context → infer → [tool_loop] → persist_state
```

### Invariantes arquitecturales (no negociables)
- El modelo **solo** lee el `Context Assembly` ensamblado para ese turno. Nunca accede a la BD cruda.
- Las capas de memoria son estrictamente separadas: `message_buffer` → `core` → `recall` → `archival`.
- **Solo `tool_runtime`** puede ejecutar tools externas. Ningún otro paquete hace llamadas HTTP directas.
- **Solo `model_adapter`** llama a proveedores LLM. Ningún otro paquete importa `openai` ni `anthropic`.
- **Solo `storage/repositories/`** accede a la base de datos. Los servicios nunca escriben SQL directo.
- `context_assembler` es consumidor puro — nunca escribe en BD ni ejecuta tools.
- Todos los cambios de memoria deben quedar auditables vía `memory_block_versions`.

---

## Official Stack

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.9 (runtime/tests), Python 3.13 (venv lint/tipos) |
| API | FastAPI + Uvicorn |
| Modelos de datos | Pydantic v2 |
| ORM / BD asíncrona | SQLAlchemy 2.x async + asyncpg |
| Almacenamiento | PostgreSQL 15 + pgvector (fuente de verdad) |
| Vector DB | pgvector (inicial); Qdrant como migración futura (ADR-002) |
| Orquestación | LangGraph (fallback: `_run_sequential` async) |
| Tools externas | MCP Protocol via `packages/tool_runtime` (ADR-004) |
| LLM providers | OpenAI, Anthropic, Axonium (llama-server local) |
| Lint / formato | ruff (line-length=100, target=py39) |
| Tipos | mypy (python_version=3.13, strict=false) |
| Tests | pytest + pytest-asyncio (asyncio_mode=strict) |
| Dependencias | **`uv` exclusivamente** — nunca pip, pip-tools ni poetry |
| Infra local | Docker Compose (`packages/storage/docker-compose.yml`) — puerto 5433 |

---

## Naming Conventions

### Archivos y módulos
- Modelos Pydantic → `models.py` dentro del paquete
- Lógica de negocio → `service.py`
- Acceso a BD → `storage/repositories/<entidad>.py`
- Nodos del orquestador → funciones standalone en `orchestrator/nodes/<nombre>.py`
- Tests → `packages/<pkg>/tests/test_<módulo>.py`

### Imports entre paquetes
```python
from memory import MemoryService          # ✅ solo top-level __init__
from memory.models import MemoryBlock     # ❌ importación interna cruzada
```

### Ramas
```
feature/<nombre>   # nueva funcionalidad
fix/<descripción>  # corrección de bug
chore/<tarea>      # tooling, config, docs, DX
```

### Commits (Conventional Commits)
```
feat(scope): descripción
fix(scope): descripción
chore(scope): descripción
refactor(scope): descripción
test(scope): descripción
docs(scope): descripción
```

---

## Mandatory Workflow

### Antes de editar
1. Localizar módulos impactados y sus dependencias.
2. Verificar que no existe un spec abierto en conflicto (`openspec/changes/`).
3. Para features y refactors no triviales: crear spec con `opsx:propose` **antes de escribir código**.

### Después de editar
1. Ejecutar el quality gate completo: `bash .git/hooks/pre-push`
2. Corregir todos los fallos antes de hacer push.
3. No introducir nuevas dependencias sin justificación explícita (`uv add <pkg>`).
4. No modificar `.git/hooks/`, `pyproject.toml` (sección `[tool.*]`) ni secretos salvo petición explícita.

### Spec-Driven (BLOQUEANTE para features y refactors)

> **BLOCKING RULE: No se puede escribir ni modificar código de producción sin un OpenSpec activo.**
> Excepciones permitidas sin spec: bug fixes, chores (tooling, config, docs).

Ciclo obligatorio:
1. **Propose** (`opsx:propose`) — definir el cambio antes de codificar.
2. **Apply** (`opsx:apply`) — implementar solo las tareas del spec.
3. **Verify** (`opsx:verify`) — confirmar deliverables y pasar el quality gate.
4. **Document** (`opsx:document`) — actualizar ADRs, README, docs de arquitectura.
5. **Archive** (`opsx:archive`) — archivar el spec, commit, push y PR.

Skills disponibles (leer el SKILL.md antes de ejecutar):
- `.github/skills/openspec-propose/SKILL.md`
- `.github/skills/openspec-apply-change/SKILL.md`
- `.github/skills/openspec-verify/SKILL.md`
- `.github/skills/openspec-document/SKILL.md`
- `.github/skills/openspec-archive-change/SKILL.md`
- `.github/skills/openspec-explore/SKILL.md`

---

## Validation Commands

```bash
# Quality gate completo (ruff + mypy + 10 suites de tests) — SIEMPRE antes de push
bash .git/hooks/pre-push

# Lint
.venv/bin/ruff check packages/ apps/ tests/

# Formato
.venv/bin/ruff format --check packages/ apps/ tests/

# Tipos
.venv/bin/mypy packages/

# Tests — paquete individual (usa python3 del sistema, no del venv)
python3 -m pytest packages/<pkg>/tests/ -v

# Tests — integración / smoke
python3 -m pytest tests/ -v

# Dependencias
uv add <package>        # añadir
uv sync                 # sincronizar entorno
uv run <comando>        # ejecutar herramienta

# API local
cd apps/api && PYTHONPATH=../../packages uvicorn app.main:app --reload --port 8000

# BD local
docker compose -f packages/storage/docker-compose.yml up -d
```

---

## Security Rules (Transversales)

- **Nunca** hardcodear credenciales, API keys ni URLs de producción. Usar `.env` (ver `.env.example`).
- **Nunca** exponer `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` ni `LLM_PASSWORD` en logs, outputs ni comentarios.
- Todo input externo (mensajes de usuario, tool outputs) debe tratarse como no confiable.
- Las tools externas **deben** pasar por `packages/tool_runtime/safety.py` antes de ejecutarse.
- El rate limiting del endpoint `/chat` es obligatorio (ADR-005); no deshabilitar `slowapi`.
- Los cambios al MCP gateway requieren revisión explícita contra ADR-004 antes de fusionarse.
- No usar `eval()`, `exec()` ni deserialización sin validación con Pydantic.

---

## Technology Restrictions

- **Prohibido** usar `pip`, `pip-tools` o `poetry` — solo `uv`.
- **Prohibido** importar `openai` o `anthropic` fuera de `packages/model_adapter/`.
- **Prohibido** escribir SQL directo fuera de `packages/storage/repositories/`.
- **Prohibido** importar subbmódulos internos de otro paquete (solo `__init__` público).
- **Prohibido** hacer llamadas HTTP externas fuera de `packages/tool_runtime/`.
- **Prohibido** usar `X | None` en modelos Pydantic — usar `Optional[X]` (compatibilidad Python 3.9).
- **Prohibido** hacer `asyncio.run()` dentro de un contexto ya async — solo en entry points sync.
- LangGraph es el runtime de orquestación; `_run_sequential` es el fallback para tests/local.

---

## Git & PR Rules

### Secuencia commit + push + PR
```bash
git add -A && git commit -m 'feat(scope): descripción'
git push origin <rama>
# PR body en archivo temporal para evitar problemas de quoting:
gh pr create --base develop --head <rama> --title '...' --body-file /tmp/pr_body.md
gh pr merge <n> --merge
git checkout develop && git pull
```

### Reglas de PR
- PRs **siempre** apuntan a `develop`, nunca directamente a `main`.
- Promote a `main` solo desde `develop` via otro PR después de validar en develop.
- Merge strategy: **merge commit** (no squash, no rebase) para preservar historial.
- El título sigue Conventional Commits.
- El body del PR debe incluir:
  - **Causa raíz / motivación**
  - **Impacto** (qué módulos cambian y por qué)
  - **Riesgos identificados**
  - **Validaciones ejecutadas** (output del quality gate)

---

## Definition of Done

Un cambio está **terminado** cuando:

- [ ] El quality gate pasa completo: `bash .git/hooks/pre-push` → ✅ All checks passed
- [ ] Todos los nuevos comportamientos tienen tests (unitarios o de integración)
- [ ] No hay imports cruzados entre paquetes (solo `__init__` público)
- [ ] No hay credenciales ni secretos en el código
- [ ] Los ADRs y docs de arquitectura están actualizados si cambia un contrato, flujo o decisión
- [ ] El spec OpenSpec tiene todos los tasks marcados `[x]` y está archivado (para features/refactors)
- [ ] El PR está mergeado en `develop` y posteriormente en `main`
