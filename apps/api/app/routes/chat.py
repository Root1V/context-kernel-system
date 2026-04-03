"""POST /chat route — validate payload, call orchestrate(), return ChatResponse.

This route MUST NOT contain context-assembly, memory, or retrieval logic.
All processing is delegated to the orchestrator.
"""
from __future__ import annotations

import sys
import os

from fastapi import APIRouter, HTTPException

from ..schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

# Make packages importable when running inside apps/api/
_PACKAGES = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages")
if _PACKAGES not in sys.path:
    sys.path.insert(0, _PACKAGES)
_ORCHESTRATOR = os.path.join(_PACKAGES, "orchestrator")
if _ORCHESTRATOR not in sys.path:
    sys.path.insert(0, _ORCHESTRATOR)


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat(request: ChatRequest) -> ChatResponse:
    """Receive a chat message, run a full Turn-Time DAG, return the response."""
    try:
        from orchestrator import TurnRequest, orchestrate
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Orchestrator not available: {exc}")

    turn_req = TurnRequest(
        session_id=request.session_id,
        user_message=request.message,
        model_id=request.model_id,
        max_tool_iterations=request.max_tool_iterations,
        retrieval_needed=request.retrieval_needed,
    )
    turn_resp = orchestrate(turn_req)
    return ChatResponse(
        session_id=turn_resp.session_id,
        turn_id=turn_resp.turn_id,
        assistant_message=turn_resp.assistant_message,
        status=turn_resp.status.value,
        tool_calls_made=turn_resp.tool_calls_made,
        state_persisted=turn_resp.state_persisted,
    )
