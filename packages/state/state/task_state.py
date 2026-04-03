from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    blocked = "blocked"
    complete = "complete"
    failed = "failed"


# Valid transitions: from_state -> set of allowed to_states
_VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.pending: {TaskStatus.running, TaskStatus.failed},
    TaskStatus.running: {TaskStatus.blocked, TaskStatus.complete, TaskStatus.failed},
    TaskStatus.blocked: {TaskStatus.running, TaskStatus.failed},
    TaskStatus.complete: set(),  # terminal
    TaskStatus.failed: set(),  # terminal
}


class StateTransitionError(Exception):
    def __init__(self, from_status: TaskStatus, to_status: TaskStatus) -> None:
        super().__init__(f"Invalid task state transition: {from_status!r} -> {to_status!r}")
        self.from_status = from_status
        self.to_status = to_status


class TaskState(BaseModel):
    task_id: str
    status: TaskStatus = TaskStatus.pending
    current_step: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def validate_transition(self, to_status: TaskStatus) -> None:
        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if to_status not in allowed:
            raise StateTransitionError(self.status, to_status)


class TaskStatePatch(BaseModel):
    status: Optional[TaskStatus] = None
    current_step: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
