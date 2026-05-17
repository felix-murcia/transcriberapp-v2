"""Web layer - FastAPI application with REST API endpoints."""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import shutil
import json
import requests
from uuid import uuid4
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.application.use_cases import ProcessAudioUseCase, ProcessTextUseCase
from backend.src.infrastructure.email.system_email_sender import send_transcription_email
from backend.src.infrastructure.dependency_injection import (
    create_transcription_service,
    get_background_tasks_adapter,
)
from backend.src.infrastructure.persistence.models import Base, User, Transcription, TranscriptionMode, Conversation
from backend.src.infrastructure.persistence.repositories import (
    UserRepository, TranscriptionRepository, TranscriptionModeRepository, ConversationRepository
)

# --- Database setup ---
DATABASE_URL = os.getenv("POSTGRES_URL", "sqlite:///./local.db")
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

# Migration: ensure legacy summaries column exists and populate transcription_modes from it
import sqlalchemy as _sa

with engine.connect() as _conn:
    # Add summaries column to existing DBs that predate it (needed to read legacy data)
    try:
        if DATABASE_URL.startswith("sqlite"):
            _conn.execute(_sa.text("ALTER TABLE transcriptions ADD COLUMN summaries JSON"))
        else:
            _conn.execute(_sa.text("ALTER TABLE transcriptions ADD COLUMN IF NOT EXISTS summaries JSON"))
        _conn.commit()
    except Exception:
        pass  # Already exists

    # Migrate summaries JSON → transcription_modes rows (idempotent)
    try:
        rows = _conn.execute(
            _sa.text("SELECT id, summaries FROM transcriptions WHERE summaries IS NOT NULL AND summaries != '{}'")
        ).fetchall()
        import json as _json
        for row in rows:
            tr_id, summaries_raw = row
            if not summaries_raw:
                continue
            summaries = summaries_raw if isinstance(summaries_raw, dict) else _json.loads(summaries_raw)
            for mode, summary in summaries.items():
                try:
                    _conn.execute(
                        _sa.text(
                            "INSERT INTO transcription_modes (transcription_id, mode, summary, status, created_at) "
                            "VALUES (:tid, :mode, :summary, 'completed', CURRENT_TIMESTAMP) "
                            + ("ON CONFLICT(transcription_id, mode) DO NOTHING"
                               if DATABASE_URL.startswith("sqlite")
                               else "ON CONFLICT (transcription_id, mode) DO NOTHING")
                        ),
                        {"tid": tr_id, "mode": mode, "summary": summary},
                    )
                except Exception:
                    pass
        _conn.commit()
    except Exception as _e:
        print(f"[MIGRATION] summaries→transcription_modes: {_e}")


def get_db():
    return SessionLocal()


def get_or_create_anon_user(db) -> int:
    """Return user_id for the anonymous local user, creating it if needed."""
    repo = UserRepository(db)
    user = repo.get_by_email("anonymous@local")
    if not user:
        user = repo.create(email="anonymous@local", hashed_password="")
        db.commit()
    return user.id

# Create FastAPI app
app = FastAPI(
    title="TranscriberApp API",
    description="API for audio transcription and text summarization",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio temporal para chunks
UPLOADS_TEMP_DIR = os.getenv("UPLOADS_TEMP_DIR", "/tmp/audios_chunks")
Path(UPLOADS_TEMP_DIR).mkdir(parents=True, exist_ok=True)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "TranscriberApp API"}


@app.post("/api/process-audio")
async def process_audio(
    file: UploadFile = File(...),
    mode: str = Form(...),
    email: str = Form(default=None),
    background_tasks: BackgroundTasks = None,
):
    """
    Process an audio file for transcription and summarization.

    Args:
        file: Audio file (.mp3, .webm, etc.)
        mode: Summarization mode (tecnico, ejecutivo, etc.)
        email: Optional email for notifications
        background_tasks: FastAPI background tasks

    Returns:
        JSON with job_id, transcription, and summary
    """
    job_id = str(uuid4())

    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Get file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.mp3', '.webm', '.wav', '.m4a', '.ogg']:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}"
            )

        # Create temporary file
        temp_dir = Path("audios")
        temp_dir.mkdir(exist_ok=True)

        temp_path = temp_dir / f"{job_id}{file_ext}"

        # Save uploaded file
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        # Create use case and execute
        transcription_service = create_transcription_service()
        use_case = ProcessAudioUseCase(transcription_service)

        result = use_case.execute(
            audio_path=str(temp_path),
            mode=mode,
            email=email,
            job_id=job_id,
        )

        success = result.get("status") == True or result.get("status") == "success"
        if success and email:
            try:
                send_transcription_email(
                    recipient=email,
                    transcription=result.get("transcription", ""),
                    summary=result.get("summary", ""),
                    mode=mode,
                    job_id=job_id,
                )
            except Exception as e:
                print(f"[EMAIL] No enviado: {e}")

        return JSONResponse(
            status_code=200,
            content={
                "success": success,
                "job_id": result.get("job_id"),
                "transcription": result.get("transcription"),
                "summary": result.get("summary"),
                "mode": result.get("mode"),
                "error": result.get("error"),
                "error_type": result.get("error_type"),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "job_id": job_id,
                "error": str(e),
                "error_type": "processing_error",
            }
        )


@app.post("/api/process-text")
async def process_text(payload: dict):
    """
    Process text for summarization.

    Args:
        text: Input text to summarize
        mode: Summarization mode
        filename: Optional filename for reference
        email: Optional email for notifications

    Returns:
        JSON with job_id, transcription, and summary
    """
    job_id = str(uuid4())
    text = (payload.get("text") or "").strip()
    mode = payload.get("mode", "resumen")
    filename = payload.get("filename", "text_input")
    email = payload.get("email") or None

    try:
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")

        transcription_service = create_transcription_service()
        use_case = ProcessTextUseCase(transcription_service)

        result = use_case.execute(
            text=text,
            mode=mode,
            filename=filename,
            email=email,
            job_id=job_id,
        )

        print(f"[process-text] mode={mode} markdown_len={len(result.get('markdown') or '')} transcription_len={len(text)}")

        return JSONResponse(
            status_code=200,
            content={
                "success": result.get("status") == True or result.get("status") == "success",
                "job_id": result.get("job_id"),
                "transcription": result.get("transcription"),
                "markdown": result.get("markdown"),
                "mode": result.get("mode"),
                "error": result.get("error"),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "job_id": job_id,
                "error": str(e),
            }
        )


@app.post("/api/upload-chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunkIndex: int = Form(...),
    totalChunks: int = Form(...),
    uploadId: str = Form(...),
    nombre: str = Form(...),
    modo: str = Form(...),
    email: str = Form(default=None),
    extension: str = Form(...),
):
    """
    Upload a chunk of an audio file for large file support.

    Args:
        chunk: Binary chunk data
        chunkIndex: Index of this chunk (0-based)
        totalChunks: Total number of chunks
        uploadId: Unique upload session ID
        nombre: Desired filename for the audio
        modo: Processing mode
        email: Optional email for notifications
        extension: File extension

    Returns:
        JSON with upload status
    """
    uploads_temp_dir = Path(UPLOADS_TEMP_DIR)
    upload_dir = uploads_temp_dir / uploadId
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata on first chunk
    if chunkIndex == 0:
        (upload_dir / "metadata.txt").write_text(
            f"{extension}\n{nombre}\n{modo}\n{email or ''}\n{totalChunks}"
        )

    # Save chunk
    chunk_path = upload_dir / f"chunk_{chunkIndex:06d}"
    content = await chunk.read()
    chunk_path.write_bytes(content)

    return {
        "status": "chunk_received",
        "chunkIndex": chunkIndex,
        "uploadId": uploadId,
        "receivedSize": len(content),
    }


@app.post("/api/upload-complete")
async def upload_complete(
    background_tasks: BackgroundTasks,
    uploadId: str = Form(...),
):
    """
    Complete a chunked upload by assembling all chunks.

    Args:
        uploadId: Unique upload session ID

    Returns:
        JSON with processing status and job_id
    """
    uploads_temp_dir = Path(UPLOADS_TEMP_DIR)
    upload_dir = uploads_temp_dir / uploadId

    if not upload_dir.exists():
        raise HTTPException(status_code=404, detail="Upload no encontrado")

    # Read metadata
    metadata_path = upload_dir / "metadata.txt"
    if not metadata_path.exists():
        raise HTTPException(status_code=400, detail="Metadata no encontrada")

    metadata = metadata_path.read_text().strip().split("\n")
    extension = metadata[0] if len(metadata) > 0 else "webm"
    nombre = metadata[1] if len(metadata) > 1 else uploadId
    modo = metadata[2] if len(metadata) > 2 else "resumen"
    email = metadata[3] if len(metadata) > 3 and metadata[3] else None

    # Find and sort chunk files
    chunk_files = sorted(
        upload_dir.glob("chunk_*"),
        key=lambda p: int(p.stem.split("_")[1])
    )

    if not chunk_files:
        raise HTTPException(status_code=400, detail="No se encontraron chunks")

    # Validate mode
    valid_modes = ["resumen", "tecnico", "refinamiento", "ejecutivo", "bullet",
                   "comparative", "product_manager", "project_manager", "quality_assurance"]
    if modo not in valid_modes:
        raise HTTPException(status_code=400, detail="Modo inválido")

    # Assemble file
    audios_dir = Path("audios")
    audios_dir.mkdir(exist_ok=True)

    safe_name = nombre.lower()
    if '.' in safe_name:
        safe_name = safe_name.rsplit('.', 1)[0]
    audio_path = audios_dir / f"{safe_name}.{extension}"

    with audio_path.open("wb") as outfile:
        for chunk_file in chunk_files:
            outfile.write(chunk_file.read_bytes())

    # Cleanup
    try:
        shutil.rmtree(upload_dir)
    except Exception:
        pass

    # Start processing
    job_id = str(uuid4())
    background_tasks.add_task(
        process_audio_job,
        job_id=job_id,
        nombre=safe_name,
        modo=modo,
        email=email,
    )

    return {
        "status": "processing",
        "job_id": job_id,
        "message": "Audio recibido. Procesamiento iniciado.",
    }


@app.post("/api/upload-cancel")
async def upload_cancel(uploadId: str = Form(...)):
    """
    Cancel a chunked upload session.

    Args:
        uploadId: Unique upload session ID

    Returns:
        JSON with cancellation status
    """
    uploads_temp_dir = Path(UPLOADS_TEMP_DIR)
    upload_dir = uploads_temp_dir / uploadId

    if not upload_dir.exists():
        raise HTTPException(status_code=404, detail="Upload no encontrado")

    shutil.rmtree(upload_dir)

    return {
        "status": "cancelled",
        "uploadId": uploadId,
        "message": "Upload cancelado.",
    }


@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    """Get the status of a processing job from the database."""
    db = get_db()
    try:
        repo = TranscriptionRepository(db)
        tr = repo.get_by_job_id(job_id)
        if not tr:
            return {"job_id": job_id, "status": "processing"}
        return {
            "job_id": tr.job_id,
            "status": tr.status,
            "transcription": tr.transcription_text,
            "summary": tr.summary_output,
            "mode": tr.mode,
            "error": tr.error_message,
        }
    finally:
        db.close()


def process_audio_job(job_id: str, nombre: str, modo: str, email: str = None):
    """Process audio job in background and persist result to DB."""
    db = get_db()
    try:
        user_id = get_or_create_anon_user(db)
        tr_repo = TranscriptionRepository(db)

        # Register job as pending
        tr_repo.create(
            user_id=user_id,
            job_id=job_id,
            audio_filename=nombre,
            audio_path=None,
            mode=modo,
            email=email,
        )
        db.commit()

        # Find the audio file
        audios_dir = Path("audios")
        audio_path = None
        for ext in ['.webm', '.mp3', '.wav', '.m4a', '.ogg']:
            p = audios_dir / f"{nombre}{ext}"
            if p.exists():
                audio_path = p
                break

        if not audio_path:
            raise Exception(f"Audio file not found: {nombre}")

        transcription_service = create_transcription_service()
        use_case = ProcessAudioUseCase(transcription_service)
        result = use_case.execute(audio_path=str(audio_path), mode=modo, email=email, job_id=job_id)

        print(f"[JOB {job_id}] raw result: {result}")

        if result.get("status") == "error" or result.get("error"):
            tr_repo.update_status(job_id, "failed", error_message=result.get("error", "Unknown error"))
        else:
            tr_repo.update_status(
                job_id,
                "completed",
                transcription_text=result.get("transcription"),
                summary_output=result.get("summary"),
            )
        db.commit()

        # Enviar email si se proporcionó dirección
        if email and result.get("status") != "error":
            try:
                send_transcription_email(
                    recipient=email,
                    transcription=result.get("transcription", ""),
                    summary=result.get("summary", ""),
                    mode=modo,
                    job_id=job_id,
                )
            except Exception as e:
                print(f"[JOB {job_id}] Email no enviado: {e}")

        # Eliminar audio original para liberar espacio
        try:
            audio_path.unlink()
            print(f"[JOB {job_id}] Audio eliminado: {audio_path}")
        except Exception as e:
            print(f"[JOB {job_id}] No se pudo eliminar audio: {e}")

    except Exception as e:
        print(f"[JOB {job_id}] EXCEPTION: {e}")
        try:
            tr_repo.update_status(job_id, "failed", error_message=str(e))
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


# =============================================================================
# Transcription history endpoints (replaces IndexedDB)
# =============================================================================

@app.post("/api/transcriptions")
def save_transcription(payload: dict):
    """Persist a completed transcription to the database.

    All processings under the same audio_filename are grouped into one Transcription record.
    Each mode's summary is stored as a separate TranscriptionMode row.
    """
    db = get_db()
    try:
        user_id = get_or_create_anon_user(db)
        tr_repo = TranscriptionRepository(db)
        mode_repo = TranscriptionModeRepository(db)

        audio_filename = payload.get("audio_filename", "unknown")
        mode = payload.get("mode", "resumen")
        transcription_text = payload.get("transcription_text")
        summary_output = payload.get("summary_output", "")
        email = payload.get("email")

        existing = tr_repo.get_by_filename_and_user(audio_filename, user_id)

        if existing:
            existing.status = "completed"
            if transcription_text:
                existing.transcription_text = transcription_text
            mode_repo.add_or_update(existing.id, mode, summary_output)
            db.commit()
            return {"ok": True, "job_id": existing.job_id}
        else:
            job_id = payload.get("job_id", str(uuid4()))
            tr = tr_repo.create(
                user_id=user_id,
                job_id=job_id,
                audio_filename=audio_filename,
                audio_path=payload.get("audio_path"),
                mode=mode,
                email=email,
            )
            tr_repo.update_status(job_id, "completed", transcription_text=transcription_text, summary_output=summary_output)
            mode_repo.add_or_update(tr.id, mode, summary_output)
            db.commit()
            return {"ok": True, "job_id": job_id}
    finally:
        db.close()


@app.get("/api/transcriptions")
def list_transcriptions():
    """List all transcriptions for the anonymous user."""
    db = get_db()
    try:
        user_id = get_or_create_anon_user(db)
        tr_repo = TranscriptionRepository(db)
        mode_repo = TranscriptionModeRepository(db)
        items = tr_repo.list_by_user(user_id, limit=50)
        return [
            {
                "job_id": t.job_id,
                "audio_filename": t.audio_filename,
                "mode": t.mode,
                "status": t.status,
                "summaries": mode_repo.summaries_dict(t.id),
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in items
        ]
    finally:
        db.close()


@app.get("/api/transcriptions/{job_id}")
def get_transcription(job_id: str):
    """Get a single transcription with full content."""
    db = get_db()
    try:
        tr_repo = TranscriptionRepository(db)
        mode_repo = TranscriptionModeRepository(db)
        tr = tr_repo.get_by_job_id(job_id)
        if not tr:
            raise HTTPException(status_code=404, detail="Not found")
        return {
            "job_id": tr.job_id,
            "audio_filename": tr.audio_filename,
            "mode": tr.mode,
            "status": tr.status,
            "transcription_text": tr.transcription_text,
            "summary_output": tr.summary_output,
            "summaries": mode_repo.summaries_dict(tr.id),
            "created_at": tr.created_at.isoformat() if tr.created_at else None,
        }
    finally:
        db.close()


@app.patch("/api/transcriptions/{job_id}")
def rename_transcription(job_id: str, payload: dict):
    """Rename a transcription (audio_filename)."""
    new_name = (payload.get("audio_filename") or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="audio_filename required")
    db = get_db()
    try:
        repo = TranscriptionRepository(db)
        tr = repo.get_by_job_id(job_id)
        if not tr:
            raise HTTPException(status_code=404, detail="Not found")
        tr.audio_filename = new_name
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@app.delete("/api/transcriptions/{job_id}")
def delete_transcription(job_id: str):
    """Delete a transcription."""
    db = get_db()
    try:
        repo = TranscriptionRepository(db)
        tr = repo.get_by_job_id(job_id)
        if not tr:
            raise HTTPException(status_code=404, detail="Not found")
        repo.delete(job_id)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


# =============================================================================
# Conversation endpoints
# =============================================================================

@app.post("/api/conversations")
def add_conversation_message(payload: dict):
    """Add a message to a transcription's conversation."""
    db = get_db()
    try:
        tr_repo = TranscriptionRepository(db)
        tr = tr_repo.get_by_job_id(payload["job_id"])
        if not tr:
            raise HTTPException(status_code=404, detail="Transcription not found")

        conv_repo = ConversationRepository(db)
        msg = conv_repo.add_message(
            transcription_id=tr.id,
            role=payload["role"],
            content=payload["content"],
        )
        db.commit()
        return {"ok": True, "id": msg.id}
    finally:
        db.close()


@app.get("/api/conversations/{job_id}")
def get_conversation(job_id: str):
    """Get all messages for a transcription's conversation."""
    db = get_db()
    try:
        tr_repo = TranscriptionRepository(db)
        tr = tr_repo.get_by_job_id(job_id)
        if not tr:
            raise HTTPException(status_code=404, detail="Transcription not found")

        conv_repo = ConversationRepository(db)
        msgs = conv_repo.list_by_transcription(tr.id)
        return [{"role": m.role, "content": m.content} for m in msgs]
    finally:
        db.close()


# =============================================================================
# Chat streaming endpoint
# =============================================================================

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("USE_MODEL", "gemini-2.5-flash-lite")

_MODE_LABELS = {
    "resumen": "Resumen general",
    "tecnico": "Análisis técnico",
    "ejecutivo": "Resumen ejecutivo",
    "refinamiento": "Refinamiento",
    "bullet": "Puntos clave (bullet points)",
    "comparative": "Análisis comparativo",
    "product_manager": "Perspectiva Product Manager",
    "project_manager": "Perspectiva Project Manager",
    "quality_assurance": "Perspectiva Quality Assurance",
}


def _build_system_instruction(transcription: str, summaries: dict) -> str:
    parts = [
        "Eres un asistente experto en análisis de contenido de audio.",
        "Tu función es responder preguntas sobre una transcripción y los resúmenes que se han generado a partir de ella.",
        "",
        "REGLAS ESTRICTAS:",
        "- Responde SIEMPRE basándote exclusivamente en el contenido proporcionado a continuación.",
        "- Si el usuario pregunta por un modo concreto (técnico, ejecutivo, bullet, etc.), trabaja con ese resumen específico.",
        "- Si pregunta por la transcripción, trabaja con el texto original.",
        "- Si la pregunta es ambigua, usa todos los contextos disponibles y aclara de cuál extraes la respuesta.",
        "- No inventes ni añadas información que no esté en el contexto.",
        "- Sé preciso, directo y útil. Evita respuestas vagas o genéricas.",
        "- Responde en el mismo idioma que el usuario.",
        "",
        "═" * 60,
        "CONTENIDO DE REFERENCIA",
        "═" * 60,
    ]

    if transcription:
        parts += ["", "TRANSCRIPCIÓN COMPLETA:", "─" * 40, transcription]

    if summaries:
        parts += ["", "RESÚMENES GENERADOS:", "─" * 40]
        for mode, summary in summaries.items():
            if summary:
                label = _MODE_LABELS.get(mode, mode.replace("_", " ").title())
                parts += [f"\n## {label}:", summary]

    parts += ["", "═" * 60]
    return "\n".join(parts)


@app.post("/api/chat/stream")
async def chat_stream(payload: dict):
    """Stream a chat response from Gemini given transcription context."""
    message = payload.get("message", "")
    transcription = payload.get("transcription", "")
    summaries = payload.get("summaries") or {}
    history = payload.get("history", [])

    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    system_instruction = _build_system_instruction(transcription, summaries)

    # Build conversation history (exclude current message, it's in `message`)
    contents = []
    for h in history[:-1]:
        role = "model" if h["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": h["content"]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    import httpx as _httpx

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}"
    )
    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4096},
    }

    async def generate():
        try:
            async with _httpx.AsyncClient(timeout=60) as client:
                async with client.stream("POST", url, headers={"Content-Type": "application/json"}, json=body) as resp:
                    if resp.status_code != 200:
                        yield f"[Error Gemini: {resp.status_code}]"
                        return
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            text = (
                                data.get("candidates", [{}])[0]
                                .get("content", {})
                                .get("parts", [{}])[0]
                                .get("text", "")
                            )
                            if text:
                                yield text
                        except Exception:
                            pass
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
