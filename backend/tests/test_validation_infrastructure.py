"""
Tests for validation infrastructure implementations.
Covers audio validation, file validation, and data validation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os
from backend.src.infrastructure.validation import FFmpegAudioValidator, FileValidator


class TestFFmpegAudioValidator:
    """Test FFmpeg audio validator implementation."""

    def test_init(self):
        """Test FFmpegAudioValidator initialization."""
        validator = FFmpegAudioValidator()
        assert validator is not None

    @patch('os.path.exists')
    def test_validate_existing_file(self, mock_exists):
        """Test validation of existing file."""
        mock_exists.return_value = True
        
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/audio.mp3")
        
        # Should return valid result with metadata
        assert result["valid"] is True
        assert result["issues"] == []
        assert "metadata" in result
        assert "size_bytes" in result["metadata"]

    @patch('os.path.exists')
    def test_validate_nonexistent_file(self, mock_exists):
        """Test validation of non-existent file."""
        mock_exists.return_value = False
        
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/nonexistent.mp3")
        
        # Should return invalid result
        assert result["valid"] is False
        assert "File not found" in result["issues"]
        assert result["warnings"] == []

    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_validate_file_with_size(self, mock_getsize, mock_exists):
        """Test validation with file size information."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # 1KB
        
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/audio.mp3")
        
        assert result["valid"] is True
        assert result["metadata"]["size_bytes"] == 1024

    @patch('os.path.exists')
    def test_validate_with_exception(self, mock_exists):
        """Test validation with exception during file access."""
        mock_exists.side_effect = Exception("Permission denied")
        
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/audio.mp3")
        
        # Should return valid with warning
        assert result["valid"] is True
        assert result["issues"] == []
        assert "Validation check failed" in result["warnings"][0]

    @patch('os.path.exists')
    def test_validate_large_file_warning(self, mock_exists):
        """Test validation with large file warning."""
        mock_exists.return_value = True
        
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/large_audio.mp3")
        
        # Should return valid with warnings
        assert result["valid"] is True
        assert "too long" in result["warnings"][0].lower()

    @patch('os.path.exists')
    def test_validate_small_file_warning(self, mock_exists):
        """Test validation with small file warning."""
        mock_exists.return_value = True
        
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/small_audio.mp3")
        
        # Should return valid with warnings
        assert result["valid"] is True
        assert "too short" in result["warnings"][0].lower()


class TestFileValidator:
    """Test file validator implementation."""

    def test_init(self):
        """Test FileValidator initialization."""
        validator = FileValidator()
        assert validator is not None

    def test_validate_file_exists(self):
        """Test file existence validation."""
        with tempfile.NamedTemporaryFile() as tmp:
            validator = FileValidator()
            result = validator.validate_file_exists(tmp.name)
            
            assert result is True

    def test_validate_file_not_exists(self):
        """Test file existence validation for non-existent file."""
        validator = FileValidator()
        result = validator.validate_file_exists("/nonexistent/file.txt")
        
        assert result is False

    def test_validate_file_extension(self):
        """Test file extension validation."""
        validator = FileValidator()
        
        # Valid extensions
        assert validator.validate_file_extension("file.mp3") is True
        assert validator.validate_file_extension("file.wav") is True
        assert validator.validate_file_extension("file.flac") is True
        assert validator.validate_file_extension("file.m4a") is True
        
        # Invalid extensions
        assert validator.validate_file_extension("file.txt") is False
        assert validator.validate_file_extension("file.pdf") is False
        assert validator.validate_file_extension("file.jpg") is False

    def test_validate_file_extension_custom(self):
        """Test file extension validation with custom extensions."""
        validator = FileValidator(allowed_extensions=[".txt", ".csv", ".json"])
        
        assert validator.validate_file_extension("file.txt") is True
        assert validator.validate_file_extension("file.csv") is True
        assert validator.validate_file_extension("file.json") is True
        assert validator.validate_file_extension("file.mp3") is False

    def test_validate_file_size_min(self):
        """Test minimum file size validation."""
        with tempfile.NamedTemporaryFile() as tmp:
            # Write some content
            tmp.write(b"Hello World")
            tmp.flush()
            
            validator = FileValidator(min_size=5)  # 5 bytes
            result = validator.validate_file_size(tmp.name)
            
            assert result is True

    def test_validate_file_size_max(self):
        """Test maximum file size validation."""
        with tempfile.NamedTemporaryFile() as tmp:
            # Write large content (1MB)
            tmp.write(b"x" * 1024 * 1024)
            tmp.flush()
            
            validator = FileValidator(max_size=2 * 1024 * 1024)  # 2MB
            result = validator.validate_file_size(tmp.name)
            
            assert result is True

    def test_validate_file_size_too_small(self):
        """Test file size validation for file too small."""
        with tempfile.NamedTemporaryFile() as tmp:
            # Write small content
            tmp.write(b"Hi")
            tmp.flush()
            
            validator = FileValidator(min_size=10)  # 10 bytes
            result = validator.validate_file_size(tmp.name)
            
            assert result is False

    def test_validate_file_size_too_large(self):
        """Test file size validation for file too large."""
        with tempfile.NamedTemporaryFile() as tmp:
            # Write large content (2MB)
            tmp.write(b"x" * 2 * 1024 * 1024)
            tmp.flush()
            
            validator = FileValidator(max_size=1024 * 1024)  # 1MB
            result = validator.validate_file_size(tmp.name)
            
            assert result is False

    def test_validate_file_permissions_read(self):
        """Test file read permissions validation."""
        with tempfile.NamedTemporaryFile() as tmp:
            validator = FileValidator()
            result = validator.validate_file_permissions(tmp.name, "read")
            
            assert result is True

    def test_validate_file_permissions_write(self):
        """Test file write permissions validation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            validator = FileValidator()
            result = validator.validate_file_permissions(tmp_path, "write")
            
            assert result is True
        finally:
            os.unlink(tmp_path)

    def test_validate_file_permissions_no_access(self):
        """Test file permissions validation for no access."""
        # Create a file with no read permissions (this might not work on all systems)
        validator = FileValidator()
        result = validator.validate_file_permissions("/root/readonly.txt", "read")
        
        # This will likely be False on most systems
        assert result is False

    def test_validate_audio_format(self):
        """Test audio format validation."""
        validator = FileValidator()
        
        # Valid audio formats
        assert validator.validate_audio_format("file.mp3") is True
        assert validator.validate_audio_format("file.wav") is True
        assert validator.validate_audio_format("file.flac") is True
        assert validator.validate_audio_format("file.m4a") is True
        assert validator.validate_audio_format("file.ogg") is True
        
        # Invalid audio formats
        assert validator.validate_audio_format("file.txt") is False
        assert validator.validate_audio_format("file.pdf") is False
        assert validator.validate_audio_format("file.jpg") is False

    def test_validate_audio_duration(self):
        """Test audio duration validation (mocked)."""
        validator = FileValidator()
        
        # Mock duration validation
        with patch.object(validator, '_get_audio_duration', return_value=120):
            result = validator.validate_audio_duration("/path/to/audio.mp3", min_duration=60, max_duration=180)
            assert result is True
            
            result = validator.validate_audio_duration("/path/to/audio.mp3", min_duration=180, max_duration=300)
            assert result is False

    def test_validate_audio_quality(self):
        """Test audio quality validation (mocked)."""
        validator = FileValidator()
        
        # Mock quality validation
        with patch.object(validator, '_get_audio_quality', return_value="high"):
            result = validator.validate_audio_quality("/path/to/audio.mp3", min_quality="medium")
            assert result is True
            
            result = validator.validate_audio_quality("/path/to/audio.mp3", min_quality="lossless")
            assert result is False

    def test_comprehensive_validation(self):
        """Test comprehensive file validation."""
        with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
            # Write some content
            tmp.write(b"audio content")
            tmp.flush()
            
            validator = FileValidator(
                allowed_extensions=[".mp3", ".wav"],
                min_size=5,
                max_size=1024 * 1024  # 1MB
            )
            
            result = validator.comprehensive_validation(tmp.name)
            
            assert result["valid"] is True
            assert result["issues"] == []
            assert "metadata" in result

    def test_comprehensive_validation_with_issues(self):
        """Test comprehensive file validation with issues."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            # Write small content
            tmp.write(b"small")
            tmp.flush()
            
            validator = FileValidator(
                allowed_extensions=[".mp3", ".wav"],
                min_size=10,
                max_size=1024 * 1024
            )
            
            result = validator.comprehensive_validation(tmp.name)
            
            assert result["valid"] is False
            assert len(result["issues"]) > 0
            assert "extension" in str(result["issues"][0]).lower()