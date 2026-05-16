"""
Google Gemini AI summarizer implementation.
"""

import os
import json
import requests
from backend.src.domain.ports import AISummarizerPort


class GeminiAISummarizer(AISummarizerPort):
    """Google Gemini AI summarizer."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = os.getenv("USE_MODEL", "gemini-2.5-flash-lite")

    def summarize(self, text: str, mode: str) -> str:
        """Summarize text using Google Gemini AI."""
        try:
            # Define prompt based on mode
            mode_prompts = {
                "default": "Resume el siguiente texto de forma concisa y clara:",
                "tecnico": "Resume el siguiente texto con enfoque técnico, usando terminología profesional:",
                "ejecutivo": "Resume el siguiente texto para un ejecutivo, destacando puntos clave y conclusiones:",
                "refinamiento": "Refina y resume el siguiente texto mejorando su estructura y claridad:",
                "bullet": "Resume el siguiente texto en puntos clave (bullet points):",
                "comparative": "Resume el siguiente texto destacando puntos comparativos y contrastantes:",
                "product_manager": "Resume el siguiente texto desde la perspectiva de un Product Manager:",
                "project_manager": "Resume el siguiente texto desde la perspectiva de un Project Manager:",
                "quality_assurance": "Resume el siguiente texto enfocándote en aspectos de calidad y mejora:"
            }
            
            prompt = mode_prompts.get(mode, mode_prompts["default"])
            
            # Prepare request
            request_data = {
                "contents": [{
                    "parts": [{
                        "text": f"{prompt}\n\n{text}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 2048,
                }
            }
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            # Make API request
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(request_data)
            )
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Extract summary
            summary = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            if not summary:
                raise Exception("Empty summary received from Gemini API")
            
            return summary.strip()
            
        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")