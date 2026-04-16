"""retrieve_context node — run hybrid retrieval for the turn query.

This node is conditional: if `state.retrieval_needed` is False, it is skipped
and `state.retrieved_chunks` remains an empty list.
"""

from __future__ import annotations

from ..models import RuntimeState


async def retrieve_context(state: RuntimeState) -> RuntimeState:
    """Fetch relevant document chunks via the retrieval pipeline."""
    if not state.retrieval_needed:
        state.completed_nodes.append("retrieve_context")
        return state

    try:
        from retrieval import RetrievalService

        session_factory = getattr(state, "session_factory", None)
        svc = RetrievalService(session_factory=session_factory)

        if session_factory is not None:
            session_id = str(state.turn_request.session_id)
            chunks = await svc.async_search(session_id, state.turn_request.user_message, top_k=5)
        else:
            chunks = svc.search(query=state.turn_request.user_message, top_k=5)

        state.retrieved_chunks = [c.content for c in chunks]
    except Exception:
        # Retrieval service unavailable — continue without retrieved context.
        state.retrieved_chunks = []

    state.completed_nodes.append("retrieve_context")
    return state
