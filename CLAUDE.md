# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Proyecto: TranscriberApp

## Reglas estrictas:
- **NO CREAR WORKTREES** automáticamente bajo ninguna circunstancia
- Siempre trabajar en la rama actual
- Si necesitas aislar cambios, preguntar al usuario primero

## Prevención de worktrees:
- Nunca ejecutar: `git worktree add`
- Nunca crear branches temporales con sufijos aleatorios (gamy-*, goofy-*, etc.)
- Si ves un worktree existente, reportarlo y no usarlo

## Comandos permitidos:
- `git status`, `git diff`, `git log`
- Modificaciones directas en la rama actual
- Commits normales

## Workflow:
1. Verificar rama actual: `git branch --show-current`
2. Hacer cambios directamente
3. Si hay conflictos, reportar al usuario

## Approach

- Read existing files before writing. Don't re-read unless changed.
- Thorough in reasoning, concise in output.
- Skip files over 100KB unless required.
- No sycophantic openers or closing fluff.
- No emojis or em-dashes.
- Do not guess APIs, versions, flags, commit SHAs, or package names. Verify by reading code or docs before asserting.

## Commands

**Setup**
```bash
python3 -m venv venv_transcriber
source venv_transcriber/bin/activate
pip install -r requirements.txt
```

**Run web server (local)**
```bash
uvicorn transcriber_app.web.web_app:app --host 0.0.0.0 --port 9000
```

**Run CLI pipeline**
```bash
python -m transcriber_app.main audio <name> <mode>
python -m transcriber_app.main texto <name> <mode>
```

**Tests**
```bash
pytest -q                           # all tests
pytest --cov=transcriber_app        # with coverage
pytest transcriber_app/tests/test_orchestrator.py  # single file
```

**Linting**
```bash
flake8 . --max-line-length=127
```

**Docker (development)**
```bash
docker-compose up --build
```

**Docker (production)**
```bash
docker-compose -f docker-compose.prod.yml up --build
```

## Environment Variables

Copy `.env-example` to `.env`. Required keys:
- `GOOGLE_API_KEY` — Gemini API key
- `GROQ_API_KEY` — Groq Whisper API key
- `USE_MODEL` — Gemini model name (default: `gemini-2.5-flash-lite`)
- `LANGUAGE` — transcription language (default: `es`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` — for email sending

## Architecture

### Processing Pipeline

The core pipeline runs through `Orchestrator` → `AIManager`:

1. **AudioReceiver** (`modules/audio_receiver.py`) — loads and validates audio file metadata
2. **GroqTranscriber** (`modules/ai/groq/transcriber.py`) — converts audio to WAV via ffmpeg, sends to Groq Whisper API, returns transcript text
3. **AIManager** (`modules/ai/ai_manager.py`) — central router that dispatches to GeminiModel or GroqModel; `summarize()` calls `GeminiModel.run_agent(mode, text)`
4. **GeminiModel** (`modules/ai/gemini/client.py`) — holds a dict of `GeminiAgent` instances keyed by mode; each agent loads its system prompt from `modules/ai/gemini/prompts/<mode>.md`
5. **OutputFormatter** (`modules/output_formatter.py`) — saves transcripts to `transcripts/`, outputs to `outputs/`, metrics alongside

### Summary Modes

Defined in `config.py`: `default`, `tecnico`, `refinamiento`, `ejecutivo`, `bullet`. Each maps to a `GeminiAgent` in `modules/ai/gemini/agents/` with a corresponding prompt file in `modules/ai/gemini/prompts/`.

### Web Layer

- **FastAPI app** created via factory in `web/web_app.py`; mounts `/api` router, `/static` files, `/api/resultados` (outputs dir), `/api/transcripciones` (transcripts dir)
- **API routes** (`web/api/routes.py`): `POST /api/upload-audio` saves file and launches a FastAPI `BackgroundTask`; `GET /api/status/{job_id}` polls in-memory `JOB_STATUS` dict; `POST /api/chat/stream` streams Gemini responses via SSE; `POST /api/process-existing` re-summarizes from existing transcript
- **Background jobs** (`web/api/background.py`): `JOB_STATUS` is a plain dict (in-memory, reset on restart); results (transcription + markdown) are stored there for the frontend to poll

### Frontend

Single-page app at `web/static/index.html`, JS split into modules under `web/static/js/modules/`:
- `audioProcessing.js` — handles upload + polling loop
- `chat.js` — SSE chat streaming
- `historyStorage.js` — localStorage-based history
- `api.js` — all fetch calls to the backend

### External Dependency

`ffmpeg` must be installed on the host (used by `GroqTranscriber.ensure_wav()` to convert any audio format to 16kHz mono WAV before sending to Groq).

### Kubernetes Deployment

Manifests in `k3s/`. The app runs with Uvicorn + Tailscale TLS certs mounted from `/var/lib/tailscale/certs` on the host. Exposed via `NodePort 30090`. PVCs handle persistence for `audios/`, `transcripts/`, `outputs/`.
