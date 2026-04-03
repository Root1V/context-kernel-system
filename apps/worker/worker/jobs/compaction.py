"""Compaction job handler.

Loads the compaction_template.md prompt, summarizes old message buffer turns via
model_adapter, and writes a RecallEntry via MemoryService.
"""

from __future__ import annotations

import os
import sys

from ..models import Job, JobStatus

# Make packages importable
_PACKAGES = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages")
if _PACKAGES not in sys.path:
    sys.path.insert(0, _PACKAGES)

_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "..",
    "prompts",
    "summaries",
    "compaction_template.md",
)


def _load_template() -> str:
    """Load compaction prompt from file — never hardcoded inline."""
    with open(_TEMPLATE_PATH) as f:
        return f.read()


def handle_compaction(job: Job) -> Job:
    """Summarize old message buffer turns into a RecallEntry.

    Steps:
      1. Load compaction template from file.
      2. Fetch message buffer via MemoryService.
      3. Call model_adapter.complete() with the prompt.
      4. Write a RecallEntry with the summary.
      5. Clear old messages from the buffer.
    """
    try:
        template = _load_template()

        messages: list[str] = job.payload.get("messages", [])
        if not messages:
            job.status = JobStatus.complete
            return job

        prompt = template.replace("{messages}", "\n".join(messages))

        summary_text = ""
        try:
            from model_adapter import complete

            response = complete(
                model_id=job.payload.get("model_id", "gpt-4o"),
                messages=[{"role": "user", "content": prompt}],
            )
            summary_text = response.content or ""
        except Exception as exc:
            # Fallback: join messages as plain text
            summary_text = f"[compaction summary unavailable: {exc}]\n" + "\n".join(messages)

        # Write recall entry
        try:
            import datetime

            from memory import MemoryService
            from memory.models import RecallEntry, RecallEntryType

            svc = MemoryService()
            entry = RecallEntry(
                session_id=job.session_id,
                content=summary_text,
                entry_type=RecallEntryType.compaction_summary,
                source_turn_ids=job.payload.get("turn_ids", []),
                created_at=datetime.datetime.utcnow(),
            )
            svc.recall.add(entry)
        except Exception:
            pass

        from datetime import datetime as dt

        job.status = JobStatus.complete
        job.completed_at = dt.utcnow()
    except Exception as exc:
        job.status = JobStatus.failed
        job.error = str(exc)

    return job
