"""Infrastructure layer - transcription implementations.
Concrete implementations of transcription ports.
"""
from backend.src.domain.ports import AudioTranscriberPort


class GroqAudioTranscriber(AudioTranscriberPort):
    """Groq-based audio transcriber stub."""

    def __init__(self):
        pass

    def transcribe(self, audio_path: str) -> tuple[str, dict]:
        """Transcribe audio - stub implementation."""
        # Real implementation would call Groq API
        return "", {"time": 0.0}
