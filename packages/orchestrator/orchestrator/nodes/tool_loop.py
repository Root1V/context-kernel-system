"""tool_loop node — conditional loop: execute tool calls, re-infer until resolved.

Loop logic:
  1. If last_model_response has no tool_calls, this is a no-op (pass-through).
  2. Otherwise, execute each tool call via ToolRuntime.
  3. Append tool results to assembled_messages and call infer() again.
  4. Repeat up to max_tool_iterations.
"""

from __future__ import annotations

from ..models import RuntimeState

try:
    from model_adapter import complete
except ImportError:
    complete = None  # type: ignore[assignment,misc]

try:
    from tool_runtime import ToolRegistry, ToolRuntime
except ImportError:
    ToolRegistry = None  # type: ignore[assignment,misc]
    ToolRuntime = None  # type: ignore[assignment,misc]


def tool_loop(state: RuntimeState) -> RuntimeState:
    """Execute pending tool calls and re-infer until resolved or limit hit."""
    req = state.turn_request

    while True:
        tool_calls = state.last_model_response.get("tool_calls", [])
        if not tool_calls:
            break
        if state.tool_iterations >= req.max_tool_iterations:
            break

        state.tool_iterations += 1

        # Execute each tool call.
        tool_results: list[dict] = []
        try:
            if ToolRuntime is None or ToolRegistry is None:
                raise ImportError("tool_runtime not installed")
            runtime = ToolRuntime(registry=ToolRegistry())
            for call in tool_calls:
                name = call.get("name") or call.get("function", {}).get("name", "")
                args = call.get("arguments") or call.get("function", {}).get("arguments", {})
                result = runtime.execute_tool(name, args)
                tool_results.append(
                    {
                        "tool_call_id": call.get("id", name),
                        "role": "tool",
                        "content": result.output,
                    }
                )
                state.tool_results_log.append(
                    {
                        "iteration": state.tool_iterations,
                        "tool": name,
                        "success": result.status == "success",
                    }
                )
        except Exception as exc:
            tool_results.append(
                {
                    "role": "tool",
                    "content": f"[tool error: {exc}]",
                }
            )

        # Append tool results to message list and re-infer.
        state.assembled_messages.extend(tool_results)

        # Re-run inference with updated messages.
        try:
            if complete is None:
                raise ImportError("model_adapter not installed")
            response = complete(
                model_id=req.model_id,
                messages=state.assembled_messages,
            )
            state.last_model_response = response.model_dump()
        except Exception as exc:
            state.last_model_response = {
                "content": f"[re-inference error: {exc}]",
                "tool_calls": [],
                "finish_reason": "error",
            }
            break

    state.completed_nodes.append("tool_loop")
    return state
