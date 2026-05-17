"""
Tests for AI infrastructure implementations.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.src.infrastructure.ai import GeminiAISummarizer

FAKE_RESPONSE = {
    "candidates": [{"content": {"parts": [{"text": "Summary text"}]}}]
}


class TestGeminiAISummarizer:

    def test_init(self):
        summarizer = GeminiAISummarizer()
        assert summarizer is not None

    def test_init_with_api_key(self):
        summarizer = GeminiAISummarizer(api_key="test-key")
        assert summarizer is not None

    def test_has_model_attribute(self):
        summarizer = GeminiAISummarizer()
        assert hasattr(summarizer, 'model')

    @patch('requests.post')
    def test_summarize_resumen(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: FAKE_RESPONSE)
        summarizer = GeminiAISummarizer(api_key="test-key")
        result = summarizer.summarize("Sample transcription text", "resumen")
        assert result is not None
        assert isinstance(result, str)

    @patch('requests.post')
    def test_summarize_tecnico(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: FAKE_RESPONSE)
        summarizer = GeminiAISummarizer(api_key="test-key")
        result = summarizer.summarize("Sample transcription text", "tecnico")
        assert result is not None
        assert isinstance(result, str)

    @patch('requests.post')
    def test_summarize_all_modes(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: FAKE_RESPONSE)
        summarizer = GeminiAISummarizer(api_key="test-key")
        modes = ["resumen", "tecnico", "ejecutivo", "refinamiento", "bullet",
                 "comparative", "product_manager", "project_manager", "quality_assurance"]
        for mode in modes:
            result = summarizer.summarize("text", mode)
            assert result is not None

    @patch('requests.post')
    def test_summarize_api_error_raises(self, mock_post):
        mock_post.return_value = MagicMock(status_code=500, text="Server error")
        summarizer = GeminiAISummarizer(api_key="test-key")
        with pytest.raises(Exception, match="Gemini API error"):
            summarizer.summarize("text", "resumen")

    def test_get_agent_returns_none(self):
        summarizer = GeminiAISummarizer(api_key="test-key")
        agent = summarizer.get_agent("resumen")
        assert agent is None

    def test_get_agent_any_mode(self):
        summarizer = GeminiAISummarizer(api_key="test-key")
        for mode in ["tecnico", "ejecutivo", "bullet"]:
            assert summarizer.get_agent(mode) is None
