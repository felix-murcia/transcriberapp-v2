"""
In-memory job status repository implementation.
"""

from typing import Dict, Optional
from backend.src.domain.ports import JobStatusRepositoryPort
from backend.src.domain.entities import TranscriptionJob


class InMemoryJobStatusRepository(JobStatusRepositoryPort):
    """In-memory implementation of job status repository."""

    def __init__(self):
        self._jobs: Dict[str, TranscriptionJob] = {}

    def save(self, job: TranscriptionJob) -> None:
        """Save job status to memory."""
        self._jobs[job.job_id] = job

    def find_by_id(self, job_id: str) -> Optional[TranscriptionJob]:
        """Find job by ID."""
        return self._jobs.get(job_id)

    def find_all(self) -> list[TranscriptionJob]:
        """Find all jobs."""
        return list(self._jobs.values())

    def delete(self, job_id: str) -> bool:
        """Delete job by ID."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def update_status(self, job_id: str, status: str) -> bool:
        """Update job status."""
        if job_id in self._jobs:
            self._jobs[job_id].status = status
            return True
        return False