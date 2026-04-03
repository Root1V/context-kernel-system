# Run: uv run python3 examples/02_memory_retrieval_smoke.py
"""
Layer 2 — Memory + Retrieval
Packages: memory, retrieval

What this tests:
  - memory.MemoryService.snapshot()  →  loads all 4 memory layers for a session
  - retrieval.RetrievalService.search()  →  hybrid BM25+vector search for relevant chunks
"""

import os
import sys
import uuid

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pkg in ["memory", "retrieval", "storage"]:  # retrieval depends on storage models
    _d = os.path.join(_ROOT, "packages", _pkg)
    if _d not in sys.path:
        sys.path.insert(0, _d)

SESSION_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
SEARCH_QUERY = "context engineering memory system"

# ---------------------------------------------------------------------------
# Section 1: memory — MemoryService.snapshot()
# ---------------------------------------------------------------------------
print("\n--- Memory Snapshot ---")
try:
    from memory import MemoryService

    svc = MemoryService()
    snap = svc.snapshot(SESSION_ID)

    core = snap.core_memory
    buffer = snap.message_buffer
    recall = snap.recall_entries

    print(f"  core_memory     : {len(core)} block(s)")
    for b in core[:3]:
        print(f"    [{b.label}] {str(b.value)[:80]}")

    print(f"  message_buffer  : {len(buffer)} turn(s)")
    for t in buffer[:3]:
        print(f"    {t.role}: {str(t.content)[:80]}")

    print(f"  recall_entries  : {len(recall)} entry(ies)")
    for e in recall[:3]:
        print(f"    • {str(e.content)[:80]}")

    if not core and not buffer and not recall:
        print("  ⚠️  fallback: snapshot is empty (no DB configured — in-memory fallback returns empty)")
    else:
        print("\n  ✓ MemoryService returned non-empty snapshot")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 2: retrieval — RetrievalService.search()
# ---------------------------------------------------------------------------
print("\n--- Retrieved Chunks ---")
try:
    from retrieval import RetrievalService

    svc = RetrievalService()
    chunks = svc.search(SEARCH_QUERY, top_k=3)

    print(f"  query  : \"{SEARCH_QUERY}\"")
    print(f"  top_k  : 3")
    print(f"  found  : {len(chunks)} chunk(s)")

    for i, chunk in enumerate(chunks, 1):
        print(f"\n  Chunk {i}:")
        print(f"    {chunk.content[:120]}")

    if not chunks:
        print("  ⚠️  fallback: 0 chunks returned (no DB configured — RetrievalService returns empty list)")
    else:
        print("\n  ✓ RetrievalService returned results")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

print()
