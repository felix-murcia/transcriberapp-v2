"""
Domain ports (interfaces) for TranscriberApp hexagonal architecture.
Copied from legacy and adjusted import paths.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from .entities import AudioFile


class AudioTranscriberPort(ABC):
    """Port for audio transcription services (driven)."""

    @abstractmethod
    def transcribe(self, audio_path: str) -> tuple[str, Dict[str, Any]]:
        """Transcribe an audio file to text.

        Returns a tuple ``(transcription_text, metadata)``.
        """
        ...


class AISummarizerPort(ABC):
    """Port for AI summarization services (driven)."""

    @abstractmethod
    def summarize(self, text: str, mode: str) -> str:
        """Summarize text using AI agents based on the specified mode."""
        ...

    @abstractmethod
    def get_agent(self, mode: str) -> Any:
        """Get the appropriate agent for the given mode."""
        ...


class AudioValidatorPort(ABC):
    """Port for audio validation services (driven)."""

    @abstractmethod
    def validate(self, audio_path: str) -> Dict[str, Any]:
        """Validate an audio file and return a dict with ``valid`` flag, ``issues`` and ``warnings``."""
        ...


class AudioFileReaderPort(ABC):
    """Port for reading audio files (driven)."""

    @abstractmethod
    def load(self, audio_path: str) -> AudioFile:
        """Load an audio file and return its metadata as :class:`AudioFile`."""
        ...


class OutputFormatterPort(ABC):
    """Port for formatting and persisting output (driven)."""

    @abstractmethod
    def save_transcription(self, job_id: str, audio_name: str, text: str) -> str:
        ...

    @abstractmethod
    def save_output(self, job_id: str, audio_name: str, content: str, mode: str) -> str:
        ...

    @abstractmethod
    def save_metrics(self, job_id: str, audio_name: str, summary: str, mode: str) -> Dict[str, Any]:
        ...


class JobStatusRepositoryPort(ABC):
    """Port for tracking job status (driven)."""

    @abstractmethod
    def set_status(self, job_id: str, status: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def clear_all(self) -> None:
        ...


class JobQueuePort(ABC):
    """Port for background job queue (driven)."""

    @abstractmethod
    def add_task(self, func, *args, **kwargs) -> None:
        ...


class FileStoragePort(ABC):
    """Port for file storage operations (driven)."""

    @abstractmethod
    def save_file(self, content: bytes, filename: str, directory: str) -> str:
        ...
