"""
Local file system output formatter implementation.
"""

import json
import os
from pathlib import Path
from backend.src.domain.ports import OutputFormatterPort


class LocalOutputFormatter(OutputFormatterPort):
    """Local file system output formatter."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_transcription(self, job_id: str, filename: str, transcription: str) -> str:
        """Save transcription to local file."""
        transcription_dir = self.output_dir / "transcriptions"
        transcription_dir.mkdir(parents=True, exist_ok=True)
        
        safe_filename = filename.replace('/', '_').replace('\\', '_')
        output_path = transcription_dir / f"{job_id}_{safe_filename}_transcription.txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcription)
        
        return str(output_path)

    def save_output(self, job_id: str, filename: str, summary: str, mode: str) -> str:
        """Save summary output to local file."""
        output_dir = self.output_dir / "summaries"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        safe_filename = filename.replace('/', '_').replace('\\', '_')
        output_path = output_dir / f"{job_id}_{safe_filename}_{mode}_summary.txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        
        return str(output_path)

    def save_metrics(self, job_id: str, filename: str, summary: str, mode: str) -> str:
        """Save processing metrics to local file."""
        metrics_dir = self.output_dir / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        
        safe_filename = filename.replace('/', '_').replace('\\', '_')
        output_path = metrics_dir / f"{job_id}_{safe_filename}_{mode}_metrics.json"
        
        metrics = {
            "job_id": job_id,
            "filename": safe_filename,
            "mode": mode,
            "summary_length": len(summary),
            "timestamp": str(Path(output_path).stat().st_mtime) if output_path.exists() else None
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        return str(output_path)