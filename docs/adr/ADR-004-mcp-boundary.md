# ADR-004: Standardized MCP (Model Context Protocol) Security Boundary

- **Status**: Accepted
- **Date**: 2026-03-24
- **Impacts**: Tool Runtime Package, Orchestrator Package, Security Policies

## 1. Context

The *Context Kernel* demands dynamic interactions with external systems (live filesystems, dynamic web searches, corporate databases, and distinct API services). 

Allowing arbitrary agent modules to invoke external APIs indiscriminately introduces catastrophic architectural risks:
- Uncontrolled, side-effect-heavy actions breaking the deterministic "Turn Execution Loop".
- Massive coupling of the core cognitive architecture to ephemeral third-party dependencies.
- Opaque transaction logs, making strict security audits and token cost tracing impossible.
- An absolute inability to build offline, isolated "Mock / Fixture" tests for the CI pipeline.

We require an impenetrable, unified perimeter isolating the core reasoning/memory engines from dangerous real-world side effects.

## 2. Decision

We formally adopt:
- An **MCP (Model Context Protocol) Gateway** as the exclusive routing abstraction layer for all External Tool invocations.
- The `packages/tool_runtime` module acting as the sole authorized gatekeeper.
- **No core cognitive module** (Memory, State, Retrieval, or Assembler) is permitted to embed third-party API clients or execute external network requests directly.

## 3. Rationale (Why)

Implementing an MCP boundary mathematically enforces our "Contract-First" and "Separation of Concerns" invariants:
- **Interchangeability**: External tools become hyper-abstracted capabilities. If a live API provider goes offline or changes, the `Context Assembler` and `Orchestrator` remain fundamentally unaware and unbroken.
- **Centralized Payload Security**: The gateway enforces strict runtime validation (`Pydantic` input schemas) and parameter sanitization before an external execution is allowed to fire.
- **Universal Traceability**: All tool outputs are natively decorated with system invariants (e.g., `latency_ms`, `tool_id`, `timestamp`), ensuring perfect consistency when feeding results back into the Context and Retrieval layers.

## 4. Consequences

### Positive
- **Strict Governance**: Absolute, single-point control over what the LLMs are physically capable of triggering externally.
- **Clean Mocking Boundaries**: Subagents (such as the `@evaluator` and `@backend-builder`) can instantly construct 100% deterministic mock objects for the MCP Gateway, enforcing the absolute testing requirements required by `test-strategy`.
- **Ecosystem Extensibility**: External engineering teams can snap in standard open-source MCP servers without modifying or risking our core kernel logic footprint.

### Negative / Risks
- **Architectural Friction**: Writing a simple, "quick-and-dirty" HTTP call is impossible; it now requires building formal MCP-compatible contracts and routing logic via the gateway.
- **Serialization Overhead**: Marshaling Pydantic data objects to JSON and routing through the gateway adds a minuscule processing tax.

## 5. Alternatives Considered

- **Arbitrary Module Integrations**: Building API clients wherever they are needed. **Cons:** Guaranteed technical debt, massive security vulnerabilities ("Tool Chaos"), and impossible-to-test asynchronous state leaks.
- **Monolithic Internal Wrapper**: A massive internal API holding every proprietary integration function. **Cons:** Violates "Granularity" rules. Monolithic wrappers become dumping grounds for mixed concerns lacking strict types.
- **No Standardized Boundary**: Treating integrations as basic imported functions. **Cons:** Reduces the platform into a brittle, use-case-specific application rather than a flexible, reusable generic Cognitive Engine.

## 6. Execution Boundaries & System Anti-Patterns

1. **Orchestrator Sole Authority**: Only the `orchestrator` package (specifically its designated route execution nodes) can trigger a tool. 
2. **Assemblers Are Blind**: The `context_assembler` NEVER executes a tool; its sole scope is formatting the *results* of previously run tools.
3. **Memory Is Isolated**: The `memory` layer NEVER reaches out to external APIs to verify or correlate facts; it merely persists structured final results.
4. **Mandatory Explicit Contracts**: Every tool module traversing the gateway must expose explicit, strict `Pydantic` schemas defining both its Input arguments and Returns.

## 7. Follow-up Actions
- Expose the explicit boundaries of the `packages/tool_runtime/mcp_gateway.py` registry.
- Establish the official mock and fixture testing baseline for creating fake MCP endpoints during tests.
- Formulate the security/tracing decorators to universally timestamp and log tool executions.
