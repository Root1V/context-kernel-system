"""Tool registry — loads and stores MCP tool schemas at startup."""

from __future__ import annotations

from typing import Any


class ToolNotFoundError(Exception):
    def __init__(self, tool_name: str) -> None:
        super().__init__(f"Tool not registered: {tool_name!r}")
        self.tool_name = tool_name


class ToolRegistry:
    """Stores tool schemas keyed by tool name.

    Populated at startup via :meth:`load_tools`.
    Can also be seeded directly via :meth:`register` for tests.
    """

    def __init__(self) -> None:
        self._schemas: dict[str, dict[str, Any]] = {}

    def register(self, tool_name: str, schema: dict[str, Any]) -> None:
        """Register a single tool schema."""
        self._schemas[tool_name] = schema

    def load_tools(self, tools: list[dict[str, Any]]) -> None:
        """Bulk-register tools from a list of MCP tool description dicts.

        Each dict must have a ``name`` key and an ``inputSchema`` or
        ``parameters`` key containing the JSON schema for arguments.
        """
        for tool in tools:
            name = tool.get("name")
            if not name:
                continue
            schema = tool.get("inputSchema") or tool.get("parameters") or {}
            self._schemas[name] = schema

    def get_tool_schema(self, tool_name: str) -> dict[str, Any]:
        if tool_name not in self._schemas:
            raise ToolNotFoundError(tool_name)
        return self._schemas[tool_name]

    def list_tools(self) -> list[str]:
        return list(self._schemas.keys())

    def is_registered(self, tool_name: str) -> bool:
        return tool_name in self._schemas
