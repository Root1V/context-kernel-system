"""Unit tests for tool-runtime-mcp — covers all spec scenarios."""
from __future__ import annotations

import pytest

from tool_runtime import (
    ToolArgumentValidationError,
    ToolNotFoundError,
    ToolRegistry,
    ToolResult,
    ToolRuntime,
)


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        "read_file",
        {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    )
    return reg


@pytest.fixture
def runtime(registry) -> ToolRuntime:
    def executor(tool_name, arguments):
        return f"content of {arguments.get('path', '')}"

    return ToolRuntime(registry=registry, executor_fn=executor)


class TestRegistry:
    def test_get_registered_schema(self, registry):
        schema = registry.get_tool_schema("read_file")
        assert "properties" in schema

    def test_unregistered_tool_raises(self, registry):
        with pytest.raises(ToolNotFoundError) as exc_info:
            registry.get_tool_schema("unknown_tool")
        assert "unknown_tool" in str(exc_info.value)

    def test_load_tools_bulk(self):
        reg = ToolRegistry()
        reg.load_tools([
            {"name": "search_files", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "run_command", "parameters": {"type": "object"}},
        ])
        assert reg.is_registered("search_files")
        assert reg.is_registered("run_command")


class TestSafety:
    def test_valid_arguments_pass(self, runtime):
        result = runtime.execute_tool("read_file", {"path": "/workspace/main.py"})
        assert result.status == "success"

    def test_missing_required_arg_raises(self, runtime):
        with pytest.raises(ToolArgumentValidationError):
            runtime.execute_tool("read_file", {})  # missing 'path'


class TestExecute:
    def test_valid_call_returns_tool_result(self, runtime):
        result = runtime.execute_tool("read_file", {"path": "/main.py"})
        assert isinstance(result, ToolResult)
        assert result.status == "success"
        assert "main.py" in result.output

    def test_unregistered_tool_raises_not_found(self, runtime):
        with pytest.raises(ToolNotFoundError):
            runtime.execute_tool("unknown_tool", {})

    def test_large_output_is_truncated(self, registry):
        def big_executor(tool_name, arguments):
            return "x" * 100_000  # ~25k tokens at 4 chars/token

        rt = ToolRuntime(registry=registry, executor_fn=big_executor, max_output_tokens=100)
        result = rt.execute_tool("read_file", {"path": "/file.py"})
        assert result.truncated is True
        assert "[output truncated]" in result.output
        assert len(result.output) <= 100 * 4 + len("\n[output truncated]")

    def test_tool_runtime_does_not_self_invoke(self, runtime):
        """Tool runtime must return result as-is, never recursively call execute_tool."""
        calls = []

        def tracking_executor(tool_name, arguments):
            calls.append(tool_name)
            # Return a result that "mentions" another tool — should not be called
            return f"use read_file on path /other.py"

        rt = ToolRuntime(registry=runtime._registry, executor_fn=tracking_executor)
        rt.execute_tool("read_file", {"path": "/a.py"})
        assert calls == ["read_file"]  # only called once
