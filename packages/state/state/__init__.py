"""state — public interface for session, task, and open-files state management."""

from __future__ import annotations

from .open_files_state import OpenFileEntry, OpenFilesState
from .service import StateService
from .session_state import SessionState, SessionStatePatch
from .task_state import StateTransitionError, TaskState, TaskStatePatch, TaskStatus

__all__ = [
    "StateService",
    "SessionState",
    "SessionStatePatch",
    "TaskState",
    "TaskStatePatch",
    "TaskStatus",
    "StateTransitionError",
    "OpenFilesState",
    "OpenFileEntry",
]
