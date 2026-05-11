"""Infrastructure layer - file reading implementations.
Concrete implementations of audio file reading ports.
"""
from pathlib import Path
from backend.src.domain.ports import AudioFileReaderPort
from backend.src.domain.entities import AudioFile


class LocalAudioFileReader(AudioFileReaderPort):
    """Local file system audio file reader implementation."""

    def load(self, audio_path: str) -> AudioFile:
        """Load audio file metadata from local file system."""
        abs_path = Path(audio_path).resolve()

        if not abs_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        file_size = abs_path.stat().st_size
        filename = abs_path.name
        extension = abs_path.suffix.lower() if abs_path.suffix else ""

        return AudioFile(
            path=str(abs_path),
            filename=filename,
            size_bytes=file_size,
            extension=extension,
            is_valid=True,
            validation_issues=[],
            validation_warnings=[],
        )
