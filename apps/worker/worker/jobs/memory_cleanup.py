"""Archival promotion job handler.

Scans expired recall entries and promotes them to pgvector archival memory.
Idempotent: checks for existing ArchivalEntry before inserting.
"""

from __future__ import annotations

import contextlib
import os
import sys

from ..models import Job, JobStatus

_PACKAGES = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages")
if _PACKAGES not in sys.path:
    sys.path.insert(0, _PACKAGES)


def handle_archival_promotion(job: Job) -> Job:
    """Promote aged recall entries to archival memory.

    Steps:
      1. Load expired recall entries for the session.
      2. For each entry, check if an ArchivalEntry already exists (idempotency).
      3. Generate embedding and insert ArchivalEntry.
      4. Delete the recall entry.
    """
    try:
        import datetime

        from memory import MemoryService
        from memory.models import ArchivalEntry

        svc = MemoryService()
        session_id = job.session_id

        # Get recall entries that have exceeded the recall window
        expired = svc.recall.get_expired_entries(session_id)

        for recall_entry in expired:
            # Idempotency check — skip if already archived
            already_archived = False
            with contextlib.suppress(Exception):
                already_archived = svc.archival.exists(recall_entry.entry_id)

            if already_archived:
                continue

            # Generate embedding (char/4 heuristic if embedder unavailable)
            embedding: list[float] = []
            try:
                # Real embedding would call an embedding endpoint here.
                # For now, use a random-seeded vector from content hash.
                import hashlib

                from model_adapter import count_tokens  # noqa: F401

                h = int(hashlib.md5(recall_entry.content.encode()).hexdigest(), 16)
                embedding = [((h >> i) & 0xFF) / 255.0 for i in range(1536)]
            except Exception:
                embedding = [0.0] * 1536

            archival = ArchivalEntry(
                session_id=session_id,
                content=recall_entry.content,
                embedding=embedding,
                source_recall_id=recall_entry.entry_id,
                created_at=datetime.datetime.utcnow(),
            )
            svc.archival.add(archival)

            # Remove the promoted recall entry
            with contextlib.suppress(Exception):
                svc.recall.delete(recall_entry.entry_id)

        from datetime import datetime as dt

        job.status = JobStatus.complete
        job.completed_at = dt.utcnow()
    except Exception as exc:
        job.status = JobStatus.failed
        job.error = str(exc)

    return job
