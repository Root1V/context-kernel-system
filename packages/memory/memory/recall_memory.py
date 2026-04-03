"""Recall memory — bounded recency log of recent events."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from .models import RecallEntry


class RecallMemoryService:
    """In-process recall memory with recency-window filtering.

    Entries older than *recall_window_hours* are considered expired and
    eligible for archival promotion.
    """

    def __init__(self, recall_window_hours: float = 24.0, repo=None) -> None:
        self._window = timedelta(hours=recall_window_hours)
        self._repo = repo
        self._store: dict[str, list[RecallEntry]] = {}

    def add_entry(self, entry: RecallEntry) -> RecallEntry:
        key = str(entry.session_id)
        self._store.setdefault(key, []).append(entry)
        return entry

    def get_entries(self, session_id: UUID, *, include_expired: bool = False) -> list[RecallEntry]:
        entries = self._store.get(str(session_id), [])
        if include_expired:
            return list(entries)
        cutoff = datetime.utcnow() - self._window
        return [e for e in entries if e.created_at >= cutoff]

    def get_expired_entries(self, session_id: UUID) -> list[RecallEntry]:
        entries = self._store.get(str(session_id), [])
        cutoff = datetime.utcnow() - self._window
        return [e for e in entries if e.created_at < cutoff]

    def remove_entry(self, session_id: UUID, entry_id: UUID) -> None:
        key = str(session_id)
        self._store[key] = [e for e in self._store.get(key, []) if e.id != entry_id]
