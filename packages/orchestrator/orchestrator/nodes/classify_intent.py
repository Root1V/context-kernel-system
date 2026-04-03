"""receive_request node — normalize raw input into a TurnRequest.

This node is the first step of the DAG. It validates the incoming data and
prepares the initial RuntimeState for downstream nodes.
"""
from __future__ import annotations

from ..models import RuntimeState, TurnRequest


def receive_request(state: RuntimeState) -> RuntimeState:
    """Normalize and validate the turn request; set retrieval_needed flag."""
    req = state.turn_request
    # Propagate retrieval flag from request into runtime state.
    state.retrieval_needed = req.retrieval_needed
    state.completed_nodes.append("receive_request")
    return state
