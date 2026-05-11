"""
Application layer – use cases.
Defines specific business operations the application can perform.
"""

from __future__ import annotations

from uuid import uuid4
from typing import Optional

from backend.src.domain.services import TranscriptionService
from backend.src.domain.entities import TranscriptionJob
from backend.src.domain.exceptions import AudioValidationError


class ProcessAudioUseCase:
    """Use case: Process an audio file through transcription pipeline."""

    def __init__(self, transcription_service: TranscriptionService):
        self.transcription_service = transcription_service

    def execute(
        self,
        audio_path: str,
        mode: str,
        email: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> dict:
        """Execute audio processing."""
        if job_id is None:
            job_id = str(uuid4())

        audio_filename = audio_path.split("/")[-1]

        job = TranscriptionJob(
            job_id=job_id,
            audio_filename=audio_filename,
            audio_path=audio_path,
            mode=mode,
            email=email,
        )

        try:
            result = self.transcription_service.process_audio(job)
            return {
                "status": result.success,
                "job_id": result.job_id,
                "transcription": result.transcription_text,
                "summary": result.summary_output,
                "mode": result.mode,
            }
        except AudioValidationError as e:
            return {
                "status": "error",
                "error_type": "validation_error",
                "job_id": job_id,
                "error": str(e),
                "validation_result": e.validation_result,
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "processing_error",
                "job_id": job_id,
                "error": str(e),
            }


class ProcessTextUseCase:
    """Use case: Process existing text through summarization."""

    def __init__(self, transcription_service: TranscriptionService):
        self.transcription_service = transcription_service

    def execute(
        self,
        text: str,
        mode: str,
        filename: str,
        email: Optional[str] = None,
        job_id: Optional[str] = None,
        save_files: bool = True,
    ) -> dict:
        """Execute text processing."""
        if job_id is None:
            job_id = str(uuid4())

        job = TranscriptionJob(
            job_id=job_id,
            audio_filename=filename,
            audio_path=None,
            mode=mode,
            email=email,
        )

        original_setting = self.transcription_service.save_files
        self.transcription_service.save_files = save_files

        try:
            result = self.transcription_service.process_text(job, text)
            return {
                "status": result.success,
                "job_id": result.job_id,
                "transcription": result.transcription_text,
                "markdown": result.summary_output,
                "mode": result.mode,
            }
        finally:
            self.transcription_service.save_files = original_setting


class GetJobStatusUseCase:
    """Use case: Get job status."""

    def __init__(self, job_repo):
        self.job_repo = job_repo

    def execute(self, job_id: str) -> dict:
        """Get status of a job."""
        status = self.job_repo.get_status(job_id)
        return status or {"status": "not_found", "job_id": job_id}