"""Infrastructure layer - file storage implementations.
Concrete implementations of file storage ports.
"""
from pathlib import Path
from typing import List
from backend.src.domain.ports import FileStoragePort


class LocalFileStorage(FileStoragePort):
    """Local file system storage implementation."""

    def save_file(self, content: bytes, filename: str, directory: str) -> str:
        """Save a file to local storage."""
        Path(directory).mkdir(parents=True, exist_ok=True)
        file_path = Path(directory) / filename
        with open(file_path, "wb") as f:
            f.write(content)
        return str(file_path)

    def read_file(self, file_path: str) -> bytes:
        """Read a file from local storage."""
        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from local storage."""
        try:
            Path(file_path).unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def list_files(self, directory: str, pattern: str = "*") -> List[str]:
        """List files in a directory."""
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        return [str(p) for p in dir_path.glob(pattern)]
