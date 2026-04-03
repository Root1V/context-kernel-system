"""Orchestrator runtime models.

TurnRequest, TurnResponse, and RuntimeState are the data contracts for the
Turn-Time DAG. All nodes read from and write to RuntimeState.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TurnStatus(str, Enum):
    ok = "ok"
    tool_limit_reached = "tool_limit_reached"
    error = "error"


class TurnRequest(BaseModel):
    """Normalized input for a single turn."""

    session_id: str
    user_message: str
    model_id: str = "gpt-4o"
    max_tool_iterations: int = 5
    retrieval_needed: bool = True
    # Optional: client-supplied turn id (for idempotent replay)
    turn_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class TurnResponse(BaseModel):
    """Output of a completed (or partially completed) turn."""

    session_id: str
    turn_id: str
    assistant_message: str
    status: TurnStatus = TurnStatus.ok
    tool_calls_made: int = 0
    state_persisted: bool = False


class RuntimeState(BaseModel):
    """Mutable state carried through all DAG nodes for one turn.

    Each node reads the fields it needs and writes back its outputs.
    The orchestrator checkpoints this object to storage after each node.
    """

    # --- Input ---
    turn_request: TurnRequest

    # --- Node outputs (populated progressively) ---
    session_state: dict[str, Any] = Field(default_factory=dict)
    task_state: dict[str, Any] = Field(default_factory=dict)
    memory_snapshot: dict[str, Any] = Field(default_factory=dict)
    retrieved_chunks: list[str] = Field(default_factory=list)
    assembled_messages: list[dict[str, str]] = Field(default_factory=list)
    last_model_response: dict[str, Any] = Field(default_factory=dict)
    tool_results_log: list[dict[str, Any]] = Field(default_factory=list)

    # --- Control ---
    retrieval_needed: bool = True
    tool_iterations: int = 0
    completed_nodes: list[str] = Field(default_factory=list)

    # --- Output ---
    final_response: Optional[TurnResponse] = None
