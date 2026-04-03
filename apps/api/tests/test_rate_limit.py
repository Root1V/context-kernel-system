"""Tests for the rate limiting on POST /chat.

Uses a minimal test app with a tight 1/minute limit to validate:
- Requests within the limit return 200
- The (N+1)th request returns 429
- The 429 response includes a Retry-After header
"""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
slowapi = pytest.importorskip("slowapi")

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# ---------------------------------------------------------------------------
# Minimal test app — isolates rate limit behaviour from production app state
# ---------------------------------------------------------------------------

_limiter = Limiter(key_func=get_remote_address)
_app = FastAPI()
_app.state.limiter = _limiter
_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
_app.add_middleware(SlowAPIMiddleware)


@_app.post("/chat")
@_limiter.limit("1/minute")
async def _chat(request: Request) -> dict:
    return {"ok": True}


_client = TestClient(_app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRateLimitIntegration:
    def setup_method(self) -> None:
        """Reset limiter storage before each test to avoid cross-test pollution."""
        _limiter._storage.reset()

    def test_request_within_limit_returns_200(self) -> None:
        response = _client.post("/chat")
        assert response.status_code == 200

    def test_request_exceeding_limit_returns_429(self) -> None:
        # First request — within limit
        first = _client.post("/chat")
        assert first.status_code == 200

        # Second request — exceeds 1/minute limit
        second = _client.post("/chat")
        assert second.status_code == 429

    def test_429_response_includes_retry_after_header(self) -> None:
        _client.post("/chat")  # consume the 1 allowed request
        response = _client.post("/chat")  # this one is rate-limited

        assert response.status_code == 429
        assert "retry-after" in {k.lower() for k in response.headers}
