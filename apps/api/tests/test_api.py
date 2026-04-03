"""Integration tests for the API layer.

Spec scenarios covered:
  - POST /chat: valid request triggers orchestrator, returns ChatResponse
  - POST /chat: missing 'message' field returns 422
  - POST /sessions: creates session with unique ID
  - GET /sessions/{id}: retrieves session or returns 404
  - GET /health: returns {"status": ...} with 200
  - No context-assembly/memory/retrieval logic in routes (structural check)

Requires: fastapi, httpx (for TestClient)
"""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Structural check: does not require fastapi — always runs
# ---------------------------------------------------------------------------

class TestRouteNoBizLogic:
    def test_chat_route_has_no_direct_assembly_import(self):
        """Ensure the chat route module does not import forbidden packages."""
        route_file = os.path.join(
            os.path.dirname(__file__), "..", "app", "routes", "chat.py"
        )
        with open(route_file) as f:
            source = f.read()

        forbidden = ["context_assembler", "memory.service", "retrieval.service"]
        for name in forbidden:
            assert name not in source, (
                f"Route file must not import '{name}' directly — delegate to orchestrator."
            )

    def test_sessions_route_has_no_direct_assembly_import(self):
        route_file = os.path.join(
            os.path.dirname(__file__), "..", "app", "routes", "sessions.py"
        )
        with open(route_file) as f:
            source = f.read()
        forbidden = ["context_assembler", "memory.service", "retrieval.service"]
        for name in forbidden:
            assert name not in source

    def test_health_route_has_no_direct_assembly_import(self):
        route_file = os.path.join(
            os.path.dirname(__file__), "..", "app", "routes", "health.py"
        )
        with open(route_file) as f:
            source = f.read()
        forbidden = ["context_assembler", "memory.service", "retrieval.service"]
        for name in forbidden:
            assert name not in source


# ---------------------------------------------------------------------------
# Routes requiring FastAPI TestClient
# ---------------------------------------------------------------------------

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

# Add packages to path for orchestrator and state imports.
_API_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
_PACKAGES = os.path.join(_API_ROOT, "packages")
_ORCHESTRATOR = os.path.join(_PACKAGES, "orchestrator")
for _p in [_PACKAGES, _ORCHESTRATOR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi.testclient import TestClient
from apps.api.app.main import app

client = TestClient(app)


def _mock_orchestrate(session_id="sess-1", assistant_message="Paris.", status="ok"):
    mock = MagicMock()
    mock.session_id = session_id
    mock.turn_id = "turn-abc"
    mock.assistant_message = assistant_message
    mock.status.value = status
    mock.tool_calls_made = 0
    mock.state_persisted = False
    return mock


class TestChatRoute:
    def test_valid_request_calls_orchestrator(self):
        with patch("apps.api.app.routes.chat.orchestrate", return_value=_mock_orchestrate()) as mock_orch:
            response = client.post("/chat", json={
                "session_id": "sess-1",
                "message": "What is the capital of France?",
            })

        assert response.status_code == 200
        data = response.json()
        assert data["assistant_message"] == "Paris."
        assert data["session_id"] == "sess-1"
        assert data["turn_id"] == "turn-abc"
        mock_orch.assert_called_once()

    def test_missing_message_returns_422(self):
        response = client.post("/chat", json={"session_id": "sess-1"})
        assert response.status_code == 422

    def test_missing_session_id_returns_422(self):
        response = client.post("/chat", json={"message": "hello"})
        assert response.status_code == 422

    def test_response_shape(self):
        with patch("apps.api.app.routes.chat.orchestrate", return_value=_mock_orchestrate()):
            response = client.post("/chat", json={
                "session_id": "sess-1",
                "message": "hi",
            })
        data = response.json()
        assert "session_id" in data
        assert "turn_id" in data
        assert "assistant_message" in data
        assert "status" in data
        assert "tool_calls_made" in data


class TestSessionsRoute:
    def test_create_session_returns_session_id(self):
        response = client.post("/sessions", json={})
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36

    def test_create_session_unique_ids(self):
        r1 = client.post("/sessions", json={})
        r2 = client.post("/sessions", json={})
        assert r1.json()["session_id"] != r2.json()["session_id"]

    def test_get_nonexistent_session_returns_404(self):
        response = client.get("/sessions/does-not-exist-xyz")
        assert response.status_code == 404

    def test_get_existing_session(self):
        session_id = "test-session-retrieve"
        mock_state = MagicMock()
        mock_state.session_id = session_id
        mock_state.user_id = "user-123"

        with patch("apps.api.app.routes.sessions.StateService") as MockSvc:
            MockSvc.return_value.get_session_state.return_value = mock_state
            response = client.get(f"/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id


class TestHealthRoute:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_has_status_field(self):
        response = client.get("/health")
        assert "status" in response.json()
