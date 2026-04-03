"""Session and session-state repository."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Session, SessionStateRow


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def get_or_create(self, session_id: uuid.UUID) -> Session:
        result = await self._db.execute(select(Session).where(Session.id == session_id))
        row = result.scalar_one_or_none()
        if row is None:
            row = Session(id=session_id)
            self._db.add(row)
            await self._db.flush()
        return row

    async def get_state(self, session_id: uuid.UUID) -> SessionStateRow | None:
        result = await self._db.execute(
            select(SessionStateRow).where(SessionStateRow.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def upsert_state(self, session_id: uuid.UUID, **fields) -> SessionStateRow:
        row = await self.get_state(session_id)
        if row is None:
            row = SessionStateRow(session_id=session_id, **fields)
            self._db.add(row)
        else:
            for k, v in fields.items():
                setattr(row, k, v)
            row.updated_at = datetime.utcnow()
        await self._db.flush()
        return row
