"""Background worker — job poller.

Polls for pending jobs, claims them, dispatches to the appropriate handler,
and marks them complete or failed. Designed to run as a separate process
outside the turn-time API path.

Usage:
    python -m apps.worker.worker.main
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

from .models import Job, JobStatus, JobType
from .jobs.compaction import handle_compaction
from .jobs.memory_cleanup import handle_archival_promotion

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory job queue (production: replace with DB-backed storage queue)
# ---------------------------------------------------------------------------

_JOB_QUEUE: list[Job] = []


def enqueue_job(job: Job) -> None:
    """Dispatch a job to the queue. Called by the orchestrator."""
    _JOB_QUEUE.append(job)


def _claim_next_job() -> Optional[Job]:
    """Claim the next pending job from the queue (FIFO)."""
    for job in _JOB_QUEUE:
        if job.status == JobStatus.pending:
            job.status = JobStatus.running
            job.claimed_at = datetime.utcnow()
            return job
    return None


def _dispatch(job: Job) -> Job:
    """Route a claimed job to its handler."""
    if job.job_type == JobType.compaction:
        return handle_compaction(job)
    elif job.job_type == JobType.archival_promotion:
        return handle_archival_promotion(job)
    else:
        job.status = JobStatus.failed
        job.error = f"Unknown job type: {job.job_type}"
        return job


def run_once() -> int:
    """Process all currently pending jobs. Returns number of jobs processed."""
    processed = 0
    while True:
        job = _claim_next_job()
        if job is None:
            break
        try:
            job = _dispatch(job)
        except Exception as exc:
            job.status = JobStatus.failed
            job.error = str(exc)
            logger.exception("Job %s failed: %s", job.job_id, exc)
        else:
            logger.info("Job %s → %s", job.job_id, job.status)
        processed += 1
    return processed


def run_forever(poll_interval_seconds: float = 5.0) -> None:
    """Poll for jobs indefinitely. Intended for production deployment."""
    logger.info("Worker started — polling every %.1fs", poll_interval_seconds)
    while True:
        count = run_once()
        if count:
            logger.info("Processed %d job(s)", count)
        time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
