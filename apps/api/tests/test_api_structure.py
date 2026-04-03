"""Structural tests for the API layer — check no business logic in routes.

These tests do NOT require fastapi and always run.
"""

from __future__ import annotations

import os

ROUTES_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "routes")
FORBIDDEN_IMPORTS = ["context_assembler", "memory.service", "retrieval.service"]


def _read_route(name: str) -> str:
    with open(os.path.join(ROUTES_DIR, f"{name}.py")) as f:
        return f.read()


class TestRouteNoBizLogic:
    """Enforce: API routes delegate to orchestrator — no biz logic inline."""

    def test_chat_route_no_assembly_import(self):
        source = _read_route("chat")
        for name in FORBIDDEN_IMPORTS:
            assert name not in source, f"chat.py must not import '{name}'"

    def test_sessions_route_no_assembly_import(self):
        source = _read_route("sessions")
        for name in FORBIDDEN_IMPORTS:
            assert name not in source

    def test_health_route_no_assembly_import(self):
        source = _read_route("health")
        for name in FORBIDDEN_IMPORTS:
            assert name not in source

    def test_chat_route_calls_orchestrate(self):
        """Chat route must delegate to orchestrate()."""
        source = _read_route("chat")
        assert "orchestrate" in source, "chat.py must call orchestrate()"
