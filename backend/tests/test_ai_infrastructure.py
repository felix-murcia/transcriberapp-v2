"""
Tests for AI infrastructure implementations.
Covers Gemini AI summarizer and other AI-related components.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.src.infrastructure.ai import GeminiAISummarizer


class TestGeminiAISummarizer:
    """Test Gemini AI summarizer implementation."""

    def test_init_with_default_model(self):
        """Test GeminiAISummarizer initialization with default model."""
        summarizer = GeminiAISummarizer()
        assert summarizer.model == "gemini-2.5-flash-lite"

    def test_init_with_custom_model(self):
        """Test GeminiAISummarizer initialization with custom model."""
        summarizer = GeminiAISummarizer(model="gemini-2.5-pro")
        assert summarizer.model == "gemini-2.5-pro"

    @patch('backend.src.infrastructure.ai.GeminiAISummarizer._get_client')
    def test_summarize_success(self, mock_get_client):
        """Test successful summarization."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "This is a summary of the transcription."
        mock_client.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        summarizer = GeminiAISummarizer()
        
        # Act
        result = summarizer.summarize("Sample transcription text", "default")
        
        # Assert
        assert result == "This is a summary of the transcription."
        mock_client.generate_content.assert_called_once()
        call_args = mock_client.generate_content.call_args[0][0]
        assert "Sample transcription text" in call_args.contents[0].parts[0].text
        assert "default" in call_args.contents[1].parts[0].text

    @patch('backend.src.infrastructure.ai.GeminiAISummarizer._get_client')
    def test_summarize_with_mode_specific_prompt(self, mock_get_client):
        """Test summarization with mode-specific prompts."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Technical summary of the transcription."
        mock_client.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        summarizer = GeminiAISummarizer()
        
        # Act
        result = summarizer.summarize("Sample transcription text", "tecnico")
        
        # Assert
        assert result == "Technical summary of the transcription."
        call_args = mock_client.generate_content.call_args[0][0]
        assert "tecnico" in call_args.contents[1].parts[0].text

    @patch('backend.src.infrastructure.ai.GeminiAISummarizer._get_client')
    def test_summarize_api_error(self, mock_get_client):
        """Test summarization with API error."""
        # Arrange
        mock_client = Mock()
        mock_client.generate_content.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client
        
        summarizer = GeminiAISummarizer()
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            summarizer.summarize("Sample text", "default")
        assert "API Error" in str(exc_info.value)

    @patch('backend.src.infrastructure.ai.GeminiAISummarizer._get_client')
    def test_summarize_empty_text(self, mock_get_client):
        """Test summarization with empty text."""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Empty transcription summary."
        mock_client.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        summarizer = GeminiAISummarizer()
        
        # Act
        result = summarizer.summarize("", "default")
        
        # Assert
        assert result == "Empty transcription summary."

    def test_get_client_with_api_key(self):
        """Test client creation with API key."""
        with patch('backend.src.infrastructure.ai.genai.GenerativeModel') as mock_model:
            mock_client = Mock()
            mock_model.return_value = mock_client
            
            summarizer = GeminiAISummarizer()
            client = summarizer._get_client()
            
            assert client == mock_client
            mock_model.assert_called_once_with("gemini-2.5-flash-lite")

    def test_get_client_without_api_key(self):
        """Test client creation without API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            summarizer = GeminiAISummarizer()
            with pytest.raises(Exception) as exc_info:
                summarizer._get_client()
            assert "GOOGLE_API_KEY" in str(exc_info.value)