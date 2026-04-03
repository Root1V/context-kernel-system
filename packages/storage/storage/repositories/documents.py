"""Document chunks repository (for retrieval pipeline)."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from datetime import datetime

from ..db import Base

try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_AVAILABLE = True
except ImportError:
    Vector = None  # type: ignore[assignment]
    _VECTOR_AVAILABLE = False


class DocumentChunkRow(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[str] = mapped_column(String(512))
    source_type: Mapped[str] = mapped_column(String(128))  # codebase, file, web, etc.
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    if _VECTOR_AVAILABLE:
        embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=True)


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def add(self, chunk: DocumentChunkRow) -> DocumentChunkRow:
        self._db.add(chunk)
        await self._db.flush()
        return chunk

    async def search_vector(
        self, embedding: list[float], top_k: int, filters: dict | None = None
    ) -> list[DocumentChunkRow]:
        q = select(DocumentChunkRow)
        if filters:
            for key, value in filters.items():
                if hasattr(DocumentChunkRow, key):
                    q = q.where(getattr(DocumentChunkRow, key) == value)
        q = q.order_by(DocumentChunkRow.embedding.l2_distance(embedding)).limit(top_k)
        result = await self._db.execute(q)
        return list(result.scalars().all())
