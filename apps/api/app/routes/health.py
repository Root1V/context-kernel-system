"""GET /health route — check DB and MCP gateway connectivity."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    checks: dict = {}


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health status."""
    checks: dict = {}

    # DB check
    try:
        from storage.db import init_db  # noqa: F401

        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"unavailable: {exc}"

    # MCP gateway check
    try:
        from tool_runtime import ToolRuntime  # noqa: F401

        checks["mcp"] = "ok"
    except Exception as exc:
        checks["mcp"] = f"unavailable: {exc}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return HealthResponse(status=overall, checks=checks)
