"""Infrastructure layer - job status repository implementations.
Concrete implementations of job status tracking ports using SQLAlchemy.
"""
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from backend.src.domain.ports import JobStatusRepositoryPort
from backend.src.infrastructure.persistence.models import Transcription
from backend.src.infrastructure.persistence import get_session


class SQLAlchemyJobStatusRepository(JobStatusRepositoryPort):
    """SQLAlchemy-based job status repository implementation for production."""

    def __init__(self, session: Session = None):
        self.session = session or get_session()

    def set_status(self, job_id: str, status: Dict[str, Any]) -> None:
        """Set the status for a job."""
        transcription = self.session.query(Transcription).filter_by(job_id=job_id).first()
        if transcription:
            transcription.status = status.get("status", transcription.status)
            transcription.transcription_text = status.get("transcription")
            transcription.summary_output = status.get("summary")
            transcription.error_message = status.get("error")
            self.session.commit()
        else:
            transcription = Transcription(
                job_id=job_id,
                status=status.get("status", "pending"),
                transcription_text=status.get("transcription"),
                summary_output=status.get("summary"),
                error_message=status.get("error"),
            )
            self.session.add(transcription)
            self.session.commit()

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status for a job."""
        transcription = self.session.query(Transcription).filter_by(job_id=job_id).first()
        if transcription:
            return {
                "status": transcription.status,
                "mode": transcription.mode,
                "transcription": transcription.transcription_text,
                "summary": transcription.summary_output,
                "error": transcription.error_message,
                "created_at": transcription.created_at.isoformat() if transcription.created_at else None,
            }
        return None

    def clear_all(self) -> None:
        """Clear all job statuses."""
        self.session.query(Transcription).delete()
        self.session.commit()


class InMemoryJobStatusRepository(JobStatusRepositoryPort):
    """In-memory job status repository implementation for development/testing."""

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def set_status(self, job_id: str, status: Dict[str, Any]) -> None:
        """Set the status for a job."""
        self._jobs[job_id] = status

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status for a job."""
        return self._jobs.get(job_id)

    def clear_all(self) -> None:
        """Clear all job statuses."""
        self._jobs.clear()


# Factory function to choose implementation based on environment
_job_status_repo_instance = None


def get_job_status_repository() -> JobStatusRepositoryPort:
    """Get or create the job status repository.
    
    Uses SQLAlchemy for production (DATABASE_URL env var) or in-memory for development.
    """
    global _job_status_repo_instance
    if _job_status_repo_instance is None:
        import os
        if os.getenv("DATABASE_URL") or os.getenv("ENVIRONMENT") == "production":
            _job_status_repo_instance = SQLAlchemyJobStatusRepository()
        else:
            _job_status_repo_instance = InMemoryJobStatusRepository()
    return _job_status_repo_instance