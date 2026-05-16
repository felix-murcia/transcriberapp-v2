"""Email sender using the system 'mail' command (sendmail-compatible)."""

import subprocess


def send_transcription_email(recipient: str, transcription: str, summary: str, mode: str, job_id: str) -> None:
    """Send transcription results to recipient via system mail command."""
    subject = f"Transcripción completada – modo {mode}"
    body = f"Transcripción\n{'=' * 40}\n{transcription}\n\nResumen ({mode})\n{'=' * 40}\n{summary}\n\nJob ID: {job_id}\n"

    subprocess.run(
        ["mail", "-s", subject, recipient],
        input=body.encode("utf-8"),
        check=True,
        timeout=30,
    )
    print(f"[EMAIL] Enviado a {recipient} (job={job_id})")
