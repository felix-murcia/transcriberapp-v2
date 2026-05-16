"""
FFmpeg-based audio validator implementation.
"""

import subprocess
from pathlib import Path
from backend.src.domain.ports import AudioValidatorPort
from backend.src.domain.entities import AudioFile


class FFmpegAudioValidator(AudioValidatorPort):
    """FFmpeg-based audio file validator."""

    def validate(self, file_path: str) -> dict:
        """Validate audio file using FFmpeg."""
        try:
            # Use FFmpeg to get file information
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_format", "-show_streams", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "valid": False,
                    "issues": ["FFmpeg validation failed"],
                    "error": result.stderr
                }
            
            # Parse FFmpeg output to get basic info
            duration = None
            codec = None
            has_audio_stream = False

            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('duration=') and duration is None:
                    duration = line.split('=', 1)[1]
                elif line.startswith('codec_name='):
                    codec = line.split('=', 1)[1]
                elif line == '[STREAM]':
                    has_audio_stream = True

            # Basic validation checks
            issues = []
            warnings = []

            # Check if file has audio streams
            if not has_audio_stream:
                issues.append("No audio streams found")
            
            # Check duration (basic check)
            if duration:
                try:
                    total_seconds = float(duration)
                    if total_seconds > 3600:
                        warnings.append("Audio is longer than 1 hour")
                except ValueError:
                    pass
            
            # Check codec
            if codec and codec not in ['mp3', 'wav', 'webm', 'm4a', 'ogg', 'flac']:
                warnings.append(f"Unusual codec: {codec}")
            
            # Check file size
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                file_size = file_path_obj.stat().st_size
                if file_size > 500 * 1024 * 1024:  # 500MB
                    warnings.append("File is larger than 500MB")
                elif file_size < 1024:  # 1KB
                    issues.append("File is too small")
            
            valid = len(issues) == 0
            
            return {
                "valid": valid,
                "issues": issues,
                "warnings": warnings,
                "metadata": {
                    "duration": duration,
                    "codec": codec,
                    "streams": len(streams),
                    "file_size": file_path_obj.stat().st_size if file_path_obj.exists() else None
                }
            }
            
        except subprocess.TimeoutExpired:
            return {
                "valid": False,
                "issues": ["Validation timeout"],
                "error": "FFprobe timed out"
            }
        except FileNotFoundError:
            return {
                "valid": False,
                "issues": ["FFmpeg not found"],
                "error": "FFmpeg/FFprobe is not installed"
            }
        except Exception as e:
            return {
                "valid": False,
                "issues": ["Validation error"],
                "error": str(e)
            }