"""
Tests for application use cases.
Covers all scenarios: success, validation errors, processing errors.
"""
import pytest
from unittest.mock import Mock, patch
from backend.src.application.use_cases import ProcessAudioUseCase, ProcessTextUseCase, GetJobStatusUseCase
from backend.src.domain.entities import TranscriptionJob
from backend.src.domain.exceptions import AudioValidationError


def test_process_audio_success():
    """Test successful audio processing."""
    # Arrange
    mock_service = Mock()
    mock_service.process_audio.return_value = Mock(
        success=True,
        job_id="test-job",
        transcription_text="test transcription",
        summary_output="test summary",
        mode="test-mode",
    )
    use_case = ProcessAudioUseCase(mock_service)

    # Act
    result = use_case.execute("/test/path", "test-mode")

    # Assert
    assert result["status"] == True
    assert result["job_id"] == "test-job"
    assert result["transcription"] == "test transcription"
    assert result["summary"] == "test summary"
    assert result["mode"] == "test-mode"


def test_process_audio_validation_error():
    """Test audio processing with validation error."""
    # Arrange
    mock_service = Mock()
    mock_service.process_audio.side_effect = AudioValidationError(
        "Validation failed",
        validation_result={"valid": False, "issues": ["too long"]},
    )
    use_case = ProcessAudioUseCase(mock_service)

    job = TranscriptionJob(
        job_id="test-job",
        audio_filename="test.mp3",
        audio_path="/test/path",
        mode="test-mode",
        email=None,
    )

    # Act
    result = use_case.execute("/test/path", "test-mode")

    # Assert
    assert result["status"] == "error"
    assert result["error_type"] == "validation_error"
    assert "Validation failed" in result["error"]


def test_process_audio_processing_error():
    """Test audio processing with unexpected error."""
    # Arrange
    mock_service = Mock()
    mock_service.process_audio.side_effect = Exception("Unexpected error")
    use_case = ProcessAudioUseCase(mock_service)

    job = TranscriptionJob(
        job_id="test-job",
        audio_filename="test.mp3",
        audio_path="/test/path",
        mode="test-mode",
        email=None,
    )

    # Act
    result = use_case.execute("/test/path", "test-mode")

    # Assert
    assert result["status"] == "error"
    assert result["error_type"] == "processing_error"
    assert "Unexpected error" in result["error"]


def test_process_text_success():
    """Test successful text processing."""
    # Arrange
    mock_service = Mock()
    mock_service.process_text.return_value = Mock(
        success=True,
        job_id="test-job",
        transcription_text="test transcription",
        summary_output="test summary",
        mode="test-mode",
    )
    use_case = ProcessTextUseCase(mock_service)

    # Act
    result = use_case.execute("test text", "test-mode", filename="test.txt")

    # Assert
    assert result["status"] == True
    assert result["job_id"] == "test-job"
    assert result["transcription"] == "test transcription"
    assert result["markdown"] == "test summary"
    assert result["mode"] == "test-mode"


def test_get_job_status_success():
    """Test successful job status retrieval."""
    # Arrange
    mock_repo = Mock()
    mock_repo.get_status.return_value = {
        "status": "completed",
        "mode": "test-mode",
        "transcription": "test transcription",
        "summary": "test summary",
        "error": None,
    }
    use_case = GetJobStatusUseCase(mock_repo)

    # Act
    result = use_case.execute("test-job")

    # Assert
    assert result["status"] == "completed"
    assert result["mode"] == "test-mode"
    assert result["transcription"] == "test transcription"
    assert result["summary"] == "test summary"
    assert result["error"] is None