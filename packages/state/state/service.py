"""StateService — the single source of truth for all session/task/file state.

For now this uses an in-process dict store. The storage layer integration
(DB persistence) is wired in task 2.2 once the storage layer is implemented
(Group 3). The interface contract is stable and unchanged by that swap.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from .open_files_state import OpenFileEntry, OpenFilesState
from .session_state import SessionState, SessionStatePatch
from .task_state import StateTransitionError, TaskState, TaskStatePatch, TaskStatus


class StateService:
    """Manages session, task, and open-files state.

    Storage backend is injected via *storage_backend*. If None, an in-memory
    dict is used (suitable for tests and local development).
    """

    def __init__(self, storage_backend=None) -> None:
        self._storage = storage_backend
        # In-memory fallback stores
        self._sessions: dict[str, SessionState] = {}
        self._tasks: dict[str, TaskState] = {}
        self._open_files: dict[str, OpenFilesState] = {}

    # ------------------------------------------------------------------
    # Session state
    # ------------------------------------------------------------------

    def get_session_state(self, session_id: UUID) -> SessionState:
        key = str(session_id)
        if key not in self._sessions:
            # Auto-initialise on first access
            self._sessions[key] = SessionState(session_id=session_id)
        return self._sessions[key]

    def update_session_state(
        self, session_id: UUID, patch: SessionStatePatch
    ) -> SessionState:
        state = self.get_session_state(session_id)
        update_data = patch.model_dump(exclude_none=True)
        update_data["updated_at"] = datetime.utcnow()
        updated = state.model_copy(update=update_data)
        self._sessions[str(session_id)] = updated
        return updated

    # ------------------------------------------------------------------
    # Task state
    # ------------------------------------------------------------------

    def get_task_state(self, task_id: str) -> TaskState:
        if task_id not in self._tasks:
            self._tasks[task_id] = TaskState(task_id=task_id)
        return self._tasks[task_id]

    def update_task_state(self, task_id: str, patch: TaskStatePatch) -> TaskState:
        state = self.get_task_state(task_id)
        if patch.status is not None:
            state.validate_transition(patch.status)
        update_data = patch.model_dump(exclude_none=True)
        update_data["updated_at"] = datetime.utcnow()
        updated = state.model_copy(update=update_data)
        self._tasks[task_id] = updated
        return updated

    # ------------------------------------------------------------------
    # Open files state
    # ------------------------------------------------------------------

    def get_open_files(self, session_id: UUID) -> OpenFilesState:
        key = str(session_id)
        if key not in self._open_files:
            self._open_files[key] = OpenFilesState(session_id=session_id)
        return self._open_files[key]

    def add_open_file(
        self, session_id: UUID, file_path: str, summary: str
    ) -> OpenFilesState:
        state = self.get_open_files(session_id)
        # Replace if path already tracked
        files = [f for f in state.files if f.file_path != file_path]
        files.append(OpenFileEntry(file_path=file_path, summary=summary))
        updated = state.model_copy(update={"files": files})
        self._open_files[str(session_id)] = updated
        return updated

    def remove_open_file(self, session_id: UUID, file_path: str) -> OpenFilesState:
        state = self.get_open_files(session_id)
        files = [f for f in state.files if f.file_path != file_path]
        updated = state.model_copy(update={"files": files})
        self._open_files[str(session_id)] = updated
        return updated
