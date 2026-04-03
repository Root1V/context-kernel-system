"""Session management routes — POST /sessions and GET /sessions/{session_id}."""
from __future__ import annotations

import sys
import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..schemas.session import SessionCreateRequest, SessionResponse

router = APIRouter()

_PACKAGES = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages")
if _PACKAGES not in sys.path:
    sys.path.insert(0, _PACKAGES)


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(request: SessionCreateRequest) -> SessionResponse:
    """Create a new session and initialize its state."""
    session_id = str(uuid.uuid4())
    try:
        from state import StateService
        from state.session_state import SessionState
        svc = StateService()
        svc.update_session_state(
            session_id,
            SessionState(session_id=session_id, user_id=request.user_id),
        )
    except Exception:
        # State service unavailable — still return session_id.
        pass
    return SessionResponse(
        session_id=session_id,
        user_id=request.user_id,
        is_active=True,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """Retrieve an existing session or return 404."""
    try:
        from state import StateService
        svc = StateService()
        state = svc.get_session_state(session_id)
    except Exception:
        state = None

    if state is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return SessionResponse(
        session_id=state.session_id,
        user_id=getattr(state, "user_id", None),
        is_active=True,
    )
