"""
Domain entities for TranscriberApp (copied from legacy).
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class TranscriptionJob:
    """Entity representing a transcription job."""

    job_id: str
    audio_filename: str
    audio_path: Optional[str]
    mode: str
    email: Optional[str]
    status: str = "pending"
    transcription_text: Optional[str] = None
    summary_output: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AudioFile:
    """Value object representing an audio file."""

    path: str
    filename: str
    size_bytes: int
    extension: str
    is_valid: bool = True
    validation_issues: List[str] | None = None
    validation_warnings: List[str] | None = None

    def __post_init__(self) -> None:
        if self.validation_issues is None:
            self.validation_issues = []
        if self.validation_warnings is None:
            self.validation_warnings = []


@dataclass
class ProcessingResult:
    """Value object representing the result of audio processing."""

    job_id: str
    audio_name: str
    mode: str
    transcription_text: Optional[str] = None
    summary_output: Optional[str] = None
    output_file_path: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


@dataclass
class AudioChunk:
    """Entity representing a chunk of audio data for large file uploads."""

    chunk_id: str
    job_id: str
    chunk_index: int
    total_chunks: int
    data: bytes
    filename: str
    extension: str
    is_uploaded: bool = False
    uploaded_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.uploaded_at is None:
            self.uploaded_at = datetime.now()


@dataclass
class ChunkUploadSession:
    """Entity representing a chunk upload session."""

    job_id: str
    filename: str
    total_size: int
    total_chunks: int
    uploaded_chunks: int = 0
    is_completed: bool = False
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()
