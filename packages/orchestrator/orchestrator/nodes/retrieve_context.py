"""retrieve_context node — run hybrid retrieval for the turn query.

This node is conditional: if `state.retrieval_needed` is False, it is skipped
and `state.retrieved_chunks` remains an empty list.
"""
from __future__ import annotations

from ..models import RuntimeState


def retrieve_context(state: RuntimeState) -> RuntimeState:
    """Fetch relevant document chunks via the retrieval pipeline."""
    if not state.retrieval_needed:
        state.completed_nodes.append("retrieve_context")
        return state

    try:
        from retrieval import RetrievalService
        svc = RetrievalService()
        chunks = svc.search(query=state.turn_request.user_message, top_k=5)
        state.retrieved_chunks = [c.content for c in chunks]
    except Exception:
        # Retrieval service unavailable — continue without retrieved context.
        state.retrieved_chunks = []

    state.completed_nodes.append("retrieve_context")
    return state
