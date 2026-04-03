"""Repository for core memory blocks, recall entries, and archival entries."""
from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ArchivalEntry, CoreMemoryBlock, RecallEntry


class CoreMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def list(self, session_id: uuid.UUID) -> list[CoreMemoryBlock]:
        result = await self._db.execute(
            select(CoreMemoryBlock)
            .where(CoreMemoryBlock.session_id == session_id)
            .order_by(CoreMemoryBlock.created_at)
        )
        return list(result.scalars().all())

    async def add(self, block: CoreMemoryBlock) -> CoreMemoryBlock:
        self._db.add(block)
        await self._db.flush()
        return block

    async def evict_lowest_scored(self, session_id: uuid.UUID) -> None:
        result = await self._db.execute(
            select(CoreMemoryBlock)
            .where(CoreMemoryBlock.session_id == session_id)
            .order_by(CoreMemoryBlock.importance_score.asc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            await self._db.delete(row)
            await self._db.flush()


class RecallRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def list(self, session_id: uuid.UUID, since_timestamp=None) -> list[RecallEntry]:
        q = select(RecallEntry).where(RecallEntry.session_id == session_id)
        if since_timestamp:
            q = q.where(RecallEntry.created_at >= since_timestamp)
        result = await self._db.execute(q.order_by(RecallEntry.created_at.desc()))
        return list(result.scalars().all())

    async def add(self, entry: RecallEntry) -> RecallEntry:
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def delete(self, entry_id: uuid.UUID) -> None:
        await self._db.execute(
            delete(RecallEntry).where(RecallEntry.id == entry_id)
        )
        await self._db.flush()


class ArchivalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def add(self, entry: ArchivalEntry) -> ArchivalEntry:
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def search(
        self, session_id: uuid.UUID, embedding: list[float], top_k: int = 10
    ) -> list[ArchivalEntry]:
        """Vector similarity search via pgvector <=> operator."""
        result = await self._db.execute(
            select(ArchivalEntry)
            .where(ArchivalEntry.session_id == session_id)
            .order_by(ArchivalEntry.embedding.l2_distance(embedding))
            .limit(top_k)
        )
        return list(result.scalars().all())

    async def exists(self, session_id: uuid.UUID, content_hash: str) -> bool:
        """Idempotency check: returns True if an entry with this hash already exists."""
        result = await self._db.execute(
            select(ArchivalEntry)
            .where(
                ArchivalEntry.session_id == session_id,
                ArchivalEntry.metadata_["content_hash"].as_string() == content_hash,
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
