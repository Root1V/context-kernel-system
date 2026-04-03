"""Core memory service — always-in-prompt, token-bounded memory blocks."""
from __future__ import annotations

from uuid import UUID

from .models import CoreMemoryBlock


class CoreMemoryService:
    """Manages core memory blocks with token-budget eviction.

    Uses in-memory storage by default; wire a DB repository via *repo* for
    persistence (done in the storage integration task).
    """

    def __init__(self, max_tokens: int = 2000, repo=None) -> None:
        self._max_tokens = max_tokens
        self._repo = repo
        self._store: dict[str, list[CoreMemoryBlock]] = {}  # session_id -> blocks

    def get_core_memory(self, session_id: UUID) -> list[CoreMemoryBlock]:
        return list(self._store.get(str(session_id), []))

    def total_tokens(self, session_id: UUID) -> int:
        return sum(b.token_count for b in self.get_core_memory(session_id))

    def add_block(self, block: CoreMemoryBlock) -> CoreMemoryBlock:
        key = str(block.session_id)
        blocks = list(self._store.get(key, []))
        current_tokens = sum(b.token_count for b in blocks)

        # Enforce budget: evict the least-important existing block only if
        # the incoming block has higher importance. If the new block is the
        # least important, silently drop it.
        while current_tokens + block.token_count > self._max_tokens and blocks:
            blocks.sort(key=lambda b: b.importance_score)
            if blocks[0].importance_score >= block.importance_score:
                # New block is less important than everything — don't add it.
                return block
            evicted = blocks.pop(0)
            current_tokens -= evicted.token_count

        if current_tokens + block.token_count <= self._max_tokens:
            blocks.append(block)
            self._store[key] = blocks
        return block

    def remove_block(self, session_id: UUID, block_id: UUID) -> None:
        key = str(session_id)
        self._store[key] = [
            b for b in self._store.get(key, []) if b.id != block_id
        ]
