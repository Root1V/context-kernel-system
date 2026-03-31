# AGENTS.md

## Repository Mission
To build a high-signal context engineering system for stateful agents, featuring:
- Per-call context assembly.
- Layered memory architecture.
- Hybrid retrieval systems.
- Tool/MCP runtime orchestration.
- Offline consolidation (sleep-time compute).
- Measurable observability and evaluation.

## Global Principles
1. **High-Signal Context**: Keep context windows lean and relevant.
2. **Separation of Concerns**: Maintain strict boundaries between modules.
3. **Explicit State**: Persist explicit state; do not rely solely on raw history.
4. **Contract-First Design**: Define interfaces and contracts before implementation.
5. **Quality Standards**: Prioritize simple, typed, and highly testable code.
6. **Documentation-Driven**: Every significant change must be reflected in module docs.
7. **Code Over Prompts**: Logic belongs in code or policies, not in prompt strings.
8. **Granularity**: Avoid monolithic files; divide by specific responsibility.

## Working Protocol
- **Research First**: Before touching code, review:
  - `docs/vision/system-overview.md`
  - `docs/architecture/module-boundaries.md`
  - The module-specific `AGENTS.md`.
- **Cross-Module Work**: Update Architecture Decision Records (ADR) or architecture docs first if a change spans multiple modules.
- **Delegation**: If a task exceeds a single logical unit, delegate to specialized sub-agents.

## Modular Rule Loading
Load additional context rules only when required:
- `@docs/vision/invariants.md`
- `@docs/architecture/module-boundaries.md`
- `@docs/architecture/runtime-flows.md`
- `@docs/architecture/storage-model.md`

## Quality & Safety Rules
- **Documentation**: Every module must define its purpose, boundaries, public contracts, dependencies, and non-obvious decisions.
- **Security**:
  - External tools MUST be accessed via `tool_runtime`.
  - LLM provider calls MUST be accessed via `model_adapter`.
  - DB access is restricted to `storage/repositories`.

## Tooling & Environments
- **Manager**: [uv](https://astral.sh/uv) is the primary package and project manager. It automatically manages the Python **virtual environment** (`.venv`).
- **Linter/Formatter**: [Ruff](https://astral.sh/ruff) for fast styling, linting, and formatting.
- **Type Checker**: [Mypy](https://mypy-lang.org/) for strict static type analysis.
- **Testing**: [Pytest](https://docs.pytest.org/) is the test runner. 
  - Standard execution: `uv run pytest`.
  - Continuous Testing: Tests must pass before merging to `develop` or `main`.

## Testing Rules
- Every context assembly policy REQUIRES unit tests.
- Every memory update operation REQUIRES integration tests.
- Every MCP tool integration REQUIRES dedicated fixtures or mock tests.
- Compaction and sleep-time consolidation policies REQUIRES "golden" regression tests.

## CI/CD & Automation
- **GitHub Workflows**: Automated CI/CD pipelines managed via GitHub Actions located in `.github/workflows/`.
- **Pre-commit**: All commits should ideally be checked locally using `ruff check`, `mypy`, and **`pytest`** to ensure no regressions.
- **Auto-deployment**: Stabilization occurs in `develop`, and `main` triggers production-ready releases.
