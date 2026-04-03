"""infer node — call model_adapter.complete() with assembled context."""

from __future__ import annotations

from ..models import RuntimeState

try:
    from model_adapter import complete
except ImportError:
    complete = None  # type: ignore[assignment]


def infer(state: RuntimeState) -> RuntimeState:
    """Send assembled messages to the LLM and store the response."""
    try:
        if complete is None:
            raise ImportError("model_adapter not installed")
        response = complete(
            model_id=state.turn_request.model_id,
            messages=state.assembled_messages,
        )
        state.last_model_response = response.model_dump()
    except Exception as exc:
        state.last_model_response = {
            "content": f"[inference error: {exc}]",
            "tool_calls": [],
            "finish_reason": "error",
        }

    state.completed_nodes.append("infer")
    return state
