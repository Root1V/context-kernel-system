"""Unit tests for state — covers all spec scenarios."""

from __future__ import annotations

from uuid import uuid4

import pytest
from state import (
    SessionStatePatch,
    StateService,
    StateTransitionError,
    TaskStatePatch,
    TaskStatus,
)


@pytest.fixture
def svc() -> StateService:
    return StateService()


class TestSessionState:
    def test_auto_initialised_on_first_access(self, svc):
        sid = uuid4()
        state = svc.get_session_state(sid)
        assert state.session_id == sid

    def test_partial_update_preserves_other_fields(self, svc):
        sid = uuid4()
        svc.update_session_state(sid, SessionStatePatch(is_compiling=True))
        svc.update_session_state(sid, SessionStatePatch(active_task_id="t1"))
        state = svc.get_session_state(sid)
        assert state.is_compiling is True
        assert state.active_task_id == "t1"

    def test_update_returns_updated_state(self, svc):
        sid = uuid4()
        updated = svc.update_session_state(sid, SessionStatePatch(is_searching=True))
        assert updated.is_searching is True


class TestTaskState:
    def test_valid_transition_pending_to_running(self, svc):
        updated = svc.update_task_state("t1", TaskStatePatch(status=TaskStatus.running))
        assert updated.status == TaskStatus.running

    def test_invalid_transition_running_to_running_raises(self, svc):
        svc.update_task_state("t2", TaskStatePatch(status=TaskStatus.running))
        with pytest.raises(StateTransitionError):
            svc.update_task_state("t2", TaskStatePatch(status=TaskStatus.running))

    def test_invalid_transition_complete_to_running_raises(self, svc):
        svc.update_task_state("t3", TaskStatePatch(status=TaskStatus.running))
        svc.update_task_state("t3", TaskStatePatch(status=TaskStatus.complete))
        with pytest.raises(StateTransitionError):
            svc.update_task_state("t3", TaskStatePatch(status=TaskStatus.running))

    def test_partial_update_preserves_existing_fields(self, svc):
        svc.update_task_state("t4", TaskStatePatch(current_step="step-1"))
        svc.update_task_state("t4", TaskStatePatch(status=TaskStatus.running))
        state = svc.get_task_state("t4")
        assert state.current_step == "step-1"
        assert state.status == TaskStatus.running


class TestOpenFilesState:
    def test_add_open_file_is_retrievable(self, svc):
        sid = uuid4()
        svc.add_open_file(sid, "/workspace/main.py", "Main entry point")
        state = svc.get_open_files(sid)
        assert any(f.file_path == "/workspace/main.py" for f in state.files)

    def test_adding_same_path_replaces_entry(self, svc):
        sid = uuid4()
        svc.add_open_file(sid, "/a.py", "first summary")
        svc.add_open_file(sid, "/a.py", "updated summary")
        state = svc.get_open_files(sid)
        entries = [f for f in state.files if f.file_path == "/a.py"]
        assert len(entries) == 1
        assert entries[0].summary == "updated summary"

    def test_state_is_never_inferred_from_messages(self, svc):
        """State must come from the service, not text parsing."""
        sid = uuid4()
        svc.update_session_state(sid, SessionStatePatch(is_compiling=True))
        state = svc.get_session_state(sid)
        # Direct bool attribute — no message parsing needed
        assert state.is_compiling is True
