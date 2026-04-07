# Run: uv run python3 examples/04_model_tool_runtime_smoke.py
"""
Layer 4 — Model Adapter + Tool Runtime
Packages: model_adapter, tool_runtime

What this tests:
  - tool_runtime.ToolRegistry.register()    →  registers a tool schema
  - tool_runtime.ToolRuntime.execute_tool() →  executes a tool via executor_fn
  - model_adapter.count_tokens()            →  token counting (no API key needed)
  - model_adapter.supported_models()        →  lists available model IDs
  - model_adapter.complete()               →  calls LLM (requires API key)
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pkg in ["tool_runtime", "model_adapter"]:
    _d = os.path.join(_ROOT, "packages", _pkg)
    if _d not in sys.path:
        sys.path.insert(0, _d)

# ---------------------------------------------------------------------------
# Section 1: tool_runtime — register and execute an echo tool
# ---------------------------------------------------------------------------
print("\n--- Tool Runtime ---")
try:
    from tool_runtime import ToolRegistry, ToolRuntime, ToolResult

    registry = ToolRegistry()

    # Register an echo tool with a minimal JSON schema
    registry.register(
        "echo",
        {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
            "required": ["message"],
        },
    )

    def _echo_executor(tool_name: str, arguments: dict) -> str:
        return f"[echo] {arguments['message']}"

    runtime = ToolRuntime(registry=registry, executor_fn=_echo_executor)
    result: ToolResult = runtime.execute_tool("echo", {"message": "hello from tool_runtime"})

    print(f"  tool_name  : {result.tool_name}")
    print(f"  status     : {result.status}")
    print(f"  output     : {result.output}")
    print(f"  error      : {result.error}")
    print(f"  truncated  : {result.truncated}")
    print(f"\n  ✓ ToolRuntime executed echo tool successfully")
    print(f"  Registered tools: {registry.list_tools()}")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 2: model_adapter — token counting (no API key needed)
# ---------------------------------------------------------------------------
print("\n--- Model Adapter (token count) ---")
try:
    from model_adapter import count_tokens, supported_models

    test_text = "Explain how context assembly works in this system in 1 sentence."
    token_count = count_tokens(test_text, model_id="gpt-4o")
    models = supported_models()

    print(f"  text            : \"{test_text[:60]}\"")
    print(f"  token_count     : {token_count}")
    print(f"  supported models: {models}")
    print(f"\n  ✓ count_tokens() works without API key")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 3: model_adapter — complete() (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------
print("\n--- Model Adapter (LLM call) ---")
try:
    from model_adapter import complete, UnsupportedModelError
    from model_adapter.base import RateLimitError

    messages = [{"role": "user", "content": "What is context assembly in 1 sentence?"}]
    # Uses gpt-4o-mini by default — switch to claude-3-5-haiku-20241022 if using Anthropic
    response = complete(messages=messages, model_id="gpt-4o-mini")

    print(f"  content       : {response.content[:200]}")
    print(f"  finish_reason : {response.finish_reason}")
    print(f"  tool_calls    : {len(response.tool_calls)}")
    if response.usage:
        print(f"  usage         : prompt={response.usage.prompt_tokens} "
              f"completion={response.usage.completion_tokens} "
              f"total={response.usage.total_tokens}")
    print(f"\n  ✓ model_adapter.complete() returned a ModelResponse")
except RateLimitError as exc:
    if exc.is_quota_exceeded:
        print("  ⚠️  OpenAI quota exhausted — add billing credits:")
        print("  →  https://platform.openai.com/settings/billing")
        print("  →  Or set ANTHROPIC_API_KEY in .env to use Claude instead")
    else:
        wait = exc.retry_after_seconds
        hint = f"wait ~{wait:.0f}s and retry" if wait > 0 else "wait ~60s and retry (free-tier RPM limit)"
        print(f"  ⚠️  Rate limit: {hint}")
        print("  →  Run the script again after waiting")
except UnsupportedModelError as exc:
    print(f"  ⚠️  No LLM configured: {exc}")
    print("  →  Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable LLM calls")
except Exception as exc:
    err_str = str(exc).lower()
    if any(k in err_str for k in ("api_key", "apikey", "authentication", "unauthorized", "incorrect api")):
        print("  ⚠️  No LLM configured: set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    elif "credit balance is too low" in err_str or "insufficient_quota" in err_str:
        print("  ⚠️  LLM provider has no credits — add billing credits:")
        print("  →  OpenAI:    https://platform.openai.com/settings/billing")
        print("  →  Anthropic: https://console.anthropic.com/settings/billing")
    else:
        print(f"  ⚠️  fallback: {exc}")

print()
