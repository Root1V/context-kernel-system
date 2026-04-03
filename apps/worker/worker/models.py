"""Job Pydantic model — schema-backed, persisted before execution."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import auto, Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"


class JobType(str, Enum):
    compaction = "compaction"
    archival_promotion = "archival_promotion"


class Job(BaseModel):
    """A background job dispatched by the orchestrator and claimed by the worker."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_type: JobType
    session_id: str
    status: JobStatus = JobStatus.pending
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    claimed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
