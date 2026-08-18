"""
Groq API-based audio transcriber implementation.
Handles large files by splitting into chunks using local ffmpeg.
"""

import os
import math
import json
import time
import shutil
import tempfile
import subprocess
import mimetypes
import requests
from backend.src.domain.ports import AudioTranscriberPort

MAX_GROQ_MB = 22  # stay under Groq's 25MB hard limit


class GroqAudioTranscriber(AudioTranscriberPort):
    """Groq API-based audio transcriber with chunked support for large files."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("GROQ_MODEL_TRANSCRIBER", "whisper-large-v3")
        self.base_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        self.language = os.getenv("LANGUAGE", "es")

    # ── internal helpers ────────────────────────────────────────────────────

    def _to_mp3_chunks(self, audio_path: str) -> tuple[list[str], str]:
        """Convert audio to mono 128kbps MP3 and split if > MAX_GROQ_MB.

        Returns (chunk_paths, temp_dir). Caller must delete temp_dir when done.
        """
        tmp_dir = tempfile.mkdtemp(prefix="groq_chunks_")
        full_mp3 = os.path.join(tmp_dir, "full.mp3")

        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path,
             "-vn", "-ar", "44100", "-ac", "1", "-b:a", "128k", full_mp3],
            capture_output=True, timeout=600, check=True
        )

        mp3_size = os.path.getsize(full_mp3)
        max_bytes = MAX_GROQ_MB * 1024 * 1024

        if mp3_size <= max_bytes:
            return [full_mp3], tmp_dir

        # Get duration
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", full_mp3],
            capture_output=True, text=True, timeout=30, check=True
        )
        duration_s = float(json.loads(probe.stdout)["format"]["duration"])

        n_chunks = math.ceil(mp3_size / max_bytes)
        segment_s = math.ceil(duration_s / n_chunks)

        pattern = os.path.join(tmp_dir, "chunk_%03d.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-i", full_mp3,
             "-f", "segment", "-segment_time", str(segment_s),
             "-c", "copy", "-reset_timestamps", "1", pattern],
            capture_output=True, timeout=600, check=True
        )

        chunks = sorted(
            [os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir) if f.startswith("chunk_")]
        )
        return chunks, tmp_dir

    def _send_chunk(self, path: str, filename: str, content_type: str) -> str:
        """Send one audio file to Groq with retry on 429."""
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            with open(path, "rb") as f:
                resp = requests.post(
                    self.base_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": (filename, f, content_type)},
                    data={"model": self.model, "response_format": "json", "language": self.language},
                    timeout=300,
                )
            print(f"[GROQ] chunk={filename} attempt={attempt} status={resp.status_code}")
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 30 * attempt))
                print(f"[GROQ] rate limited, waiting {wait}s")
                if attempt < max_retries:
                    time.sleep(wait)
                    continue
            if resp.status_code != 200:
                print(f"[Groq API Error] HTTP {resp.status_code}: {resp.text[:300]}")
                raise Exception("Error interno al transcribir el audio. Por favor, verifica la configuración de Groq o intenta más tarde.")
            text = resp.json().get("text", "").strip()
            print(f"[GROQ] got {len(text)} chars")
            return text
        raise Exception("Groq rate limit persists after max retries")

    # ── public interface ────────────────────────────────────────────────────

    def transcribe(self, audio_path: str) -> tuple[str, dict]:
        """Transcribe audio file using Groq API, chunking if necessary."""
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY not set")

        file_size = os.path.getsize(audio_path)
        print(f"[GROQ] transcribing {audio_path} ({file_size / 1024 / 1024:.1f} MB)")

        tmp_dir = None
        try:
            # Always convert+chunk so we control format and size
            chunks, tmp_dir = self._to_mp3_chunks(audio_path)
            print(f"[GROQ] split into {len(chunks)} chunk(s)")

            texts = []
            for i, chunk in enumerate(chunks):
                text = self._send_chunk(chunk, f"chunk_{i:03d}.mp3", "audio/mpeg")
                texts.append(text)

            full_text = "\n".join(t for t in texts if t)
            return full_text, {"model": self.model, "chunks": len(chunks)}

        finally:
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
