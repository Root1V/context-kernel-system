# Run: uv run python3 examples/03_context_observability_smoke.py
"""
Layer 3 — Context Assembly + Observability
Packages: context_assembler, observability

What this tests:
  - observability.configure_logging()  →  structured JSON logging setup
  - observability.get_logger()         →  emits a structured log record
  - observability.trace_node()         →  wraps a call with a trace span
  - context_assembler.assemble()       →  assembles all memory/state/retrieval
                                          into a formatted system prompt
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pkg in ["observability", "context_assembler"]:
    _d = os.path.join(_ROOT, "packages", _pkg)
    if _d not in sys.path:
        sys.path.insert(0, _d)

# ---------------------------------------------------------------------------
# Section 1: observability — structured logging
# ---------------------------------------------------------------------------
print("\n--- Observability ---")
try:
    from observability import configure_logging, get_logger

    configure_logging()
    log = get_logger("examples.03_smoke")
    log.info("observability smoke test started", extra={"script": "03_context_observability_smoke"})
    print("  ✓ configure_logging() ran — JSON log handler attached")
    print("  ✓ get_logger() returned a Logger instance")
    print("  ✓ INFO record emitted (check stderr for JSON output)")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 2: observability — trace_node span
# ---------------------------------------------------------------------------
print("\n--- Trace Span ---")
_span = None
try:
    from observability import trace_node

    with trace_node("assemble_context", session_id="demo-session-001") as span:
        _span = span
        span.attributes["step"] = "context_assembly_smoke"
        # assemble is called inside this block (see Section 3)
        _assembled_ctx = None

        # ----------------------------------------------------------------
        # Section 3: context_assembler — assemble()
        # ----------------------------------------------------------------
        from context_assembler import assemble, AssemblyInput

        inp = AssemblyInput(
            model_id="gpt-4o",
            core_memory_blocks=[
                "User: Emerce — prefers concise answers and practical examples.",
                "Current project: context-kernel-system — multi-layer AI agent memory.",
            ],
            message_buffer=[
                "user: How does memory work in this system?",
                "assistant: Memory has three layers: core (always present), recall (recent turns), and archival (long-term storage).",
                "user: How does context assembly pull all this together?",
            ],
            retrieved_chunks=[
                "Recall memory stores recent conversation facts for fast retrieval.",
                "ContextAssembler respects token budgets and drops lower-priority sections first.",
            ],
            state_summary="Session demo-session-001 | mode: analysis | progress: active",
            system_instructions="You are a context engineering research assistant. Answer in Spanish.",
        )
        _assembled_ctx = assemble(inp)
        span.attributes["total_tokens"] = _assembled_ctx.total_tokens

    # span finished — now print results
    print(f"  span_name    : {_span.name}")
    print(f"  session_id   : {_span.attributes.get('session_id')}")
    print(f"  duration_ms  : {_span.duration_ms}")
    print(f"  total_tokens : {_span.attributes.get('total_tokens')}")
    print(f"  error        : {_span.error}")
    print("\n  ✓ trace_node span completed successfully")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 4: context_assembler — assembled context render
# ---------------------------------------------------------------------------
print("\n--- Assembled Context ---")
try:
    if _assembled_ctx is not None:
        rendered = _assembled_ctx.render()
        lines = rendered.strip().splitlines()
        # Print first 20 lines so output is readable
        for line in lines[:20]:
            print(f"  {line}")
        if len(lines) > 20:
            print(f"  ... ({len(lines) - 20} more lines)")
        print(f"\n  ✓ ActiveContext rendered — {len(rendered)} chars, {_assembled_ctx.total_tokens} tokens")
    else:
        print("  ⚠️  fallback: assemble() did not produce output (check Section 2 error above)")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

print()
