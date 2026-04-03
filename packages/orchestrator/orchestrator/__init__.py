"""orchestrator — LangGraph Turn-Time DAG.

Public surface: orchestrate(TurnRequest) -> TurnResponse.
"""
from __future__ import annotations

import logging

from .graph import orchestrate as _orchestrate
from .models import RuntimeState, TurnRequest, TurnResponse, TurnStatus

logger = logging.getLogger(__name__)


def orchestrate(turn_request: TurnRequest) -> TurnResponse:
    """Entry point: run one turn through the orchestrator DAG."""
    logger.info(
        "orchestrate.start",
        extra={"session_id": turn_request.session_id, "model": turn_request.model_id},
    )
    response = _orchestrate(turn_request)
    logger.info(
        "orchestrate.end",
        extra={
            "session_id": turn_request.session_id,
            "status": response.status.value if response else "none",
        },
    )
    return response


__all__ = [
    "orchestrate",
    "TurnRequest",
    "TurnResponse",
    "RuntimeState",
    "TurnStatus",
]
