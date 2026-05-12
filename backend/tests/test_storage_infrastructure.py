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

    def test_init_with_default_base_dir(self):
        """Test LocalFileStorage initialization with default base directory."""
        storage = LocalFileStorage()
        # Should use current working directory as base
        assert storage.base_dir == Path.cwd()

    def test_init_with_custom_base_dir(self):
        """Test LocalFileStorage initialization with custom base directory."""
        custom_dir = "/custom/storage/path"
        storage = LocalFileStorage(base_dir=custom_dir)
        assert storage.base_dir == Path(custom_dir)

    def test_save_file_success(self):
        """Test successful file saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            # Create test content
            test_content = "This is test file content"
            test_filename = "test_file.txt"
            
            # Save file
            file_path = storage.save_file(test_content, test_filename)
            
            # Assert file was created
            assert Path(file_path).exists()
            assert Path(file_path).name == test_filename
            
            # Assert content is correct
            with open(file_path, 'r') as f:
                assert f.read() == test_content

    def test_save_file_with_subdirectory(self):
        """Test file saving with subdirectory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            test_content = "Test content"
            test_filename = "subdir/test_file.txt"
            
            file_path = storage.save_file(test_content, test_filename)
            
            # Assert subdirectory was created
            assert Path(file_path).parent.name == "subdir"
            assert Path(file_path).exists()

    def test_save_file_overwrite(self):
        """Test file overwriting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            test_filename = "test_file.txt"
            
            # Save first content
            storage.save_file("Original content", test_filename)
            
            # Save different content
            file_path = storage.save_file("New content", test_filename)
            
            # Assert content was overwritten
            with open(file_path, 'r') as f:
                assert f.read() == "New content"

    def test_load_file_success(self):
        """Test successful file loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            # Create test file
            test_content = "Test file content"
            test_filename = "test_file.txt"
            file_path = Path(temp_dir) / test_filename
            
            with open(file_path, 'w') as f:
                f.write(test_content)
            
            # Load file
            loaded_content = storage.load_file(test_filename)
            
            assert loaded_content == test_content

    def test_load_file_not_found(self):
        """Test loading non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            with pytest.raises(FileNotFoundError):
                storage.load_file("non_existent_file.txt")

    def test_load_file_with_subdirectory(self):
        """Test loading file from subdirectory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            # Create file in subdirectory
            test_content = "Subdirectory content"
            subdir = Path(temp_dir) / "subdir"
            subdir.mkdir()
            file_path = subdir / "test_file.txt"
            
            with open(file_path, 'w') as f:
                f.write(test_content)
            
            # Load file
            loaded_content = storage.load_file("subdir/test_file.txt")
            
            assert loaded_content == test_content

    def test_delete_file_success(self):
        """Test successful file deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            # Create test file
            test_content = "Test content"
            test_filename = "test_file.txt"
            file_path = Path(temp_dir) / test_filename
            
            with open(file_path, 'w') as f:
                f.write(test_content)
            
            # Delete file
            result = storage.delete_file(test_filename)
            
            # Assert file was deleted
            assert result is True
            assert not file_path.exists()

    def test_delete_file_not_found(self):
        """Test deleting non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            result = storage.delete_file("non_existent_file.txt")
            
            assert result is False

    def test_file_exists(self):
        """Test file existence check."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            # Create test file
            test_filename = "test_file.txt"
            file_path = Path(temp_dir) / test_filename
            
            with open(file_path, 'w') as f:
                f.write("test")
            
            # Check existence
            assert storage.file_exists(test_filename) is True
            
            # Check non-existent file
            assert storage.file_exists("non_existent.txt") is False

    def test_get_file_info(self):
        """Test getting file information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            # Create test file
            test_content = "Test content" * 100  # Make it larger
            test_filename = "test_file.txt"
            file_path = Path(temp_dir) / test_filename
            
            with open(file_path, 'w') as f:
                f.write(test_content)
            
            # Get file info
            file_info = storage.get_file_info(test_filename)
            
            assert file_info["filename"] == test_filename
            assert file_info["size"] == len(test_content.encode('utf-8'))
            assert file_info["path"] == str(file_path)
            assert "created_at" in file_info
            assert "modified_at" in file_info

    def test_get_file_info_not_found(self):
        """Test getting info for non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            with pytest.raises(FileNotFoundError):
                storage.get_file_info("non_existent_file.txt")

    def test_list_files(self):
        """Test listing files in directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            # Create test files
            files = ["file1.txt", "file2.txt", "subdir/file3.txt"]
            for filename in files:
                file_path = Path(temp_dir) / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write("test")
            
            # List files
            listed_files = storage.list_files()
            
            # Should include all files
            assert len(listed_files) >= 3
            assert any(f["filename"] == "file1.txt" for f in listed_files)
            assert any(f["filename"] == "file2.txt" for f in listed_files)
            assert any(f["filename"] == "subdir/file3.txt" for f in listed_files)

    def test_list_files_empty_directory(self):
        """Test listing files in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            listed_files = storage.list_files()
            
            assert listed_files == []

    def test_create_directory(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            # Create directory
            dir_path = storage.create_directory("test_dir")
            
            # Assert directory was created
            assert Path(dir_path).exists()
            assert Path(dir_path).is_dir()
            assert Path(dir_path).name == "test_dir"

    def test_create_directory_nested(self):
        """Test nested directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorage(base_dir=temp_dir)
            
            # Create nested directory
            dir_path = storage.create_directory("nested/deep/dir")
            
            # Assert nested directory was created
            assert Path(dir_path).exists()
            assert Path(dir_path).is_dir()
            assert Path(dir_path).name == "dir"