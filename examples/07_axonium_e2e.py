# Run: uv run python3 examples/07_axonium_e2e.py
"""
E2E — Axonium Local LLM (llama-server via AxoniumAdapter)
Package: model_adapter → AxoniumAdapter

What this tests:
  1. AxoniumAdapter instantiation — requires the 'axonium' package installed.
  2. Direct complete() call via model_adapter.complete() routing (local/* model ID).
  3. Full orchestrator turn using model_id="local/mistral-7b-instruct" end-to-end.
  4. Node-level diagnostic: inspects RuntimeState after each DAG node to confirm
     each component actually ran (not silently fell back to no-op).

Prerequisites (local llama-server must be running):
  export LLM_BASE_URL=http://localhost:8080   # or your llama-server address
  export LLM_USERNAME=<user>
  export LLM_PASSWORD=<pass>

  Start llama-server (example):
    llama-server --model models/mistral-7b-instruct.gguf --port 8080

If the server is not running each section will show a graceful fallback message.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pkg in [
    "model_adapter",
    "orchestrator",
    "state",
    "memory",
    "retrieval",
    "context_assembler",
    "observability",
    "tool_runtime",
    "storage",
]:
    _d = os.path.join(_ROOT, "packages", _pkg)
    if _d not in sys.path:
        sys.path.insert(0, _d)

_LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "local/mistral-7b-instruct")
_LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:8080")

# ---------------------------------------------------------------------------
# Section 1: Axonium SDK availability check
# ---------------------------------------------------------------------------
print("\n--- Axonium SDK Check ---")
try:
    from axonium import LlamaAdapter  # type: ignore[import]

    print(f"  ✓ axonium package found — LlamaAdapter importable")
except ImportError:
    print("  ⚠️  axonium package NOT installed")
    print("  →  Install with: uv add --find-links <path-to-axonium-dist> axonium")
    print("  →  Subsequent sections will show fallback messages\n")

# ---------------------------------------------------------------------------
# Section 2: AxoniumAdapter direct instantiation
# ---------------------------------------------------------------------------
print("\n--- AxoniumAdapter Instantiation ---")
adapter = None
try:
    from model_adapter import AxoniumAdapter

    adapter = AxoniumAdapter()
    print(f"  base_url : {_LLM_BASE_URL}")
    print(f"  model_id : {_LOCAL_MODEL}")
    print(f"  ✓ AxoniumAdapter instantiated")
except ImportError as exc:
    print(f"  ⚠️  fallback: {exc}")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 3: Direct chat completion via AxoniumAdapter.complete()
# ---------------------------------------------------------------------------
print("\n--- Direct complete() via AxoniumAdapter ---")
if adapter is None:
    print("  ⚠️  Skipping — AxoniumAdapter not available")
else:
    try:
        messages = [
            {"role": "system", "content": "You are a concise assistant. Answer in one sentence."},
            {"role": "user", "content": "What is the capital of France?"},
        ]
        response = adapter.complete(messages=messages, model_id=_LOCAL_MODEL)
        print(f"  model_id        : {response.model_id}")
        print(f"  finish_reason   : {response.finish_reason.value}")
        print(f"  prompt_tokens   : {response.usage.prompt_tokens}")
        print(f"  completion_tokens: {response.usage.completion_tokens}")
        print(f"  content         : {response.content!r}")
        print(f"\n  ✓ AxoniumAdapter.complete() returned ModelResponse")
    except RuntimeError as exc:
        print(f"  ⚠️  fallback: {exc}")
        print(f"  →  Is llama-server running at {_LLM_BASE_URL}?")
    except Exception as exc:
        print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 4: complete() via model_adapter.complete() routing (local/* dispatch)
# ---------------------------------------------------------------------------
print("\n--- model_adapter.complete() routing ---")
try:
    from model_adapter import complete, get_context_limit
    from model_adapter.limits import is_local

    print(f"  is_local({_LOCAL_MODEL!r}) : {is_local(_LOCAL_MODEL)}")
    print(f"  context_limit           : {get_context_limit(_LOCAL_MODEL)} tokens")

    messages = [{"role": "user", "content": "Say 'hello' in Spanish."}]
    resp = complete(messages=messages, model_id=_LOCAL_MODEL)
    print(f"  content : {resp.content!r}")
    print(f"\n  ✓ model_adapter.complete() routed to AxoniumAdapter correctly")
except RuntimeError as exc:
    print(f"  ⚠️  fallback: {exc}")
    print(f"  →  Is llama-server running at {_LLM_BASE_URL}?")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 5: Full orchestrator E2E — node-level diagnostic
#
# Runs _run_sequential directly so we can inspect the full RuntimeState after
# the pipeline. This reveals what each component actually produced instead of
# relying on the final TurnResponse alone (every orchestrator node has a bare
# except: pass that silently swallows failures).
# ---------------------------------------------------------------------------
print("\n--- Full Orchestrator E2E — Node Diagnostic ---")
print(f"  model_id         : {_LOCAL_MODEL}")
print(f"  retrieval_needed : True  (exercises the full pipeline)")
print()

_NODES_EXPECTED = [
    "receive_request",
    "load_state",
    "hydrate_memory",
    "retrieve_context",
    "assemble_context",
    "infer",
    "persist_state",
]

try:
    from orchestrator import TurnRequest
    from orchestrator.graph import _run_sequential
    from orchestrator.models import RuntimeState

    req = TurnRequest(
        session_id="00000000-0000-0000-0000-000000000007",
        user_message="Briefly explain what a context window is in LLM systems.",
        model_id=_LOCAL_MODEL,
        max_tool_iterations=0,  # no tool calls — local model doesn't support them
        retrieval_needed=True,  # force the retrieve_context node to run
    )
    initial = RuntimeState(turn_request=req, retrieval_needed=True)
    final = _run_sequential(initial)

    # ── 1. Which nodes ran? ──────────────────────────────────────────────────
    print("  Nodes executed:")
    all_ran = True
    for node in _NODES_EXPECTED:
        ran = node in final.completed_nodes
        mark = "✓" if ran else "✗ MISSING"
        print(f"    [{mark}] {node}")
        if not ran:
            all_ran = False

    # ── 2. load_state — did StateService populate session_state? ────────────
    print("\n  load_state  →  session_state:")
    if final.session_state:
        sid = final.session_state.get("session_id", "(none)")
        print(f"    session_id : {sid}  ✓ StateService returned a SessionState")
    else:
        print("    (empty) ⚠️  StateService fell back / no session exists yet (first turn)")

    # ── 3. hydrate_memory — did MemoryService populate the snapshot? ─────────
    print("\n  hydrate_memory  →  memory_snapshot:")
    snap = final.memory_snapshot
    core = snap.get("core_memory", [])
    buf  = snap.get("message_buffer", [])
    rec  = snap.get("recent_recall", [])
    print(f"    core_memory    : {len(core)} block(s)")
    print(f"    message_buffer : {len(buf)} turn(s)")
    print(f"    recent_recall  : {len(rec)} entry(ies)")
    print(f"    ✓ MemoryService.snapshot() called (in-memory — empty on first turn)")

    # ── 4. retrieve_context — did RetrievalService return chunks? ───────────
    print("\n  retrieve_context  →  retrieved_chunks:")
    if final.retrieved_chunks:
        for i, c in enumerate(final.retrieved_chunks[:2]):
            print(f"    [{i}] {c[:80]}")
        print(f"    ✓ RetrievalService returned {len(final.retrieved_chunks)} chunk(s)")
    else:
        print("    (empty) ⚠️  RetrievalService fell back — pgvector DB not running")
        print("    →  docker compose -f packages/storage/docker-compose.yml up -d")

    # ── 5. assemble_context — did ContextAssembler build the messages? ───────
    print("\n  assemble_context  →  assembled_messages:")
    if final.assembled_messages:
        for msg in final.assembled_messages:
            role = msg.get("role", "?")
            body = msg.get("content", "")[:120].replace("\n", " ")
            print(f"    [{role}] {body}")
        print(f"    ✓ ContextAssembler produced {len(final.assembled_messages)} message(s)")
    else:
        print("    (empty) ⚠️  ContextAssembler fell back — bare user message used")

    # ── 6. infer — did the model actually respond? ───────────────────────────
    print("\n  infer  →  last_model_response:")
    content = final.last_model_response.get("content", "")
    usage   = final.last_model_response.get("usage", {})
    if content:
        preview = content[:150].replace("\n", " ")
        print(f"    content (preview) : {preview}")
        print(f"    prompt_tokens     : {usage.get('prompt_tokens', '?')}")
        print(f"    completion_tokens : {usage.get('completion_tokens', '?')}")
        print(f"    ✓ AxoniumAdapter hit llama-server — real model response received")
    else:
        print(f"    (empty) ⚠️  Model did not respond — is llama-server running at {_LLM_BASE_URL}?")

    # ── 7. persist_state — was state written back? ───────────────────────────
    print("\n  persist_state  →  final_response:")
    resp = final.final_response
    if resp:
        print(f"    status          : {resp.status.value}")
        print(f"    state_persisted : {resp.state_persisted}")
        note = "✓ persisted to StateService" if resp.state_persisted else "⚠️  in-memory only (no DB)"
        print(f"    {note}")
    else:
        print("    (none) ⚠️  persist_state node did not produce a TurnResponse")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n  ─────────────────────────────────────────────────────────────")
    if all_ran and content:
        print("  ✓ ALL nodes executed and model returned a real response.")
        print("  ⚠  memory/state/retrieval are in-memory (no DB/pgvector running).")
        print("     To make those fully E2E, start the DB:")
        print("     docker compose -f packages/storage/docker-compose.yml up -d")
    elif all_ran:
        print("  ✓ All nodes executed but model response was empty.")
        print(f"  ⚠  Check llama-server at {_LLM_BASE_URL}")
    else:
        print("  ✗ Some nodes were missing — see MISSING markers above.")

except Exception as exc:
    import traceback
    print(f"  ⚠️  Error running diagnostic: {exc}")
    traceback.print_exc()

print()
