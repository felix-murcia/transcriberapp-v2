"""Infrastructure layer - output formatting implementations.
Concrete implementations of output formatting ports.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

from backend.src.domain.ports import OutputFormatterPort


class LocalOutputFormatter(OutputFormatterPort):
    """Local file system output formatter implementation."""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.getenv("APP_BASE_DIR", "/app"))

    def save_transcription(self, job_id: str, audio_name: str, text: str) -> str:
        """Save transcription to local file system."""
        transcripts_dir = self.base_dir / "transcripts"
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Use job_id as filename base for consistency
        base_name = Path(audio_name).stem
        path = transcripts_dir / f"{base_name}.txt"
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        
        return str(path)

    def save_output(self, job_id: str, audio_name: str, content: str, mode: str) -> str:
        """Save processed output to local file system."""
        outputs_dir = self.base_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = Path(audio_name).stem
        output_filename = f"{base_name}_{mode}.md"
        path = outputs_dir / output_filename
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(path)

    def save_metrics(self, job_id: str, audio_name: str, summary: str, mode: str) -> Dict[str, Any]:
        """Save metrics to local file system."""
        metrics_dir = self.base_dir / "outputs" / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = Path(audio_name).stem
        path = metrics_dir / f"{base_name}_{mode}.json"
        
        metrics = {
            "job_id": job_id,
            "name": base_name,
            "mode": mode,
            "length": len(summary),
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        return metrics