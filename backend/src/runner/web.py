"""Web layer - FastAPI application with REST API endpoints."""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tempfile
import os
import shutil
from uuid import uuid4

from backend.src.application.use_cases import ProcessAudioUseCase, ProcessTextUseCase
from backend.src.infrastructure.dependency_injection import (
    create_transcription_service,
    get_background_tasks_adapter,
)

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

        return JSONResponse(
            status_code=200,
            content={
                "success": result.get("status") == True or result.get("status") == "success",
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
async def process_text(
    text: str = Form(...),
    mode: str = Form(...),
    filename: str = Form(default="text_input"),
    email: str = Form(default=None),
    background_tasks: BackgroundTasks = None,
):
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

    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="No text provided")

        # Create use case and execute
        transcription_service = create_transcription_service()
        use_case = ProcessTextUseCase(transcription_service)

        result = use_case.execute(
            text=text,
            mode=mode,
            filename=filename,
            email=email,
            job_id=job_id,
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": result.get("status") == True or result.get("status") == "success",
                "job_id": result.get("job_id"),
                "transcription": result.get("transcription"),
                "summary": result.get("summary"),
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
    modo = metadata[2] if len(metadata) > 2 else "default"
    email = metadata[3] if len(metadata) > 3 and metadata[3] else None

    # Find and sort chunk files
    chunk_files = sorted(
        upload_dir.glob("chunk_*"),
        key=lambda p: int(p.stem.split("_")[1])
    )

    if not chunk_files:
        raise HTTPException(status_code=400, detail="No se encontraron chunks")

    # Validate mode
    valid_modes = ["default", "tecnico", "refinamiento", "ejecutivo", "bullet",
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
    """Get the status of a processing job."""
    from backend.src.application.use_cases import JOB_STATUS
    job_data = JOB_STATUS.get(job_id, "unknown")
    if isinstance(job_data, dict):
        return job_data
    return {"job_id": job_id, "status": job_data}


def process_audio_job(job_id: str, nombre: str, modo: str, email: str = None):
    """
    Process audio job in background.
    
    Args:
        job_id: Job identifier
        nombre: Audio filename
        modo: Processing mode
        email: Optional email for notifications
    """
    try:
        # Find the audio file
        audios_dir = Path("audios")
        audio_path = audios_dir / f"{nombre}.webm"  # Default extension
        
        # Try different extensions
        if not audio_path.exists():
            for ext in ['.mp3', '.webm', '.wav', '.m4a', '.ogg']:
                test_path = audios_dir / f"{nombre}{ext}"
                if test_path.exists():
                    audio_path = test_path
                    break
        
        if not audio_path.exists():
            raise Exception(f"Audio file not found: {nombre}")
        
        # Create use case and execute
        transcription_service = create_transcription_service()
        use_case = ProcessAudioUseCase(transcription_service)
        
        result = use_case.execute(
            audio_path=str(audio_path),
            mode=modo,
            email=email,
            job_id=job_id,
        )
        
        # Store result
        from backend.src.application.use_cases import JOB_STATUS
        JOB_STATUS[job_id] = {
            "status": "completed",
            "job_id": job_id,
            "transcription": result.get("transcription"),
            "summary": result.get("summary"),
            "mode": result.get("mode"),
            "error": result.get("error"),
            "error_type": result.get("error_type"),
        }
        
    except Exception as e:
        # Store error
        from backend.src.application.use_cases import JOB_STATUS
        JOB_STATUS[job_id] = {
            "status": "failed",
            "job_id": job_id,
            "error": str(e),
            "error_type": "processing_error",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
