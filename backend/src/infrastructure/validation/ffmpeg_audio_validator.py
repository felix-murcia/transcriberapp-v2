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
            streams = []
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('duration='):
                    duration = line.split('=')[1]
                elif line.startswith('codec_name='):
                    codec = line.split('=')[1]
                elif line.startswith('stream='):
                    streams.append(line)
            
            # Basic validation checks
            issues = []
            warnings = []
            
            # Check if file has audio streams
            if not streams:
                issues.append("No audio streams found")
            
            # Check duration (basic check)
            if duration:
                try:
                    # Parse duration (HH:MM:SS.mmm)
                    time_parts = duration.split(':')
                    if len(time_parts) == 3:
                        hours, minutes, seconds = time_parts
                        total_seconds = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                        
                        # Check if audio is too long (basic check)
                        if total_seconds > 3600:  # 1 hour
                            warnings.append("Audio is longer than 1 hour")
                            
                except ValueError:
                    issues.append("Invalid duration format")
            
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