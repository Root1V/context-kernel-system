"""hydrate_memory node — produce MemorySnapshot from MemoryService."""
from __future__ import annotations

from ..models import RuntimeState


def hydrate_memory(state: RuntimeState) -> RuntimeState:
    """Load all memory layers and populate state.memory_snapshot."""
    try:
        from memory import MemoryService
        svc = MemoryService()
        snapshot = svc.snapshot(session_id=state.turn_request.session_id)
        state.memory_snapshot = {
            "core_memory": [b.content for b in snapshot.core_memory],
            "message_buffer": [
                f"{t.role}: {t.content}" for t in snapshot.message_buffer
            ],
            "recent_recall": [e.content for e in snapshot.recent_recall],
        }
    except Exception:
        # Memory service unavailable — continue with empty snapshot.
        state.memory_snapshot = {"core_memory": [], "message_buffer": [], "recent_recall": []}

    state.completed_nodes.append("hydrate_memory")
    return state
