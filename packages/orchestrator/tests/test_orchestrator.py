"""Integration tests for the Orchestrator DAG.

These tests run against the sequential fallback (no LangGraph required) and
use mocks for all downstream packages (model_adapter, memory, retrieval, etc.)
so the orchestrator logic can be tested in isolation.

Spec scenarios covered:
  - Happy path turn without tool calls
  - Tool-call loop executes and resolves
  - Max tool iterations reached → status=tool_limit_reached
  - Retrieval skip when retrieval_needed=False
  - Checkpoint resume (completed_nodes tracking)
"""

from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

# Add orchestrator package root to path so 'import orchestrator' works correctly.
# Must point to packages/orchestrator (not packages) to avoid module shadowing.
_ORCHESTRATOR_PKG = os.path.join(os.path.dirname(__file__), "..")
if _ORCHESTRATOR_PKG not in sys.path:
    sys.path.insert(0, _ORCHESTRATOR_PKG)

# Also add packages/ so other packages (context_assembler, memory, etc.) are importable.
_PACKAGES = os.path.join(os.path.dirname(__file__), "..", "..")
if _PACKAGES not in sys.path:
    sys.path.append(_PACKAGES)

from orchestrator.graph import _run_sequential, orchestrate
from orchestrator.models import RuntimeState, TurnRequest, TurnStatus

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_request(**overrides) -> TurnRequest:
    defaults = {
        "session_id": "sess-1",
        "user_message": "What is the capital of France?",
        "model_id": "gpt-4o",
        "max_tool_iterations": 3,
        "retrieval_needed": False,  # skip retrieval by default for speed
    }
    defaults.update(overrides)
    return TurnRequest(**defaults)


def _mock_model_response(content="Paris.", tool_calls=None):
    """Return a mock that looks like a ModelResponse."""
    mock = MagicMock()
    mock.model_dump.return_value = {
        "content": content,
        "tool_calls": tool_calls or [],
        "finish_reason": "stop",
        "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    }
    return mock


# ---------------------------------------------------------------------------
# Scenario: Happy-path turn completes without tool calls
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_returns_turn_response(self):
        req = _make_request()
        with patch(
            "orchestrator.nodes.call_model.complete", return_value=_mock_model_response("Paris.")
        ):
            result = orchestrate(req)

        assert result.session_id == "sess-1"
        assert result.assistant_message == "Paris."
        assert result.status == TurnStatus.ok

    def test_turn_id_matches_request(self):
        req = _make_request()
        with patch("orchestrator.nodes.call_model.complete", return_value=_mock_model_response()):
            result = orchestrate(req)

        assert result.turn_id == req.turn_id

    def test_no_tool_calls_made(self):
        req = _make_request()
        with patch("orchestrator.nodes.call_model.complete", return_value=_mock_model_response()):
            result = orchestrate(req)

        assert result.tool_calls_made == 0


# ---------------------------------------------------------------------------
# Scenario: Tool-call loop executes and resolves
# ---------------------------------------------------------------------------


class TestToolCallLoop:
    def test_tool_loop_runs_and_resolves(self):
        req = _make_request(retrieval_needed=False, max_tool_iterations=3)
        tool_call = {"id": "call-1", "name": "search", "arguments": {"query": "Paris"}}

        # First call returns tool_calls; second call (re-inference) returns final answer.
        call_count = {"n": 0}

        def _side_effect(model_id, messages):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return _mock_model_response("", tool_calls=[tool_call])
            return _mock_model_response("Paris is the capital of France.")

        mock_result = MagicMock()
        mock_result.output = "search result: Paris"
        mock_result.success = True

        with (
            patch("orchestrator.nodes.call_model.complete", side_effect=_side_effect),
            patch("orchestrator.nodes.tool_loop.complete", side_effect=_side_effect),
            patch("orchestrator.nodes.tool_loop.ToolRuntime") as MockRuntime,
        ):
            MockRuntime.return_value.execute_tool.return_value = mock_result
            result = orchestrate(req)

        assert result.status == TurnStatus.ok
        assert result.tool_calls_made >= 1


# ---------------------------------------------------------------------------
# Scenario: Max tool iterations reached
# ---------------------------------------------------------------------------


class TestMaxToolIterations:
    def test_status_tool_limit_reached(self):
        req = _make_request(retrieval_needed=False, max_tool_iterations=1)
        tool_call = {"id": "c1", "name": "loop_tool", "arguments": {}}
        always_tool = _mock_model_response("...", tool_calls=[tool_call])

        mock_result = MagicMock()
        mock_result.output = "still looping"
        mock_result.success = True

        with (
            patch("orchestrator.nodes.call_model.complete", return_value=always_tool),
            patch("orchestrator.nodes.tool_loop.complete", return_value=always_tool),
            patch("orchestrator.nodes.tool_loop.ToolRuntime") as MockRuntime,
        ):
            MockRuntime.return_value.execute_tool.return_value = mock_result
            result = orchestrate(req)

        assert result.status == TurnStatus.tool_limit_reached


# ---------------------------------------------------------------------------
# Scenario: Retrieval skip when retrieval_needed=False
# ---------------------------------------------------------------------------


class TestRetrievalSkip:
    def test_retrieve_context_not_called_when_skipped(self):
        req = _make_request(retrieval_needed=False)
        initial_state = RuntimeState(turn_request=req, retrieval_needed=False)

        with patch("orchestrator.nodes.call_model.complete", return_value=_mock_model_response()):
            final = asyncio.run(_run_sequential(initial_state))

        # When retrieval_needed=False, the retrieve_context node should NOT be in completed_nodes
        assert "retrieve_context" not in final.completed_nodes

    def test_retrieved_chunks_empty_when_skipped(self):
        req = _make_request(retrieval_needed=False)
        with patch("orchestrator.nodes.call_model.complete", return_value=_mock_model_response()):
            result = orchestrate(req)

        # Result is still ok — no retrieval needed.
        assert result.status == TurnStatus.ok


# ---------------------------------------------------------------------------
# Scenario: Checkpoint resume (completed_nodes tracking)
# ---------------------------------------------------------------------------


class TestCheckpointResume:
    def test_completed_nodes_populated(self):
        req = _make_request()
        initial = RuntimeState(turn_request=req, retrieval_needed=False)
        with patch("orchestrator.nodes.call_model.complete", return_value=_mock_model_response()):
            final = asyncio.run(_run_sequential(initial))

        assert "receive_request" in final.completed_nodes
        assert "load_state" in final.completed_nodes
        assert "hydrate_memory" in final.completed_nodes
        assert "assemble_context" in final.completed_nodes
        assert "infer" in final.completed_nodes
        assert "persist_state" in final.completed_nodes

    def test_retrieve_context_in_nodes_when_retrieval_needed(self):
        req = _make_request(retrieval_needed=True)
        initial = RuntimeState(turn_request=req, retrieval_needed=True)
        with patch("orchestrator.nodes.call_model.complete", return_value=_mock_model_response()):
            final = asyncio.run(_run_sequential(initial))

        assert "retrieve_context" in final.completed_nodes


# ---------------------------------------------------------------------------
# Unit: RuntimeState model
# ---------------------------------------------------------------------------


class TestRuntimeState:
    def test_default_state_fields(self):
        req = _make_request()
        state = RuntimeState(turn_request=req)
        assert state.retrieved_chunks == []
        assert state.assembled_messages == []
        assert state.tool_iterations == 0
        assert state.final_response is None

    def test_turn_request_propagated(self):
        req = _make_request(session_id="my-session")
        state = RuntimeState(turn_request=req)
        assert state.turn_request.session_id == "my-session"
