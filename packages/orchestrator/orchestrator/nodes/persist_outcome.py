"""persist_state node — checkpoint RuntimeState and dispatch background jobs."""

from __future__ import annotations

from ..models import RuntimeState, TurnResponse, TurnStatus


def persist_state(state: RuntimeState) -> RuntimeState:
    """Write session state checkpoint; build the final TurnResponse."""
    persisted = False
    try:
        from state import StateService

        svc = StateService()
        # Snapshot current session state back to storage.
        if state.session_state:
            from state import SessionStatePatch

            patch = SessionStatePatch(
                **{
                    k: v
                    for k, v in state.session_state.items()
                    if k in SessionStatePatch.model_fields
                }
            )
            svc.update_session_state(state.turn_request.session_id, patch)  # type: ignore[arg-type]
        persisted = True
    except Exception:
        pass

    content = state.last_model_response.get("content", "")
    tool_iterations = state.tool_iterations
    req = state.turn_request

    status: TurnStatus
    if tool_iterations >= req.max_tool_iterations and state.last_model_response.get("tool_calls"):
        status = TurnStatus.tool_limit_reached
    else:
        status = TurnStatus.ok

    state.final_response = TurnResponse(
        session_id=req.session_id,
        turn_id=req.turn_id,
        assistant_message=content,
        status=status,
        tool_calls_made=tool_iterations,
        state_persisted=persisted,
    )
    state.completed_nodes.append("persist_state")
    return state
