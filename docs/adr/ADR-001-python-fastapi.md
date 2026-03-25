# ADR-001: Python + FastAPI as Primary Backend Stack

- **Status**: Accepted
- **Date**: 2026-03-24
- **Impacts**: Backend Apps, Runtime Packages, Background Workers

## 1. Context

The *Context Kernel* system requires a backend topology that strictly supports:
- Rapid iteration with explicit "Contract-First" designs.
- Seamless integration with the AI/LLM ecosystem.
- Stringent data validation across module boundaries.
- Extreme modularity (handling layered memory, tools, and retrievals).
- High legibility and parseability for autonomous Subagents (LLMs).

Given the prioritization of complex orchestrations, hybrid retrievals, and layered memory over raw CPU throughput, the technological ergonomics and agent-readability of the ecosystem are paramount.

## 2. Decision

We formally adopt:
- **Python 3.12+** as the central backend programming language.
- **FastAPI** as the primary HTTP framework and API routing layer.
- **Pydantic (v2)** as the mandatory engine for explicit data contracts and state validation.
- **uv** as the primary package and virtual environment manager.
- **ruff / mypy / pytest** as the non-negotiable QA and testing toolchain.

## 3. Rationale (Why)

### Python
Python is mathematically the most aligned ecosystem for Agentic systems because:
- It possesses the most mature tooling for LLMs, Retrieval, and Orchestration libraries.
- Python's syntax is natively optimized within the training data of almost all foundational LLMs, ensuring that subagents (like `@backend-builder`) generate significantly fewer hallucinations and syntax errors.

### FastAPI
FastAPI supports our *Context Kernel* boundaries by providing:
- First-class support for Python type-hinting, directly translating to clean agentic code.
- Simple Dependency Injection (DI) to maintain the requested "Separation of Concerns".
- Minimal rigid boilerplate, allowing granular, decoupled module architectures.

### Pydantic
Pydantic fulfills our global "Contract-First Design" and "Explicit State" invariants:
- It enforces strict boundaries between modules; data entering the Context Assembler from the Memory module MUST pass a Pydantic validation schema.
- It translates deterministically to JSON Schemas, which are heavily used by the `@sleep-time-worker` and other offline agents for explicit state persistence.

## 4. Consequences

### Positive
- **High-Signal Onboarding**: Subagents (`@planner`, `@evaluator`) will naturally understand Python 3.12 syntax and FastAPI routes.
- **Cohesive Tooling**: `uv` + `ruff` + `mypy` creates a deterministic, fast internal QA pipeline for the `@evaluator`.
- **Ecosystem Sync**: Out-of-the-box integration with standard Python AI libraries (LangGraph, pgvector adapters, etc.).

### Negative / Risks
- **CPU Bottlenecks**: Python is not optimized for extreme concurrent CPU-bound computations natively. If a pure-compute bottleneck arises, specific workers might need extraction in the future.
- **Script-Like Degradation**: Python's flexibility requires strict architectural discipline. Without enforcement by the `@orchestrator`, builders might write "script-like" monolithic code (violating our Granularity rules).
- **Schema Duplication**: Potential risk of duplicating Pydantic API schemas with database ORM models if not carefully abstracted.

## 5. Alternatives Considered

- **TypeScript / Node.js**: Excellent web/full-stack DX, but suboptimal for advanced semantic retrieval and orchestration library support compared to Python.
- **Go / Golang**: Superior concurrency and strict type safety, but the LLM ecosystem is less mature. The cognitive overhead for rapid agent-driven refactoring is too high for this phase.
- **Rust**: Unmatched memory safety and performance, but the iteration speed and implementation cost are disproportionate to our current goal of exploring cognitive architectures.

## 6. Follow-up Actions
- Define the standardized Python project structure per modular package.
- Formulate the "Golden Test" and `@evaluator` fixtures strategy.
- Establish the configuration management standard (e.g., `pydantic-settings`).
