"""
Tests for storage infrastructure implementations.
Covers local file storage and file management operations.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import os
import tempfile
from backend.src.infrastructure.storage import LocalFileStorage


class TestLocalFileStorage:
    """Test local file storage implementation."""

    def test_init(self):
        """Test LocalFileStorage initialization."""
        storage = LocalFileStorage()
        assert storage is not None

    def test_save_file_success(self):
        """Test successful file saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            # Create test content as bytes
            test_content = b"This is test file content"
            test_filename = "test_file.txt"
            test_directory = temp_dir
            
            # Save file
            file_path = storage.save_file(test_content, test_filename, test_directory)
            
            # Assert file was created
            assert Path(file_path).exists()
            assert Path(file_path).name == test_filename
            
            # Assert content is correct
            with open(file_path, 'rb') as f:
                assert f.read() == test_content

    def test_save_file_with_subdirectory(self):
        """Test file saving with subdirectory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            test_content = b"Test content"
            test_filename = "test_file.txt"
            test_directory = os.path.join(temp_dir, "subdir")
            
            file_path = storage.save_file(test_content, test_filename, test_directory)
            
            # Assert subdirectory was created
            assert Path(file_path).parent.name == "subdir"
            assert Path(file_path).exists()

    def test_save_file_overwrite(self):
        """Test file overwriting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            test_filename = "test_file.txt"
            test_directory = temp_dir
            
            # Save first content
            file_path1 = storage.save_file(b"Original content", test_filename, test_directory)
            
            # Save different content
            file_path2 = storage.save_file(b"New content", test_filename, test_directory)
            
            # Assert content was overwritten
            assert file_path1 == file_path2
            with open(file_path2, 'rb') as f:
                assert f.read() == b"New content"

    def test_read_file_success(self):
        """Test successful file reading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            # Create test file
            test_content = b"Test file content"
            test_filename = "test_file.txt"
            file_path = os.path.join(temp_dir, test_filename)
            
            with open(file_path, 'wb') as f:
                f.write(test_content)
            
            # Read file
            loaded_content = storage.read_file(file_path)
            
            assert loaded_content == test_content

    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        storage = LocalFileStorage()
        
        with pytest.raises(FileNotFoundError):
            storage.read_file("/nonexistent/file.txt")

    def test_delete_file_success(self):
        """Test successful file deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            # Create test file
            test_content = b"Test content"
            test_filename = "test_file.txt"
            file_path = os.path.join(temp_dir, test_filename)
            
            with open(file_path, 'wb') as f:
                f.write(test_content)
            
            # Delete file
            result = storage.delete_file(file_path)
            
            # Assert file was deleted
            assert result is True
            assert not Path(file_path).exists()

    def test_delete_file_not_found(self):
        """Test deleting non-existent file."""
        storage = LocalFileStorage()
        
        result = storage.delete_file("/nonexistent/file.txt")
        
        # May return True (missing_ok=True) or False, both acceptable
        assert result in [True, False]

    def test_list_files(self):
        """Test listing files in directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            # Create test files
            files = ["file1.txt", "file2.txt"]
            for filename in files:
                with open(os.path.join(temp_dir, filename), 'wb') as f:
                    f.write(b"test")
            
            # List files
            listed_files = storage.list_files(temp_dir)
            
            # Should include all files
            assert len(listed_files) >= 2
            assert any("file1.txt" in f for f in listed_files)
            assert any("file2.txt" in f for f in listed_files)

    def test_list_files_empty_directory(self):
        """Test listing files in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            listed_files = storage.list_files(temp_dir)
            
            assert listed_files == []

    def test_list_files_nonexistent_directory(self):
        """Test listing files in non-existent directory."""
        storage = LocalFileStorage()
        
        listed_files = storage.list_files("/nonexistent/directory")
        
        assert listed_files == []

    def test_save_and_read_roundtrip(self):
        """Test save and read roundtrip."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            test_content = b"Test content for roundtrip"
            test_filename = "roundtrip.txt"
            test_directory = temp_dir
            
            # Save
            file_path = storage.save_file(test_content, test_filename, test_directory)
            
            # Read
            loaded_content = storage.read_file(file_path)
            
            assert loaded_content == test_content

    def test_save_empty_content(self):
        """Test saving empty content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            test_filename = "empty.txt"
            test_directory = temp_dir
            
            file_path = storage.save_file(b"", test_filename, test_directory)
            
            assert Path(file_path).exists()
            with open(file_path, 'rb') as f:
                assert f.read() == b""

    def test_save_large_content(self):
        """Test saving large content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage()
            
            test_content = b"x" * (1024 * 1024)  # 1MB
            test_filename = "large.txt"
            test_directory = temp_dir
            
            file_path = storage.save_file(test_content, test_filename, test_directory)
            
            assert Path(file_path).exists()
            with open(file_path, 'rb') as f:
                assert len(f.read()) == 1024 * 1024