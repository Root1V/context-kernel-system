# ADR-003: LangGraph as Orchestration Layer for Turn Execution

- **Status**: Accepted
- **Date**: 2026-03-24
- **Impacts**: Orchestrator Package, Context Pipeline, Runtime Flows

## 1. Context

The *Context Kernel* operates fundamentally beyond a traditional request/response web architecture. It demands an orchestration mechanism capable of mathematically mapping a strict DAG (Directed Acyclic Graph) workflow per user turn. 

The core Turn Execution Loop MUST distinctly separate the following isolated lifecycles without obfuscating them via implicit "helpers":
1. State Hydration (`load_state`)
2. Knowledge Fetching (`retrieve_context`)
3. Prompt Bundling (`assemble_context`)
4. Inference Invocation (`call_model`)
5. Memory Commitment (`persist_outcome`)
6. Conditional Edge Routing

Furthermore, the solution must strictly support the "Explicit State" invariant, enabling human developers and AI subagents to effortlessly trace, test, and adapt the cognitive topology.

## 2. Decision

We formally adopt:
- **LangGraph** as the singular orchestration layer governing the synchronous Turn Execution Loop and deterministic agentic routing.

## 3. Rationale (Why)

LangGraph aligns faultlessly with our *Context Kernel* core architectural invariants:
- **Native DAG Topologies**: It enforces the strict algorithmic flows we identified in the `repo-intake` and `orchestrator` Agent protocols, locking logic within highly cohesive `Nodes`.
- **Explicit State Injection**: Standardizes the transport layer (e.g., `StateGraph` using Pydantic schemas) moving between nodes, cementing the "Explicit State" model required by ADR-002 and `AGENTS.md`. 
- **Evolvability**: Guarantees simple scalability from a basic sequential RAG pipeline into complex multi-agent hierarchical deployments without requiring a foundational rewrite.
- **Traceability**: Out-of-the-box integration with tracing mechanisms for granular step debugging.

## 4. Consequences

### Positive
- **API Boundary Protection**: Execution topology is entirely decoupled from the FastAPI (`apps/api/`) HTTP endpoints.
- **High Testability**: Functional node design ensures each discrete step (like `assemble_context`) can be unit tested in pure isolation without firing full executions.
- **Readability**: Code agents (like `@backend-builder`) excel at parsing and mutating isolated LangGraph node functions since they map perfectly to pure Python functions and boundaries.

### Negative / Risks
- **Over-Engineering Vector**: Requires strict architectural discipline to prevent the graph from becoming an untraceable "spaghetti" web of conditional edge exceptions.
- **Initial Abstraction Tax**: Introduces a steeper learning curve (and slight latency overhead) compared to simple linear function calls. 

## 5. Alternatives Considered

- **Hand-Rolled Orchestrator**: Complete baseline control. **Cons:** Prohibitive boilerplate, forces us to reinvent state checkpointing and cyclic graph error-handling, diverging focus away from core cognitive behaviors.
- **Linear Service Layer (No Graph)**: Simplest day-1 start. **Cons:** Fails to support cyclic subagent loops (e.g., self-correction loops upon constraint failure), guaranteeing severe technical debt as retrieval complexity grows.
- **Full Distributed Workflow Engine (e.g., Temporal)**: Infinite scalability and durability. **Cons:** Catastrophic cognitive overload and latency penalty for extremely fast, synchronous, turn-by-turn LLM loop executions.

## 6. Decision Boundary & Scope

LangGraph is **EXCLUSIVELY** authorized for:
- Synchronous Turn execution (The primary cognitive loop).
- Deterministic routing boundaries between execution nodes.
- Short-term conversational multi-agent graphs.

LangGraph is **NOT AUTHORIZED** for:
- Long-running, durable, asynchronous offline tasks.
- Background systems like the `@sleep-time-worker`, bulk database aggregations, or Memory Compaction jobs. These processes must leverage traditional cron/schedulers or specialized durable workers outside of the LangGraph runtime.

## 7. Follow-up Actions
- Define the absolute Minimum Viable Graph Nodes (e.g., State, Retrieve, Call).
- Formulate strict Pydantic typing for the root `AgentState` payload traversing the graph.
- Configure automatic retry policies and boundary constraints within the `packages/orchestrator` module.
