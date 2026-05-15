"""
Local audio file reader implementation.
"""

from pathlib import Path
from backend.src.domain.ports import AudioFileReaderPort
from backend.src.domain.entities import AudioFile


class LocalAudioFileReader(AudioFileReaderPort):
    """Local file system audio file reader."""

    def load(self, file_path: str) -> AudioFile:
        """Load audio file from local filesystem."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Get file size
        file_size = path.stat().st_size
        
        # Determine file type from extension
        extension = path.suffix.lower()
        
        return AudioFile(
            path=str(path),
            size=file_size,
            extension=extension,
            is_valid=True,
        )