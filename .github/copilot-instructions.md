# GitHub Copilot Instructions — Context Kernel System

## Git & Branching

- **Default base branch for PRs is `develop`**, never `main`.
- Feature branches: `feature/<name>`, fix branches: `fix/<name>`.
- When asked to create a branch, always branch from `develop`.
- When asked to commit + push + PR, the sequence is:
  1. `git add -A && git commit -m '<conventional commit message>'`
  2. `git push origin <branch>`
  3. `gh pr create --base develop --head <branch> --title '...' --body-file <file>`
  4. Use a temp file (`/tmp/pr_body.md`) for the PR body to avoid shell quoting issues.
- Merge strategy: **merge commit** (`gh pr merge <n> --merge`).
- After merging, pull develop locally: `git checkout develop && git pull`.

## Before Every Push
Always run the pre-push hook first:
```bash
bash .git/hooks/pre-push
```
Fix any failures before pushing. The hook runs: ruff lint, ruff format check, mypy, and 10 test suites.

## Code Style
- **Dependencies must be managed exclusively with `uv`** — never use `pip`, `pip-tools`, or `poetry`.
  - Add a dependency: `uv add <package>`
  - Sync the environment: `uv sync`
  - Run a tool: `uv run <command>`
- Python 3.9 compatibility — use `Optional[X]` not `X | None` in Pydantic models.
- Line length: 100 chars (ruff config).
- All new code must pass `ruff check` and `ruff format --check`.
- Type annotations required on all public functions.

## Testing
- Every package has tests in `packages/<pkg>/tests/`.
- Run a single suite: `python3 -m pytest packages/<pkg>/tests/ -v`
- Do not skip tests without a clear reason.
- System python (`python3`) for tests; venv python (`.venv/bin/python`) for ruff/mypy.

## Project Conventions
- Pydantic models live in `models.py` within each package.
- Services are in `service.py`; repositories in `storage/repositories/`.
- Orchestrator nodes are standalone functions in `orchestrator/nodes/`.
- Never import cross-package internal submodules — only top-level `__init__` exports.
- `from memory import MemoryService` ✅  |  `from memory.models import X` ❌

## Spec-Driven Workflow (MANDATORY)

> **BLOCKING RULE: No production code may be written, modified, or proposed without an active OpenSpec change.**
> This applies to new features, refactors, and any non-trivial logic change.
> Bug fixes and chore tasks (tooling, config, docs) are the only exceptions.

The mandatory cycle for every change is:
1. **Propose** — create a spec with `opsx:propose` before writing any code.
2. **Apply** — implement only the tasks defined in the spec with `opsx:apply`.
3. **Archive** — mark the change as complete with `opsx:archive` after the PR merges.

If asked to implement something that has no open spec:
- Do NOT write the code.
- Instead, propose a spec first using `opsx:propose`.
- Wait for the user to confirm the spec before proceeding to implementation.

Skills available:
- Propose: read `.github/skills/openspec-propose/SKILL.md`
- Apply: read `.github/skills/openspec-apply-change/SKILL.md`
- Archive: read `.github/skills/openspec-archive-change/SKILL.md`
- Explore: read `.github/skills/openspec-explore/SKILL.md`
