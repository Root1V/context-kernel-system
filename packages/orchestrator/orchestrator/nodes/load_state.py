"""load_state node — fetch RuntimeState from StateService."""

from __future__ import annotations

from ..models import RuntimeState


def load_state(state: RuntimeState) -> RuntimeState:
    """Load session and task state from the state service."""
    try:
        from state import StateService

        svc = StateService()
        session = svc.get_session_state(state.turn_request.session_id)  # type: ignore[arg-type]
        if session is not None:
            state.session_state = session.model_dump()
    except Exception:
        # State service unavailable — continue with empty state.
        pass
    state.completed_nodes.append("load_state")
    return state
