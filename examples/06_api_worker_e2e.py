# Run: uv run python3 examples/06_api_worker_e2e.py
"""
Layer 6 — API HTTP + Worker (entry points)
Apps: apps/api, apps/worker

What this tests:
  Section 1 — API E2E:
    POST http://localhost:8000/chat   →  full HTTP round-trip through the FastAPI layer
    Uses stdlib urllib.request only (no httpx dependency).

  Section 2 — Worker Job:
    worker.Job + worker.JobType       →  job model creation
    worker.enqueue_job()              →  puts a job on the in-process queue
    worker.jobs.compaction.handle_compaction()  →  runs memory compaction
      (compaction uses: memory.MemoryService, model_adapter.complete)

Run the API server first (for Section 1 only):
  cd apps/api && PYTHONPATH=../../packages uvicorn app.main:app --reload --port 8000
"""

import json
import os
import sys
import urllib.error
import urllib.request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Worker imports need apps/worker + the packages it depends on
for _pkg in ["memory", "model_adapter", "storage"]:
    _d = os.path.join(_ROOT, "packages", _pkg)
    if _d not in sys.path:
        sys.path.insert(0, _d)
_worker_dir = os.path.join(_ROOT, "apps", "worker")
if _worker_dir not in sys.path:
    sys.path.insert(0, _worker_dir)

# ---------------------------------------------------------------------------
# Section 1: API E2E — POST /chat via HTTP (requires server on :8000)
# ---------------------------------------------------------------------------
print("\n--- API E2E ---")
_api_url = "http://localhost:8000/chat"
_payload = {
    "session_id": "demo-session-001",
    "message": "What is the status of our project?",
    "model_id": "gpt-4o",
    "max_tool_iterations": 2,
    "retrieval_needed": False,
}

try:
    data = json.dumps(_payload).encode("utf-8")
    req = urllib.request.Request(
        _api_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    print(f"  HTTP status      : {resp.status}")
    print(f"  session_id       : {body.get('session_id')}")
    print(f"  turn_id          : {body.get('turn_id')}")
    print(f"  status           : {body.get('status')}")
    print(f"  tool_calls_made  : {body.get('tool_calls_made')}")
    print(f"  state_persisted  : {body.get('state_persisted')}")
    print(f"\n  assistant_message:")
    msg = body.get("assistant_message", "")
    for line in msg[:300].splitlines():
        print(f"    {line}")
    print(f"\n  ✓ POST /chat returned HTTP {resp.status}")
except urllib.error.HTTPError as exc:
    err_body = exc.read().decode("utf-8", errors="replace")[:300]
    print(f"  ⚠️  HTTP {exc.code} {exc.reason}: {err_body or '(no body)'}")
    print("  →  Check server logs; API is running but returned an error")
except urllib.error.URLError as exc:
    print(f"  ⚠️  API not running: {exc.reason}")
    print("  →  Start the server with:")
    print("     cd apps/api && PYTHONPATH=../../packages uvicorn app.main:app --reload --port 8000")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

# ---------------------------------------------------------------------------
# Section 2: Worker Job — compaction (runs directly, no server needed)
# ---------------------------------------------------------------------------
print("\n--- Worker Job ---")
try:
    from worker.models import Job, JobType
    from worker.main import enqueue_job
    from worker.jobs.compaction import handle_compaction

    job = Job(
        job_type=JobType.compaction,
        session_id="demo-session-001",
        payload={
            "messages": [
                "Turn 1: user asked about memory layers in the context kernel system",
                "Turn 2: assistant explained core memory, recall memory, and archival memory",
                "Turn 3: user asked how retrieval fits into context assembly",
                "Turn 4: assistant explained hybrid BM25+vector search feeding the assembler",
            ]
        },
    )

    print(f"  job_id    : {job.job_id}")
    print(f"  job_type  : {job.job_type.value}")
    print(f"  session_id: {job.session_id}")
    print(f"  status    : {job.status.value} (before execution)")

    enqueue_job(job)
    result = handle_compaction(job)

    print(f"\n  After handle_compaction():")
    print(f"  status       : {result.status.value}")
    print(f"  error        : {result.error}")
    print(f"  completed_at : {result.completed_at}")

    if result.status.value == "complete":
        print(f"\n  ✓ Compaction job completed successfully")
    else:
        print(f"\n  ⚠️  Job status: {result.status.value} — error: {result.error}")
        print("  →  Set OPENAI_API_KEY to enable LLM-based compaction summary")
except Exception as exc:
    print(f"  ⚠️  fallback: {exc}")

print()
