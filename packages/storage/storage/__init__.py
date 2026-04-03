"""storage — public interface for database access."""
from __future__ import annotations

from .db import Base, get_session, init_db
from .models import (
    ArchivalEntry,
    CoreMemoryBlock,
    Job,
    RecallEntry,
    Session,
    SessionStateRow,
    TaskStateRow,
)
from .repositories.context_assemblies import ContextAssemblyRepository, ContextAssemblyRow
from .repositories.documents import DocumentChunkRow, DocumentRepository
from .repositories.memory_blocks import ArchivalRepository, CoreMemoryRepository, RecallRepository
from .repositories.sessions import SessionRepository

__all__ = [
    "init_db",
    "get_session",
    "Base",
    # ORM models
    "Session",
    "SessionStateRow",
    "TaskStateRow",
    "CoreMemoryBlock",
    "RecallEntry",
    "ArchivalEntry",
    "Job",
    "DocumentChunkRow",
    "ContextAssemblyRow",
    # Repositories
    "SessionRepository",
    "CoreMemoryRepository",
    "RecallRepository",
    "ArchivalRepository",
    "DocumentRepository",
    "ContextAssemblyRepository",
]
