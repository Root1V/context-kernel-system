from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OpenFileEntry(BaseModel):
    file_path: str
    summary: str
    last_modified: datetime = Field(default_factory=datetime.utcnow)


class OpenFilesState(BaseModel):
    session_id: UUID
    files: list[OpenFileEntry] = Field(default_factory=list)
