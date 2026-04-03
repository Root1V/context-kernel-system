"""Archival memory — vectorized long-term storage with semantic search."""

from __future__ import annotations

import math
from uuid import UUID

from .models import ArchivalEntry


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class ArchivalMemoryService:
    """In-process archival memory. Uses cosine similarity for search.

    In production, delegate to ArchivalRepository (pgvector) by passing *repo*.
    """

    def __init__(self, repo=None) -> None:
        self._repo = repo
        self._store: dict[str, list[ArchivalEntry]] = {}

    def add_entry(self, entry: ArchivalEntry) -> ArchivalEntry:
        self._store.setdefault(str(entry.session_id), []).append(entry)
        return entry

    def search(
        self, session_id: UUID, query_embedding: list[float], top_k: int = 10
    ) -> list[ArchivalEntry]:
        entries = self._store.get(str(session_id), [])
        if not entries:
            return []
        ranked = sorted(
            entries,
            key=lambda e: _cosine_similarity(e.embedding, query_embedding),
            reverse=True,
        )
        return ranked[:top_k]

    def all_entries(self, session_id: UUID) -> list[ArchivalEntry]:
        return list(self._store.get(str(session_id), []))
