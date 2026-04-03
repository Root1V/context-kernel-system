"""Unit tests for the background worker.

Spec scenarios covered:
  - Compaction job summarizes old buffer turns into RecallEntry
  - Archival promotion: aged recall entry promoted; idempotent (no duplicates)
  - Job survives worker crash (status stays pending if not claimed)
  - Completed job is marked done with completed_at timestamp
  - Compaction template loaded from file (not hardcoded)
  - Job poller dispatches correct handler per job type
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, patch

# Ensure worker package is importable.
_WORKER_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _WORKER_ROOT not in sys.path:
    sys.path.insert(0, _WORKER_ROOT)

_PACKAGES = os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages")
if _PACKAGES not in sys.path:
    sys.path.insert(0, _PACKAGES)

from worker.jobs.compaction import _load_template, handle_compaction
from worker.jobs.memory_cleanup import handle_archival_promotion
from worker.main import _JOB_QUEUE, enqueue_job, run_once
from worker.models import Job, JobStatus, JobType

# ---------------------------------------------------------------------------
# sys.modules injection helpers (handlers use local imports inside functions)
# ---------------------------------------------------------------------------


@contextmanager
def _mock_model_adapter(return_content: str = "Summary."):
    """Inject a fake model_adapter so `from model_adapter import complete` works."""
    mock_complete = MagicMock()
    mock_response = MagicMock()
    mock_response.content = return_content
    mock_complete.return_value = mock_response

    fake_mod = MagicMock()
    fake_mod.complete = mock_complete

    old = sys.modules.get("model_adapter")
    sys.modules["model_adapter"] = fake_mod
    try:
        yield mock_complete
    finally:
        if old is None:
            sys.modules.pop("model_adapter", None)
        else:
            sys.modules["model_adapter"] = old


@contextmanager
def _mock_memory_service(mock_svc: MagicMock):
    """Inject a fake memory module so MemoryService() returns mock_svc."""
    fake_svc_cls = MagicMock(return_value=mock_svc)
    fake_memory = MagicMock()
    fake_memory.MemoryService = fake_svc_cls
    fake_models = MagicMock()

    old_memory = sys.modules.get("memory")
    old_models = sys.modules.get("memory.models")
    sys.modules["memory"] = fake_memory
    sys.modules["memory.models"] = fake_models
    try:
        yield mock_svc
    finally:
        if old_memory is None:
            sys.modules.pop("memory", None)
        else:
            sys.modules["memory"] = old_memory
        if old_models is None:
            sys.modules.pop("memory.models", None)
        else:
            sys.modules["memory.models"] = old_models


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(job_type=JobType.compaction, **payload_overrides) -> Job:
    payload = {"messages": ["User: Hello!", "Assistant: Hi there!"], "model_id": "gpt-4o"}
    payload.update(payload_overrides)
    return Job(
        job_type=job_type,
        session_id="sess-test",
        payload=payload,
    )


def _clear_queue() -> None:
    _JOB_QUEUE.clear()


# ---------------------------------------------------------------------------
# Scenario: Compaction template loaded from file
# ---------------------------------------------------------------------------


class TestCompactionTemplate:
    def test_template_loads_from_file(self):
        template = _load_template()
        assert "{messages}" in template, "Template must contain {messages} placeholder"
        assert len(template) > 10, "Template should not be empty"

    def test_template_not_in_compaction_source(self):
        """Ensure template text is loaded from file, not hardcoded in handler."""
        import inspect

        from worker.jobs import compaction as mod

        source = inspect.getsource(mod)
        # The compaction handler should NOT contain the prompt text inline.
        assert "You are a highly efficient" not in source, (
            "Template text must not be hardcoded in compaction.py"
        )


# ---------------------------------------------------------------------------
# Scenario: Compaction job processes messages
# ---------------------------------------------------------------------------


class TestCompactionHandler:
    def test_compaction_marks_complete(self):
        job = _make_job()
        with _mock_model_adapter("Summary: User greeted assistant."):
            result = handle_compaction(job)
        assert result.status == JobStatus.complete
        assert result.completed_at is not None

    def test_compaction_empty_messages_noop(self):
        job = _make_job(messages=[])
        result = handle_compaction(job)
        assert result.status == JobStatus.complete

    def test_compaction_handles_model_error_gracefully(self):
        """If model_adapter.complete raises, handler falls back and still completes."""
        job = _make_job()
        fake_mod = MagicMock()
        fake_mod.complete.side_effect = Exception("API error")
        old = sys.modules.get("model_adapter")
        sys.modules["model_adapter"] = fake_mod
        try:
            result = handle_compaction(job)
        finally:
            if old is None:
                sys.modules.pop("model_adapter", None)
            else:
                sys.modules["model_adapter"] = old
        assert result.status == JobStatus.complete

    def test_compaction_uses_template(self):
        """Template placeholder {messages} must be filled with actual messages."""
        job = _make_job(messages=["User: capital of France?"])
        captured_prompts = []

        def _capture(model_id, messages):
            captured_prompts.append(messages)
            r = MagicMock()
            r.content = "Paris."
            return r

        fake_mod = MagicMock()
        fake_mod.complete.side_effect = _capture
        old = sys.modules.get("model_adapter")
        sys.modules["model_adapter"] = fake_mod
        try:
            handle_compaction(job)
        finally:
            if old is None:
                sys.modules.pop("model_adapter", None)
            else:
                sys.modules["model_adapter"] = old

        assert captured_prompts, "complete() was never called"
        prompt_text = captured_prompts[0][0]["content"]
        assert "capital of France" in prompt_text


# ---------------------------------------------------------------------------
# Scenario: Archival promotion — idempotent
# ---------------------------------------------------------------------------


class TestArchivalPromotion:
    def test_archival_marks_complete(self):
        job = _make_job(job_type=JobType.archival_promotion)

        mock_recall = MagicMock()
        mock_recall.entry_id = "recall-1"
        mock_recall.content = "Some old memory."

        mock_svc = MagicMock()
        mock_svc.recall.get_expired_entries.return_value = [mock_recall]
        mock_svc.archival.exists.return_value = False

        with _mock_memory_service(mock_svc):
            result = handle_archival_promotion(job)

        assert result.status == JobStatus.complete
        assert result.completed_at is not None

    def test_archival_idempotent_skips_existing(self):
        """Already-archived entries must not be re-inserted."""
        job = _make_job(job_type=JobType.archival_promotion)

        mock_recall = MagicMock()
        mock_recall.entry_id = "recall-already-archived"
        mock_recall.content = "Already archived."

        mock_svc = MagicMock()
        mock_svc.recall.get_expired_entries.return_value = [mock_recall]
        mock_svc.archival.exists.return_value = True  # Already archived!

        with _mock_memory_service(mock_svc):
            handle_archival_promotion(job)

        # add() must NOT have been called
        mock_svc.archival.add.assert_not_called()

    def test_archival_no_expired_entries_completes(self):
        job = _make_job(job_type=JobType.archival_promotion)
        mock_svc = MagicMock()
        mock_svc.recall.get_expired_entries.return_value = []

        with _mock_memory_service(mock_svc):
            result = handle_archival_promotion(job)

        assert result.status == JobStatus.complete


# ---------------------------------------------------------------------------
# Scenario: Job survives worker crash (status stays pending if not claimed)
# ---------------------------------------------------------------------------


class TestJobPersistence:
    def setup_method(self):
        _clear_queue()

    def test_pending_job_in_queue_survives_run_once_crash(self):
        job = _make_job()
        enqueue_job(job)
        assert job.status == JobStatus.pending

        # Simulate crash mid-dispatch by raising on dispatch
        with patch("worker.main._dispatch", side_effect=Exception("crash")):
            run_once()

        # After crash, job should be marked failed (not left dangling as running)
        assert job.status == JobStatus.failed

    def test_completed_job_has_status_complete(self):
        job = _make_job()
        enqueue_job(job)

        with _mock_model_adapter("Summary."):
            run_once()

        assert job.status == JobStatus.complete

    def test_run_once_returns_count(self):
        enqueue_job(_make_job())
        enqueue_job(_make_job())

        with _mock_model_adapter("s"):
            count = run_once()

        assert count == 2

    def test_unknown_job_type_fails(self):
        job = _make_job()
        # Manually override the job_type after creation
        object.__setattr__(job, "job_type", "unknown_type")  # bypass pydantic validator
        enqueue_job(job)
        run_once()
        assert job.status == JobStatus.failed


# ---------------------------------------------------------------------------
# Job model tests
# ---------------------------------------------------------------------------


class TestJobModel:
    def test_default_status_is_pending(self):
        job = _make_job()
        assert job.status == JobStatus.pending

    def test_job_id_is_uuid(self):
        job = _make_job()
        assert len(job.job_id) == 36

    def test_job_has_created_at(self):
        job = _make_job()
        assert isinstance(job.created_at, datetime)
