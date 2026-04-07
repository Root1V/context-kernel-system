# Run: uv run python3 examples/05_orchestrator_direct.py
"""
Layer 5 — Orchestrator (full pipeline)
Package: orchestrator — exercises ALL 9 packages in one call

How each orchestrator node maps to a package:
  receive_request   → (validates input, no external package)
  load_state        → state.StateService.get_session_state()
  hydrate_memory    → memory.MemoryService.snapshot()
  retrieve_context  → retrieval.RetrievalService.search()   (if retrieval_needed=True)
  assemble_context  → context_assembler.assemble()
  infer             → model_adapter.complete()
  tool_loop         → tool_runtime.ToolRuntime.execute_tool() + re-infer
  persist_state     → state.StateService.update_session_state()
  (all nodes traced) → observability.trace_node()

Without a DB or LLM: each node runs with graceful fallback and returns empty data.
The TurnResponse will still be populated with status="ok" or status="error".
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pkg in [
    "orchestrator",
    "state",
    "memory",
    "retrieval",
    "context_assembler",
    "observability",
    "model_adapter",
    "tool_runtime",
    "storage",
]:
    _d = os.path.join(_ROOT, "packages", _pkg)
    if _d not in sys.path:
        sys.path.insert(0, _d)

# ---------------------------------------------------------------------------
# Section 1: build TurnRequest
# ---------------------------------------------------------------------------
print("\n--- Turn Request ---")
try:
    from orchestrator import TurnRequest

    req = TurnRequest(
        session_id="00000000-0000-0000-0000-000000000001",
        user_message="Explain how context assembly works in this system",
        model_id="gpt-4o",
        max_tool_iterations=3,
        retrieval_needed=True,
    )
    print(f"  session_id         : {req.session_id}")
    print(f"  user_message       : {req.user_message}")
    print(f"  model_id           : {req.model_id}")
    print(f"  max_tool_iterations: {req.max_tool_iterations}")
    print(f"  retrieval_needed   : {req.retrieval_needed}")
    print(f"  turn_id            : {req.turn_id}")
    print(f"\n  ✓ TurnRequest built")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")
    req = None

# ---------------------------------------------------------------------------
# Section 2: run the full orchestrator pipeline
# ---------------------------------------------------------------------------
print("\n--- Orchestrator Pipeline ---")
print("  Running all DAG nodes: receive_request → load_state → hydrate_memory")
print("  → retrieve_context → assemble_context → infer → [tool_loop] → persist_state")
print()

if req is None:
    print("  ⚠️  Skipping — TurnRequest creation failed above")
else:
    try:
        from orchestrator import orchestrate

        response = orchestrate(req)

        print("\n--- Turn Response ---")
        print(f"  session_id       : {response.session_id}")
        print(f"  turn_id          : {response.turn_id}")
        print(f"  status           : {response.status}")
        print(f"  tool_calls_made  : {response.tool_calls_made}")
        print(f"  state_persisted  : {response.state_persisted}")
        print(f"\n  assistant_message:")
        msg = response.assistant_message or "(empty — no LLM configured)"
        for line in msg[:300].splitlines():
            print(f"    {line}")
        if len(msg) > 300:
            print(f"    ... ({len(msg) - 300} more chars)")

        if not response.assistant_message:
            print("\n  ⚠️  fallback: empty assistant_message — set OPENAI_API_KEY to get a real response")
        print(f"\n  ✓ orchestrate() completed — status={response.status.value}")
    except Exception as exc:
        print(f"  ⚠️  fallback: {exc}")

print()
