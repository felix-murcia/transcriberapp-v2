# TranscriberApp

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

TranscriberApp is a self-hosted audio transcription and AI summarization tool. You upload or record audio, it transcribes it using Groq Whisper, and then generates structured summaries through nine purpose-built modes powered by Google Gemini. A streaming chat agent lets you ask follow-up questions about any transcription.

**Target audience:** engineering teams, product managers, project managers, and QA engineers who need structured, role-specific summaries extracted from meetings, interviews, or any spoken audio.

---

## Features

- **In-browser audio recording** using the MediaRecorder API, with download and delete controls.
- **File upload** with automatic chunked transfer (2 MB chunks) for large files. Progress bar with cancel support.
- **Groq Whisper transcription** (`whisper-large-v3` by default). Automatically splits files exceeding 22 MB into timed MP3 chunks via `ffmpeg`, transcribes each in sequence with retry on rate limits, then joins the text.
- **Nine summarization modes**, each backed by a distinct Gemini prompt:

  | Mode key | Display name | Purpose |
  |---|---|---|
  | `resumen` | Resumen general | Structured general summary with key points and next steps |
  | `tecnico` | Análisis técnico | Senior-engineer technical analysis: architecture, decisions, risks, recommendations |
  | `ejecutivo` | Resumen ejecutivo | C-level executive briefing focused on business impact and decisions required |
  | `refinamiento` | Refinamiento | Engineering refinement artifacts: decisions, user stories, tasks, open questions |
  | `bullet` | Puntos clave | Extreme distillation to a maximum of 12 bullet points |
  | `comparative` | Análisis comparativo | Structured comparison table of alternatives with pros, cons, and decision matrix |
  | `product_manager` | Perspectiva Product Manager | Feature tables, prioritization, metrics, roadmap impact |
  | `project_manager` | Perspectiva Project Manager | Project health dashboard, milestones, blockers, resource allocation |
  | `quality_assurance` | Perspectiva Quality Assurance | Test scenarios, coverage gaps, automation candidates, quality risks |

- **Re-summarize without re-transcribing.** Load a past transcription from history and run any mode directly against the saved text.
- **Streaming chat agent.** After any processing, open the chat panel to ask questions. Gemini streams its answer in real time using Server-Sent Events. The agent is grounded exclusively on the transcription and all summaries generated so far.
- **Persistent history** stored in PostgreSQL (or SQLite for local runs). Each audio file groups all its mode summaries under a single record. History panel supports rename, delete, and one-click reload.
- **Email notifications.** Optionally supply an email address; the backend sends the transcription and summary via `mailutils` when processing completes.
- **Health endpoint** at `GET /health`.
- **Dual environment** — dev (hot-reload backend, port 8003/8088) and prod (Nginx reverse proxy, port 80).

---

## UI Layout

The single-page application is organized into the following sections:

- **Header** — application title and job ID indicator once a session is active.
- **Session setup** — a named session must be at least 5 characters long before any processing is enabled.
- **Form config** — mode selector (nine options) and optional email field.
- **Audio recorder** — record from microphone or upload a file (`mp3`, `webm`, `wav`, `m4a`, `ogg`). Shows a playback preview after capture.
- **Process button** — sends audio or re-runs summarization on existing transcription text. Disabled while the selected mode has already been processed for the current session.
- **Results panel** — tabbed view of all summaries generated for the current session, rendered as Markdown.
- **Chat panel** (floating button) — streaming conversational interface grounded in the active transcription and summaries.
- **History panel** (floating button) — slide-in panel listing the last 50 transcriptions with rename and delete actions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI 0.116, Uvicorn 0.40 |
| Transcription | Groq API — `whisper-large-v3` (configurable) |
| AI summarization / chat | Google Gemini API — `gemini-2.5-flash-lite` (configurable) |
| Audio processing | `ffmpeg` (system binary, invoked via subprocess) |
| ORM / database | SQLAlchemy 2.0 — PostgreSQL 16 (prod) or SQLite (local fallback) |
| Cache / queue | Redis 7 (present in compose; reserved for future use) |
| Frontend | React 18, TypeScript 5, Vite 6, `marked` for Markdown rendering |
| Reverse proxy | Nginx (alpine) — proxies `/api/` and `/health` to the backend |
| Containerization | Docker Compose (separate dev and prod files) |

---

## Prerequisites

- Docker and Docker Compose v2
- Node.js 20+ and npm (only needed when building the frontend outside Docker)
- A [Groq API key](https://console.groq.com/) for transcription
- A [Google AI Studio API key](https://aistudio.google.com/app/apikey) for summarization and chat

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd transcriberapp-v2
cp .env.example .env.dev   # for development
cp .env.example .env.prod  # for production
```

Edit both files and set at minimum:

```
GOOGLE_API_KEY=<your-google-key>
GROQ_API_KEY=<your-groq-key>
SECRET_KEY=<a-long-random-string>
```

### 2. Development environment

Runs the backend with `--reload` on port **8003** and serves the frontend through Nginx on port **8088**.

```bash
./start-dev.sh
```

The script builds the frontend (`npm run build`), builds the backend Docker image, and starts all services. Equivalent manual command:

```bash
(cd frontend && npm run build)
docker compose -f docker-compose.dev.yml build backend
docker compose -f docker-compose.dev.yml up -d
```

Access the app at `http://localhost:8088`.

To follow backend logs:

```bash
docker compose -f docker-compose.dev.yml logs -f backend
```

To stop:

```bash
docker compose -f docker-compose.dev.yml down
```

### 3. Production environment

Runs the backend on port **8002** and the full stack (Nginx, PostgreSQL, Redis) with the frontend served at **http://localhost** (port 80).

```bash
./start-prod.sh
```

To stop:

```bash
docker compose -f docker-compose.yml down
```

### 4. Local run without Docker

```bash
# Backend
python -m venv venv_transcriber
source venv_transcriber/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
# Edit .env — POSTGRES_URL defaults to sqlite:///./local.db when unset
python -m uvicorn backend.src.runner.web:app --host 0.0.0.0 --port 8002 --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

The backend auto-creates the SQLite database and runs schema migrations on startup. No separate migration step is required.

---

## Environment Variables

All variables are loaded from `.env.dev` (dev compose) or `.env.prod` (prod compose). See `.env.example` for the template.

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | Yes | — | Google Generative AI API key used for Gemini summarization and streaming chat |
| `GROQ_API_KEY` | Yes | — | Groq API key used for Whisper audio transcription |
| `GROQ_API_URL` | No | `https://api.groq.com/openai/v1` | Base URL for the Groq API |
| `GROQ_MODEL_TRANSCRIBER` | No | `whisper-large-v3` | Groq model identifier for transcription |
| `USE_MODEL` | No | `gemini-2.5-flash-lite` | Gemini model identifier for summarization and chat |
| `LANGUAGE` | No | `es` | Language code passed to Groq Whisper (e.g. `en`, `es`) |
| `FFMPEG_API_URL` | No | `http://ffmpeg-api:8080` | URL of a remote ffmpeg service (not used in current implementation; ffmpeg is invoked locally) |
| `POSTGRES_URL` | No | `sqlite:///./local.db` | SQLAlchemy database URL. Falls back to SQLite when not set |
| `REDIS_URL` | No | `redis://redis:6379` | Redis connection URL (reserved for future use) |
| `SECRET_KEY` | Yes | — | Secret key for security purposes. Change before any deployment |

---

## API Reference

Base path for all API routes: `/api/`

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status": "ok", "service": "TranscriberApp API"}` |

### Audio processing

| Method | Path | Body type | Description |
|---|---|---|---|
| `POST` | `/api/process-audio` | `multipart/form-data` | Upload an audio file and return transcription + summary synchronously. Fields: `file` (binary), `mode` (string), `email` (string, optional) |
| `POST` | `/api/process-text` | JSON | Summarize existing text. Fields: `text`, `mode`, `filename` (optional), `email` (optional) |
| `POST` | `/api/upload-chunk` | `multipart/form-data` | Upload one chunk of a large file. Fields: `chunk`, `chunkIndex`, `totalChunks`, `uploadId`, `nombre`, `modo`, `email`, `extension` |
| `POST` | `/api/upload-complete` | `multipart/form-data` | Assemble all chunks and start background processing. Field: `uploadId` |
| `POST` | `/api/upload-cancel` | `multipart/form-data` | Delete a partial chunked upload. Field: `uploadId` |
| `GET` | `/api/status/{job_id}` | — | Poll background job status: `pending`, `completed`, or `failed` |

### Transcription history

| Method | Path | Body type | Description |
|---|---|---|---|
| `POST` | `/api/transcriptions` | JSON | Save or update a completed transcription record |
| `GET` | `/api/transcriptions` | — | List last 50 transcriptions for the anonymous user |
| `GET` | `/api/transcriptions/{job_id}` | — | Retrieve a single transcription with full text and all mode summaries |
| `PATCH` | `/api/transcriptions/{job_id}` | JSON | Rename a transcription. Field: `audio_filename` |
| `DELETE` | `/api/transcriptions/{job_id}` | — | Delete a transcription and its associated data |

### Chat

| Method | Path | Body type | Description |
|---|---|---|---|
| `POST` | `/api/chat/stream` | JSON | Stream a Gemini chat response (`text/plain` SSE). Fields: `message`, `transcription`, `summaries` (object), `history` (array of `{role, content}`) |
| `POST` | `/api/conversations` | JSON | Persist a chat message. Fields: `job_id`, `role`, `content` |
| `GET` | `/api/conversations/{job_id}` | — | Retrieve all conversation messages for a transcription |

**Accepted audio formats:** `.mp3`, `.webm`, `.wav`, `.m4a`, `.ogg`

**Valid mode values:** `resumen`, `tecnico`, `ejecutivo`, `refinamiento`, `bullet`, `comparative`, `product_manager`, `project_manager`, `quality_assurance`

---

## Project Structure

```
transcriberapp-v2/
├── backend/
│   ├── requirements.txt
│   └── src/
│       ├── application/
│       │   └── use_cases.py          # ProcessAudioUseCase, ProcessTextUseCase
│       ├── domain/
│       │   ├── entities.py           # TranscriptionJob, AudioFile, ProcessingResult
│       │   ├── ports.py              # AudioTranscriberPort, AISummarizerPort
│       │   └── exceptions.py
│       ├── infrastructure/
│       │   ├── ai/
│       │   │   └── gemini_ai_summarizer.py   # All nine mode prompts + Gemini client
│       │   ├── transcription/
│       │   │   └── groq_audio_transcriber.py # Whisper via Groq, chunked ffmpeg support
│       │   ├── persistence/
│       │   │   ├── models.py         # SQLAlchemy models: User, Transcription, TranscriptionMode, Conversation
│       │   │   └── repositories.py
│       │   ├── email/
│       │   │   └── system_email_sender.py
│       │   ├── file_processing/
│       │   ├── job_status/
│       │   ├── validation/
│       │   └── dependency_injection.py
│       ├── runner/
│       │   └── web.py                # FastAPI app — all endpoints
│       └── config.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AudioRecorder.tsx     # Record + chunked file upload
│   │   │   ├── ChatPanel.tsx         # Streaming chat UI
│   │   │   ├── FormConfig.tsx        # Mode selector + email field
│   │   │   ├── Header.tsx
│   │   │   ├── HistoryPanel.tsx      # Slide-in history with rename/delete
│   │   │   ├── ResultsPanel.tsx      # Markdown summary tabs
│   │   │   └── SessionSetup.tsx      # Session name input
│   │   ├── context/
│   │   │   └── AppContext.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   └── MainApp.tsx           # Top-level page component
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml                # Production: Nginx + backend + PostgreSQL + Redis
├── docker-compose.dev.yml            # Development: same stack, hot-reload, different ports
├── Dockerfile                        # Backend production image (python:3.12-slim + ffmpeg)
├── Dockerfile.dev                    # Backend development image
├── Dockerfile.frontend               # Frontend multi-stage build (node:20-alpine + nginx:alpine)
├── nginx.conf                        # Reverse proxy: /api/ → backend:8000, SPA fallback
├── start-dev.sh                      # Build frontend + start dev compose
├── start-prod.sh                     # Build frontend + start prod compose
└── .env.example                      # Environment variable template
```

---

## Running Tests

```bash
source venv_transcriber/bin/activate
pytest backend/tests/ -v
```

Coverage report:

```bash
pytest backend/tests/ --cov=backend/src --cov-report=html
# Open htmlcov/index.html
```

---

## Contributing

1. Fork the repository and create a feature branch.
2. Follow the conventions in `CLAUDE.md`: surgical changes, minimum code, no speculative features.
3. Ensure existing tests pass and add tests for new behavior.
4. Open a pull request describing what changed and why.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
