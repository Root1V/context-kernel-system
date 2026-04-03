"""MCP Gateway — executes tool calls through safety validation.

The orchestrator is the ONLY caller of this gateway.
This module MUST NOT self-invoke or initiate chained tool calls.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

from .registry import ToolRegistry
from .safety import validate_arguments


class ToolResult(BaseModel):
    tool_name: str
    output: str
    truncated: bool = False
    error: Optional[str] = None
    status: str = "success"  # success | error


class ToolRuntime:
    """Executes tools through the registry + safety layer.

    *executor_fn* is an async callable that performs the actual tool call.
    It receives ``(tool_name, arguments)`` and returns a string payload.
    In tests this can be a simple mock; in production it proxies to the MCP server.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        executor_fn=None,
        max_output_tokens: int = 4000,
    ) -> None:
        self._registry = registry
        self._executor_fn = executor_fn
        self._max_output_tokens = max_output_tokens

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool synchronously after safety validation.

        Raises:
            ToolNotFoundError: if *tool_name* is not in the registry.
            ToolArgumentValidationError: if *arguments* fail schema validation.
        """
        # 1. Registry check
        schema = self._registry.get_tool_schema(tool_name)  # raises ToolNotFoundError

        # 2. Safety validation
        validate_arguments(tool_name, arguments, schema)  # raises ToolArgumentValidationError

        # 3. Execute
        if self._executor_fn is None:
            return ToolResult(
                tool_name=tool_name,
                output="",
                status="error",
                error="No executor configured.",
            )

        try:
            raw_output: str = self._executor_fn(tool_name, arguments)
        except Exception as exc:
            return ToolResult(
                tool_name=tool_name,
                output="",
                status="error",
                error=str(exc),
            )

        # 4. Truncate output if too large (approx: 4 chars per token)
        max_chars = self._max_output_tokens * 4
        truncated = False
        if len(raw_output) > max_chars:
            raw_output = raw_output[:max_chars] + "\n[output truncated]"
            truncated = True

        return ToolResult(
            tool_name=tool_name,
            output=raw_output,
            truncated=truncated,
            status="success",
        )
