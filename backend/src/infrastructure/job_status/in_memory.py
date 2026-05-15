"""Infrastructure layer - in-memory job status repository implementation.
Concrete implementation of job status tracking ports using in-memory storage.
"""
from typing import Optional, Dict, Any
from backend.src.domain.ports import JobStatusRepositoryPort


class InMemoryJobStatusRepository(JobStatusRepositoryPort):
    """In-memory job status repository implementation for development/testing."""

    def __init__(self):
        self._storage = {}

    def set_status(self, job_id: str, status: Dict[str, Any]) -> None:
        """Set the status for a job."""
        self._storage[job_id] = {
            "status": status.get("status", "pending"),
            "mode": status.get("mode"),
            "transcription": status.get("transcription"),
            "summary": status.get("summary"),
            "error": status.get("error"),
            "created_at": status.get("created_at"),
        }

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status for a job."""
        return self._storage.get(job_id)

    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all jobs for debugging purposes."""
        return self._storage.copy()