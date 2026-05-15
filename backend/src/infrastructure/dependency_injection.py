"""Infrastructure layer - dependency injection container.
Factory functions to create and wire all port implementations.
"""
from backend.src.infrastructure.file_processing import LocalAudioFileReader
from backend.src.infrastructure.validation import FFmpegAudioValidator
from backend.src.infrastructure.transcription import GroqAudioTranscriber
from backend.src.infrastructure.ai import GeminiAISummarizer
from backend.src.infrastructure.output import LocalOutputFormatter
from backend.src.infrastructure.storage import LocalFileStorage
from backend.src.infrastructure.queue import FastAPIBackgroundTasksAdapter


def create_transcription_service():
    """Create a fully wired transcription service with all dependencies."""
    from backend.src.domain.services import TranscriptionService
    from backend.src.infrastructure.job_status import get_job_status_repository
    
    # Create all port implementations
    file_reader = LocalAudioFileReader()
    validator = FFmpegAudioValidator()
    transcriber = GroqAudioTranscriber()
    summarizer = GeminiAISummarizer()
    formatter = LocalOutputFormatter()
    job_repo = get_job_status_repository()  # Uses appropriate implementation based on environment
    file_storage = LocalFileStorage()
    
    return TranscriptionService(
        file_reader=file_reader,
        validator=validator,
        transcriber=transcriber,
        summarizer=summarizer,
        formatter=formatter,
        job_repo=job_repo,
        save_files=True,
    )


def get_audio_reader() -> LocalAudioFileReader:
    """Get audio file reader instance."""
    return LocalAudioFileReader()


def get_audio_validator() -> FFmpegAudioValidator:
    """Get audio validator instance."""
    return FFmpegAudioValidator()


def get_transcriber() -> GroqAudioTranscriber:
    """Get audio transcriber instance."""
    return GroqAudioTranscriber()


def get_ai_summarizer() -> GeminiAISummarizer:
    """Get AI summarizer instance."""
    return GeminiAISummarizer()


def get_output_formatter() -> LocalOutputFormatter:
    """Get output formatter instance."""
    return LocalOutputFormatter()


def get_file_storage() -> LocalFileStorage:
    """Get file storage instance."""
    return LocalFileStorage()


def get_background_tasks_adapter(background_tasks=None) -> FastAPIBackgroundTasksAdapter:
    """Get background tasks adapter instance."""
    return FastAPIBackgroundTasksAdapter(background_tasks)