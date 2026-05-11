"""
Application layer – domain service for transcription.
Orchestrates the transcription workflow using injected ports.
"""

from __future__ import annotations

from backend.src.domain.ports import (
    AudioTranscriberPort,
    AudioValidatorPort,
    AudioFileReaderPort,
    OutputFormatterPort,
    JobStatusRepositoryPort,
    AISummarizerPort
)
from backend.src.domain.entities import TranscriptionJob, ProcessingResult
from backend.src.domain.exceptions import AudioValidationError


class TranscriptionService:
    """
    Core domain service for transcription processing.
    Orchestrates the transcription workflow using injected ports.
    """

    def __init__(
        self,
        file_reader: AudioFileReaderPort,
        validator: AudioValidatorPort,
        transcriber: AudioTranscriberPort,
        summarizer: AISummarizerPort,
        formatter: OutputFormatterPort,
        job_repo: JobStatusRepositoryPort,
        save_files: bool = True,
    ):
        self.file_reader = file_reader
        self.validator = validator
        self.transcriber = transcriber
        self.summarizer = summarizer
        self.formatter = formatter
        self.job_repo = job_repo
        self.save_files = save_files

    def process_audio(self, job: TranscriptionJob) -> ProcessingResult:
        """Process an audio file through the complete transcription pipeline."""
        try:
            job.status = "processing"
            self._update_job_status(job)

            # 1. Load audio file
            audio_file = self.file_reader.load(job.audio_path)

            # 2. Validate audio
            validation_result = self.validator.validate(audio_file.path)

            if not validation_result.get("valid", False):
                non_length_issues = [
                    issue for issue in validation_result.get("issues", [])
                    if "demasiado largo" not in issue.lower() and "too long" not in issue.lower()
                ]
                if non_length_issues:
                    raise AudioValidationError(
                        f"Audio not valid: {', '.join(non_length_issues)}",
                        validation_result,
                    )
                validation_result["warnings"] = validation_result.get("warnings", []) + [
                    issue for issue in validation_result.get("issues", [])
                    if "demasiado largo" in issue.lower() or "too long" in issue.lower()
                ]
                validation_result["valid"] = True
                audio_file.is_valid = False

            # 3. Transcribe
            transcription_text, metadata = self.transcriber.transcribe(audio_file.path)
            job.transcription_text = transcription_text

            # 4. Save transcription if enabled
            if self.save_files:
                self.formatter.save_transcription(
                    job.job_id, job.audio_filename, transcription_text
                )

            # 5. Summarize with AI
            summary_output = self.summarizer.summarize(transcription_text, job.mode)
            job.summary_output = summary_output

            # 6. Save output if enabled
            if self.save_files:
                output_path = self.formatter.save_output(
                    job.job_id, job.audio_filename, summary_output, job.mode
                )
            else:
                output_path = None

            # 7. Save metrics
            self.formatter.save_metrics(
                job.job_id, job.audio_filename, summary_output, job.mode
            )

            # Update job status to completed
            job.status = "completed"
            self._update_job_status(job, transcription_text, summary_output)

            return ProcessingResult(
                job_id=job.job_id,
                audio_name=job.audio_filename,
                mode=job.mode,
                transcription_text=transcription_text,
                summary_output=summary_output,
                output_file_path=output_path,
                success=True,
            )

        except AudioValidationError as e:
            job.status = "validation_error"
            job.error_message = str(e)
            self._update_job_status(job, error=str(e), validation_result=e.validation_result)
            raise
        except Exception as e:
            job.status = "error"
            job.error_message = str(e)
            self._update_job_status(job, error=str(e))
            raise

    def process_text(self, job: TranscriptionJob, text: str) -> ProcessingResult:
        """Process existing text through the summarization pipeline."""
        try:
            job.status = "processing"
            self._update_job_status(job)

            if self.save_files:
                self.formatter.save_transcription(job.job_id, job.audio_filename, text)

            # Summarize with AI
            summary_output = self.summarizer.summarize(text, job.mode)
            job.summary_output = summary_output

            if self.save_files:
                output_path = self.formatter.save_output(
                    job.job_id, job.audio_filename, summary_output, job.mode
                )
            else:
                output_path = None

            # Save metrics
            self.formatter.save_metrics(
                job.job_id, job.audio_filename, summary_output, job.mode
            )

            # Update job status
            job.status = "completed"
            self._update_job_status(job, text, summary_output)

            return ProcessingResult(
                job_id=job.job_id,
                audio_name=job.audio_filename,
                mode=job.mode,
                transcription_text=text,
                summary_output=summary_output,
                output_file_path=output_path,
                success=True,
            )

        except Exception as e:
            job.status = "error"
            job.error_message = str(e)
            self._update_job_status(job, error=str(e))
            raise

    def _update_job_status(
        self,
        job: TranscriptionJob,
        transcription: str = None,
        summary: str = None,
        error: str = None,
        validation_result: dict = None,
    ) -> None:
        """Update job status in repository."""
        status = {
            "status": job.status,
            "mode": job.mode,
        }
        if transcription is not None:
            status["transcription"] = transcription
        if summary is not None:
            status["summary"] = summary
        if error is not None:
            status["error"] = error
        if validation_result is not None:
            status["validation_result"] = validation_result
        self.job_repo.set_status(job.job_id, status)
