"""Orchestrator DAG — LangGraph StateGraph wiring.

The DAG implements the Turn-Time pipeline:
  receive_request → load_state → hydrate_memory → [retrieve_context] →
  assemble_context → infer → [tool_loop] → persist_state

Conditional edges:
  - retrieve_context: skipped when RuntimeState.retrieval_needed is False.
  - tool_loop: runs only when the model response contains tool calls.

Public API:
  orchestrate(turn_request: TurnRequest) -> TurnResponse
"""
from __future__ import annotations

import sys
import os
import logging

from .models import RuntimeState, TurnRequest, TurnResponse
from .nodes import (
    assemble_context,
    hydrate_memory,
    infer,
    load_state,
    persist_state,
    receive_request,
    retrieve_context,
    run_tool_loop,
)
from .nodes.tool_loop import tool_loop

logger = logging.getLogger(__name__)

# Observability — optional; falls back to no-op if package not on sys.path
_PACKAGES = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _PACKAGES not in sys.path:
    sys.path.insert(0, _PACKAGES)

try:
    from observability import trace_node as _trace_node
except ImportError:  # pragma: no cover
    from contextlib import contextmanager

    @contextmanager  # type: ignore[misc]
    def _trace_node(name, session_id=None, **kw):  # type: ignore[misc]
        yield None


# ---------------------------------------------------------------------------
# Conditional routing helpers
# ---------------------------------------------------------------------------

def _should_retrieve(state: RuntimeState) -> str:
    return "retrieve_context" if state.retrieval_needed else "assemble_context"


def _should_tool_loop(state: RuntimeState) -> str:
    tool_calls = state.last_model_response.get("tool_calls", [])
    req = state.turn_request
    if tool_calls and state.tool_iterations < req.max_tool_iterations:
        return "tool_loop"
    return "persist_state"


# ---------------------------------------------------------------------------
# Graph construction (lazy import of langgraph so tests can patch it)
# ---------------------------------------------------------------------------

def _build_graph():
    """Build and compile the LangGraph StateGraph."""
    from langgraph.graph import StateGraph, END

    builder = StateGraph(RuntimeState)

    # Add nodes
    builder.add_node("receive_request", receive_request)
    builder.add_node("load_state", load_state)
    builder.add_node("hydrate_memory", hydrate_memory)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("assemble_context", assemble_context)
    builder.add_node("infer", infer)
    builder.add_node("tool_loop", run_tool_loop)
    builder.add_node("persist_state", persist_state)

    # Linear edges
    builder.set_entry_point("receive_request")
    builder.add_edge("receive_request", "load_state")
    builder.add_edge("load_state", "hydrate_memory")

    # Conditional: retrieve or skip
    builder.add_conditional_edges(
        "hydrate_memory",
        _should_retrieve,
        {"retrieve_context": "retrieve_context", "assemble_context": "assemble_context"},
    )

    builder.add_edge("retrieve_context", "assemble_context")
    builder.add_edge("assemble_context", "infer")

    # Conditional: tool loop or persist
    builder.add_conditional_edges(
        "infer",
        _should_tool_loop,
        {"tool_loop": "tool_loop", "persist_state": "persist_state"},
    )

    # tool_loop may need to re-evaluate after executing tools
    builder.add_conditional_edges(
        "tool_loop",
        _should_tool_loop,
        {"tool_loop": "tool_loop", "persist_state": "persist_state"},
    )

    builder.add_edge("persist_state", END)

    return builder.compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def orchestrate(turn_request: TurnRequest) -> TurnResponse:
    """Run a full Turn-Time DAG pass and return the TurnResponse.

    This is the single public function the API layer calls. All internal DAG
    steps are hidden behind this contract.
    """
    initial_state = RuntimeState(
        turn_request=turn_request,
        retrieval_needed=turn_request.retrieval_needed,
    )

    try:
        graph = _build_graph()
        final_state: RuntimeState = graph.invoke(initial_state)
    except ImportError:
        # LangGraph not installed — run nodes sequentially as a fallback.
        final_state = _run_sequential(initial_state)

    if final_state.final_response is None:
        # Should not happen but guard defensively.
        final_state = persist_state(final_state)

    return final_state.final_response  # type: ignore[return-value]


def _run_sequential(state: RuntimeState) -> RuntimeState:
    """Fallback: run nodes sequentially when LangGraph is not installed."""
    req = state.turn_request
    sid = req.session_id

    with _trace_node("receive_request", session_id=sid):
        state = receive_request(state)
    with _trace_node("load_state", session_id=sid):
        state = load_state(state)
    with _trace_node("hydrate_memory", session_id=sid):
        state = hydrate_memory(state)
    if state.retrieval_needed:
        with _trace_node("retrieve_context", session_id=sid):
            state = retrieve_context(state)
    with _trace_node("assemble_context", session_id=sid):
        state = assemble_context(state)
    with _trace_node("infer", session_id=sid):
        state = infer(state)
    # Simple tool loop without graph routing
    iterations = 0
    while (
        state.last_model_response.get("tool_calls")
        and iterations < req.max_tool_iterations
    ):
        with _trace_node("tool_loop", session_id=sid, iteration=iterations):
            state = tool_loop(state)
        iterations += 1
        if not state.last_model_response.get("tool_calls"):
            break
    with _trace_node("persist_state", session_id=sid):
        state = persist_state(state)
    return state
