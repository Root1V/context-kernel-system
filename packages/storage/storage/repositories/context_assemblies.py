"""Repository for context assembly audit records (optional tracing)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..db import Base


class ContextAssemblyRow(Base):
    __tablename__ = "context_assemblies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    turn_id: Mapped[str] = mapped_column(String(256))
    model_id: Mapped[str] = mapped_column(String(128))
    payload_preview: Mapped[str] = mapped_column(Text)  # first 500 chars
    token_count: Mapped[int] = mapped_column(default=0)
    truncated: Mapped[bool] = mapped_column(default=False)
    truncated_sections: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContextAssemblyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def record(self, row: ContextAssemblyRow) -> ContextAssemblyRow:
        self._db.add(row)
        await self._db.flush()
        return row
