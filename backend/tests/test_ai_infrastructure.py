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
        assert summarizer.model_name == "gemini"

    def test_init_with_custom_model(self):
        """Test GeminiAISummarizer initialization with custom model."""
        summarizer = GeminiAISummarizer(model_name="gemini-2.5-pro")
        assert summarizer.model_name == "gemini-2.5-pro"

    def test_summarize_success(self):
        """Test successful summarization."""
        summarizer = GeminiAISummarizer()
        result = summarizer.summarize("Sample transcription text", "default")
        assert result is not None
        assert isinstance(result, str)

    def test_summarize_with_mode_specific_prompt(self):
        """Test summarization with mode-specific prompts."""
        summarizer = GeminiAISummarizer()
        result = summarizer.summarize("Sample transcription text", "tecnico")
        assert result is not None
        assert isinstance(result, str)

    def test_summarize_with_long_text(self):
        """Test summarization with long text."""
        summarizer = GeminiAISummarizer()
        long_text = "word " * 200
        result = summarizer.summarize(long_text, "default")
        assert result is not None
        assert isinstance(result, str)

    def test_summarize_with_short_text(self):
        """Test summarization with short text."""
        summarizer = GeminiAISummarizer()
        short_text = "Hello world"
        result = summarizer.summarize(short_text, "default")
        assert result is not None
        assert isinstance(result, str)

    def test_get_agent_default(self):
        """Test getting agent for default mode."""
        summarizer = GeminiAISummarizer()
        agent = summarizer.get_agent("default")
        assert agent is not None

    def test_get_agent_tecnico(self):
        """Test getting agent for tecnico mode."""
        summarizer = GeminiAISummarizer()
        agent = summarizer.get_agent("tecnico")
        assert agent is not None

    def test_get_agent_bullet(self):
        """Test getting agent for bullet mode."""
        summarizer = GeminiAISummarizer()
        agent = summarizer.get_agent("bullet")
        assert agent is not None

    def test_get_agent_refinamiento(self):
        """Test getting agent for refinamiento mode."""
        summarizer = GeminiAISummarizer()
        agent = summarizer.get_agent("refinamiento")
        assert agent is not None

    def test_get_agent_ejecutivo(self):
        """Test getting agent for ejecutivo mode."""
        summarizer = GeminiAISummarizer()
        agent = summarizer.get_agent("ejecutivo")
        assert agent is not None

    def test_get_agent_run(self):
        """Test agent run method."""
        summarizer = GeminiAISummarizer()
        agent = summarizer.get_agent("default")
        result = agent.run("test message", stream=False)
        # Agent.run returns a generator, not a string directly
        # Convert to list to verify it produces output
        output = list(result) if hasattr(result, '__iter__') else result
        assert output is not None

    def test_get_agent_run_stream(self):
        """Test agent run method with streaming."""
        summarizer = GeminiAISummarizer()
        agent = summarizer.get_agent("default")
        result = list(agent.run("test message", stream=True))
        assert len(result) > 0
        assert all(isinstance(r, str) for r in result)

    def test_fallback_summarization(self):
        """Test fallback summarization when Gemini not available."""
        with patch('backend.src.infrastructure.ai.GEMINI_AVAILABLE', False):
            summarizer = GeminiAISummarizer()
            result = summarizer.summarize("Sample text with enough words to truncate", "default")
            assert result is not None

    def test_agent_cache(self):
        """Test agent caching works correctly."""
        summarizer = GeminiAISummarizer()
        agent1 = summarizer.get_agent("default")
        agent2 = summarizer.get_agent("default")
        # Should return cached agent
        assert agent1 is agent2


class TestGeminiModelAISummarizer:
    """Test GeminiModel AI summarizer implementation."""

    def test_init(self):
        """Test GeminiModelAISummarizer initialization."""
        summarizer = GeminiAISummarizer()
        assert summarizer is not None

    def test_summarize_basic(self):
        """Test basic summarization."""
        summarizer = GeminiAISummarizer()
        result = summarizer.summarize("Test text for summarization", "default")
        assert result is not None
        assert isinstance(result, str)