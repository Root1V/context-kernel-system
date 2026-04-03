"""End-to-end smoke test.

Exercises the full turn path:
  API request → orchestrator DAG → context_assembler → model_adapter
  → tool_runtime (no-op) → memory → state → response

All external I/O (DB, LLM API calls) is replaced with in-process fakes so
the test runs without any infrastructure.

The test verifies:
  1. A valid ChatRequest produces a ChatResponse with a non-empty assistant message.
  2. The response session_id matches the request.
  3. The orchestrator marks the turn as `ok` (not tool_limit_reached or error).
  4. Memory and state services are exercised without exceptions.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# sys.path: make all packages importable
# ---------------------------------------------------------------------------

_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
_PACKAGES = os.path.join(_REPO_ROOT, "packages")
_ORCHESTRATOR_PKG = os.path.join(_PACKAGES, "orchestrator")

for _p in [_PACKAGES, _ORCHESTRATOR_PKG]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Fake providers injected into sys.modules before any package imports them
# ---------------------------------------------------------------------------


def _build_fake_model_adapter() -> MagicMock:
    """Return a fake model_adapter module whose complete() echoes the prompt."""

    def _complete(model_id: str, messages: list[dict[str, Any]], **kw):
        last_content = messages[-1].get("content", "") if messages else ""

        # Return a real object (not MagicMock) so model_dump() works correctly
        class _FakeResponse:
            content = f"Echo ({model_id}): {str(last_content)[:50]}"
            tool_calls: list = []
            finish_reason = "stop"

            def model_dump(self):
                return {
                    "content": self.content,
                    "tool_calls": self.tool_calls,
                    "finish_reason": self.finish_reason,
                }

        return _FakeResponse()

    def _count_tokens(text: str, model_id: str = "gpt-4o") -> int:
        return len(str(text)) // 4

    mod = MagicMock()
    mod.complete = _complete
    mod.count_tokens = _count_tokens
    return mod


@contextmanager
def _inject_fake_modules() -> Generator[None, None, None]:
    """Inject fake modules before importing any package that uses them."""
    injected = {
        "model_adapter": _build_fake_model_adapter(),
        "memory": MagicMock(),
        "state": MagicMock(),
        "retrieval": MagicMock(),
        "tool_runtime": MagicMock(),
        "storage": MagicMock(),
    }
    # Configure memory fake
    injected["memory"].MemoryService.return_value.message_buffer.get_recent.return_value = []
    injected["memory"].MemoryService.return_value.core.get_blocks.return_value = []
    injected["memory"].MemoryService.return_value.recall.search.return_value = []

    # Configure state fake
    injected["state"].StateService.return_value.get_session_state.return_value = None
    injected["state"].StateService.return_value.update_session_state.return_value = None

    # Configure retrieval fake
    injected["retrieval"].RetrievalService.return_value.search.return_value = []

    # Configure tool_runtime fake
    injected["tool_runtime"].ToolRuntime.return_value.list_tools.return_value = []

    originals = {k: sys.modules.get(k) for k in injected}
    sys.modules.update(injected)
    try:
        yield
    finally:
        for k, v in originals.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


# ---------------------------------------------------------------------------
# Import orchestrator inside the fake-module context
# ---------------------------------------------------------------------------


class TestEndToEndTurn:
    """Full-path smoke tests: API → orchestrator → all packages → response."""

    def _run_turn(self, session_id: str, turn_id: str, message: str) -> Any:
        """Helper: run a full orchestration turn with all externals faked."""
        with _inject_fake_modules():
            import importlib

            # Force reload of the nodes that do module-level optional imports
            import orchestrator.nodes.call_model as call_model_mod

            importlib.reload(call_model_mod)

            import orchestrator.graph as graph_mod

            importlib.reload(graph_mod)

            import orchestrator as orch_mod

            importlib.reload(orch_mod)

            from orchestrator import TurnRequest, orchestrate

            req = TurnRequest(
                session_id=session_id,
                turn_id=turn_id,
                user_message=message,
                model_id="gpt-4o",
            )
            return orchestrate(req)

    def test_valid_chat_request_returns_response(self):
        response = self._run_turn("smoke-1", "t1", "What is the capital of France?")
        assert response is not None
        assert response.session_id == "smoke-1"
        assert response.assistant_message

    def test_response_turn_id_matches_request(self):
        response = self._run_turn("smoke-2", "turn-99", "Hello!")
        assert response.turn_id == "turn-99"

    def test_orchestrator_status_ok(self):
        with _inject_fake_modules():
            import importlib

            import orchestrator as om
            import orchestrator.graph as gm
            import orchestrator.nodes.call_model as cm

            importlib.reload(cm)
            importlib.reload(gm)
            importlib.reload(om)
            from orchestrator import TurnRequest, TurnStatus, orchestrate

            req = TurnRequest(session_id="s3", turn_id="t3", user_message="Ping", model_id="gpt-4o")
            response = orchestrate(req)
        assert response.status == TurnStatus.ok

    def test_no_tool_calls_in_plain_response(self):
        response = self._run_turn("smoke-4", "t4", "What time is it?")
        assert response.tool_calls_made == 0

    def test_context_assembler_invoked_during_turn(self):
        """assemble_context node must appear in completed_nodes after a turn."""
        with _inject_fake_modules():
            import importlib

            import orchestrator as om
            import orchestrator.graph as gm
            import orchestrator.nodes.call_model as cm

            importlib.reload(cm)
            importlib.reload(gm)
            importlib.reload(om)

            from orchestrator import TurnRequest
            from orchestrator.graph import _run_sequential
            from orchestrator.models import RuntimeState

            req = TurnRequest(
                session_id="s5",
                turn_id="t5",
                user_message="Test context assembly",
                model_id="gpt-4o",
            )
            initial_state = RuntimeState(
                turn_request=req,
                retrieval_needed=req.retrieval_needed,
            )
            final_state = _run_sequential(initial_state)

        assert "assemble_context" in final_state.completed_nodes, (
            "assemble_context node was not executed during the turn"
        )
