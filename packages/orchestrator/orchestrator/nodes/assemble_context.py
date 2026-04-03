"""assemble_context node — call ContextAssembler to produce prompt payload."""

from __future__ import annotations

from ..models import RuntimeState


def assemble_context(state: RuntimeState) -> RuntimeState:
    """Assemble the token-budget-constrained prompt from all gathered inputs."""
    try:
        from context_assembler import AssemblyInput, assemble

        snapshot = state.memory_snapshot
        inp = AssemblyInput(
            model_id=state.turn_request.model_id,
            core_memory_blocks=snapshot.get("core_memory", []),
            state_summary=_build_state_summary(state),
            message_buffer=snapshot.get("message_buffer", []),
            retrieved_chunks=state.retrieved_chunks,
        )
        ctx = assemble(inp)
        # Convert assembled sections to the messages format expected by model adapter.
        state.assembled_messages = [
            {"role": "system", "content": ctx.render()},
            {"role": "user", "content": state.turn_request.user_message},
        ]
    except Exception:
        # Assembler unavailable — fall back to bare message.
        state.assembled_messages = [
            {"role": "user", "content": state.turn_request.user_message},
        ]

    state.completed_nodes.append("assemble_context")
    return state


def _build_state_summary(state: RuntimeState) -> str:
    parts = []
    if state.session_state:
        sid = state.session_state.get("session_id", "")
        if sid:
            parts.append(f"session_id: {sid}")
    return "; ".join(parts)
