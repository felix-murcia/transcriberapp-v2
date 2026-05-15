"""
Groq API-based audio transcriber implementation.
"""

import json
import requests
from backend.src.domain.ports import AudioTranscriberPort


class GroqAudioTranscriber(AudioTranscriberPort):
    """Groq API-based audio transcriber."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or "YOUR_GROQ_API_KEY"  # Replace with actual API key
        self.base_url = "https://api.groq.com/openai/v1"

    def transcribe(self, audio_path: str) -> tuple[str, dict]:
        """Transcribe audio file using Groq API."""
        try:
            # Read audio file
            with open(audio_path, "rb") as audio_file:
                files = {"file": audio_file}
                data = {
                    "model": "whisper-large-v3",  # Use Groq's Whisper model
                    "response_format": "json",
                    "language": "es"  # Spanish language
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                # Make API request
                response = requests.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code != 200:
                    raise Exception(f"Groq API error: {response.status_code} - {response.text}")
                
                result = response.json()
                
                # Extract transcription text
                transcription_text = result.get("text", "")
                
                # Extract metadata
                metadata = {
                    "model": result.get("model", "whisper-large-v3"),
                    "language": result.get("language", "es"),
                    "duration": result.get("duration", 0),
                    "segments": len(result.get("segments", []))
                }
                
                return transcription_text, metadata
                
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")