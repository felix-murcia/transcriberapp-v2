"""
Tests for validation infrastructure implementations.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.src.infrastructure.validation import FFmpegAudioValidator


class TestFFmpegAudioValidator:

    def test_init(self):
        validator = FFmpegAudioValidator()
        assert validator is not None

    @patch('subprocess.run')
    def test_validate_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[STREAM]\ncodec_name=mp3\nduration=120.5\n",
            stderr=""
        )
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/audio.mp3")
        assert result["valid"] is True
        assert result["issues"] == []
        assert "metadata" in result

    @patch('subprocess.run')
    def test_validate_ffprobe_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Invalid data"
        )
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/audio.mp3")
        assert result["valid"] is False
        assert len(result["issues"]) > 0

    @patch('subprocess.run')
    def test_validate_timeout(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffprobe", timeout=30)
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/audio.mp3")
        assert result["valid"] is False
        assert any("timeout" in i.lower() or "Validation timeout" in i for i in result["issues"])

    @patch('subprocess.run')
    def test_validate_ffmpeg_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("ffprobe not found")
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/audio.mp3")
        assert result["valid"] is False
        assert any("FFmpeg" in i or "not found" in i.lower() for i in result["issues"])

    @patch('subprocess.run')
    def test_validate_no_streams(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="duration=10.0\n",
            stderr=""
        )
        validator = FFmpegAudioValidator()
        result = validator.validate("/path/to/audio.mp3")
        assert result["valid"] is False
        assert any("stream" in i.lower() for i in result["issues"])
