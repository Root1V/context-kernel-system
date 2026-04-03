"""POST /chat route — validate payload, call orchestrate(), return ChatResponse.

This route MUST NOT contain context-assembly, memory, or retrieval logic.
All processing is delegated to the orchestrator.
"""

from __future__ import annotations

import os
import sys

from fastapi import APIRouter, HTTPException, Request

from ..config import settings
from ..limiter import limiter
from ..schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

# Make packages importable when running inside apps/api/.
# Each package lives in its own subdirectory (packages/<name>/<name>/)
# so we add every packages/*/ subdir to sys.path.
_PACKAGES_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages")
)
for _pkg_dir in sorted(os.listdir(_PACKAGES_ROOT)):
    _pkg_path = os.path.join(_PACKAGES_ROOT, _pkg_dir)
    if os.path.isdir(_pkg_path) and _pkg_path not in sys.path:
        sys.path.insert(0, _pkg_path)


@router.post("/chat", response_model=ChatResponse, status_code=200)
@limiter.limit(settings.CHAT_RATE_LIMIT)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """Receive a chat message, run a full Turn-Time DAG, return the response."""
    try:
        from orchestrator import TurnRequest, orchestrate
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Orchestrator not available: {exc}") from exc

    turn_req = TurnRequest(
        session_id=body.session_id,
        user_message=body.message,
        model_id=body.model_id,
        max_tool_iterations=body.max_tool_iterations,
        retrieval_needed=body.retrieval_needed,
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
