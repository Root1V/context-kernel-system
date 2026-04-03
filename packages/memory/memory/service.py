"""Unified MemoryService facade exposing all four memory layers.

MessageBuffer is defined here since it doesn't warrant its own module.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable
from uuid import UUID

from .archival_memory import ArchivalMemoryService
from .core_memory import CoreMemoryService
from .models import (
    ArchivalEntry,
    CoreMemoryBlock,
    MemorySnapshot,
    MessageTurn,
    RecallEntry,
)
from .recall_memory import RecallMemoryService


@dataclass
class MessageBuffer:
    """Bounded FIFO buffer of conversation turns.

    When the buffer is full and a new message is appended, the oldest turn
    is dropped and *on_overflow* is called with the evicted turn so callers
    (e.g. the background worker dispatcher) can schedule compaction.
    """

    max_size: int = 20
    on_overflow: Callable[[MessageTurn], None] | None = None
    _buffer: deque[MessageTurn] = field(default_factory=deque, init=False)

    def append(self, turn: MessageTurn) -> MessageTurn:
        if len(self._buffer) >= self.max_size:
            evicted = self._buffer.popleft()
            if self.on_overflow:
                self.on_overflow(evicted)
        self._buffer.append(turn)
        return turn

    def messages(self) -> list[MessageTurn]:
        return list(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)


class MemoryService:
    """Facade that coordinates all four memory layers for a single session."""

    def __init__(
        self,
        max_core_tokens: int = 2000,
        recall_window_hours: float = 24.0,
        message_buffer_size: int = 20,
        on_buffer_overflow: Callable[[MessageTurn], None] | None = None,
    ) -> None:
        self._core = CoreMemoryService(max_tokens=max_core_tokens)
        self._recall = RecallMemoryService(recall_window_hours=recall_window_hours)
        self._archival = ArchivalMemoryService()
        self._buffers: dict[str, MessageBuffer] = {}
        self._buffer_size = message_buffer_size
        self._on_overflow = on_buffer_overflow

    # ------------------------------------------------------------------
    # Message buffer
    # ------------------------------------------------------------------

    def _get_buffer(self, session_id: UUID) -> MessageBuffer:
        key = str(session_id)
        if key not in self._buffers:
            self._buffers[key] = MessageBuffer(
                max_size=self._buffer_size, on_overflow=self._on_overflow
            )
        return self._buffers[key]

    def append_message(self, session_id: UUID, turn: MessageTurn) -> MessageTurn:
        return self._get_buffer(session_id).append(turn)

    def get_message_buffer(self, session_id: UUID) -> list[MessageTurn]:
        return self._get_buffer(session_id).messages()

    # ------------------------------------------------------------------
    # Core memory
    # ------------------------------------------------------------------

    def get_core_memory(self, session_id: UUID) -> list[CoreMemoryBlock]:
        return self._core.get_core_memory(session_id)

    def add_core_memory_block(self, block: CoreMemoryBlock) -> CoreMemoryBlock:
        return self._core.add_block(block)

    # ------------------------------------------------------------------
    # Recall memory
    # ------------------------------------------------------------------

    def get_recall_entries(self, session_id: UUID) -> list[RecallEntry]:
        return self._recall.get_entries(session_id)

    def add_recall_entry(self, entry: RecallEntry) -> RecallEntry:
        return self._recall.add_entry(entry)

    def get_expired_recall_entries(self, session_id: UUID) -> list[RecallEntry]:
        return self._recall.get_expired_entries(session_id)

    # ------------------------------------------------------------------
    # Archival memory
    # ------------------------------------------------------------------

    def add_archival_entry(self, entry: ArchivalEntry) -> ArchivalEntry:
        return self._archival.add_entry(entry)

    def search_archival(
        self, session_id: UUID, query_embedding: list[float], top_k: int = 10
    ) -> list[ArchivalEntry]:
        return self._archival.search(session_id, query_embedding, top_k)

    # ------------------------------------------------------------------
    # Snapshot (for context assembly)
    # ------------------------------------------------------------------

    def snapshot(self, session_id: UUID) -> MemorySnapshot:
        return MemorySnapshot(
            session_id=session_id,
            core_memory=self.get_core_memory(session_id),
            message_buffer=self.get_message_buffer(session_id),
            recall_entries=self.get_recall_entries(session_id),
        )
