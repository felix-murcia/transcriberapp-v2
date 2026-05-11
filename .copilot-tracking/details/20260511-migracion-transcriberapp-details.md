<!-- markdownlint-disable-file -->

# Task Details: Migración de TranscriberApp

## Research Reference

**Source Research**: #file:../research/20260511-migracion-transcriberapp-research.md

## Phase 1: Inventario y Diseño de Arquitectura

### Task 1.1: Generar listado de módulos y dependencias

Ejecutar `tree` y `pipdeptree` para obtener el árbol de paquetes y dependencias.

- **Files**:
  - `transcriber_app/` – código fuente actual.
  - `requirements.txt` – lista de paquetes Python.
- **Success**:
  - Archivo `inventory.txt` generado con listado completo.
  - Dependencias críticas identificadas (FastAPI, ffmpeg, Gemini, Groq).
  - Referencia: #file:../research/20260511-migracion-transcriberapp-research.md (Lines 23-30)

### Task 1.2: Definir paquetes `src/domain`, `src/application`, `src/infrastructure`

Diseñar estructura siguiendo arquitectura hexagonal.

- **Files**:
  - Crear directorio `src/` con sub‑carpetas `domain/`, `application/`, `infrastructure/`.
  - Mover módulos existentes a los paquetes correspondientes.
- **Success**:
  - Estructura de carpetas creada y añadida al control de versiones.
  - Importaciones actualizadas sin errores.
  - Referencia: #file:../research/20260511-migracion-transcriberapp-research.md (Lines 34-45)

## Phase 2: Refactorización del Backend

### Task 2.1: Mover lógica de IA a `src/application`

Transferir `modules/ai/` a `src/application/ai/` manteniendo la interfaz del `AIManager`.

- **Files**:
  - `src/application/ai/ai_manager.py`
  - `src/application/ai/gemini/client.py`
  - `src/application/ai/groq/transcriber.py`
- **Success**:
  - Todas las pruebas de IA pasan.
  - No se rompe la API pública.
  - Referencia: #file:../research/20260511-migracion-transcriberapp-research.md (Lines 50-60)

### Task 2.2: Reubicar adaptadores de audio a `src/infrastructure`

Mover `modules/audio_receiver.py` y utilidades de ffmpeg a `src/infrastructure/audio/`.

- **Files**:
  - `src/infrastructure/audio/audio_receiver.py`
  - `src/infrastructure/audio/ffmpeg_helper.py`
- **Success**:
  - Conversión a WAV funciona correctamente.
  - Integración con `AIManager` sin cambios de comportamiento.
  - Referencia: #file:../research/20260511-migracion-transcriberapp-research.md (Lines 61-70)

### Task 2.3: Actualizar CLI usando `typer`

Reescribir `main.py` para usar `typer` y apuntar a los nuevos paquetes.

- **Files**:
  - `src/cli/main.py`
- **Success**:
  - CLI muestra ayuda y ejecuta comandos sin errores.
  - Compatibilidad con los modos existentes.
  - Referencia: #file:../research/20260511-migracion-transcriberapp-research.md (Lines 71-80)

## Phase 3: Migración del Frontend

### Task 3.1: Crear proyecto React/Vite en `frontend/`

Inicializar proyecto con `npm create vite@latest frontend --template react-ts`.

- **Files**:
  - `frontend/src/App.tsx`
  - `frontend/src/api.ts` – cliente para FastAPI.
- **Success**:
  - Aplicación compila y sirve en `http://localhost:5173`.
  - Conexión básica con endpoint `/api/status` funciona.
  - Referencia: #file:../research/20260511-migracion-transcriberapp-research.md (Lines 85-95)

### Task 3.2: Consumir API `/api` desde la SPA

Implementar llamadas a los endpoints de transcripción y chat.

- **Files**:
  - `frontend/src/components/UploadAudio.tsx`
  - `frontend/src/components/Chat.tsx`
- **Success**:
  - Subida de audio y recepción de resultados en la UI.
  - Manejo de errores y estados de carga.
  - Referencia: #file:../research/20260511-migracion-transcriberapp-research.md (Lines 96-110)

## Dependencies

- Python 3.11, virtualenv `venv_transcriber`
- Node.js 20, npm
- Docker & Docker‑Compose (o Helm para K8s)
- ffmpeg en host

## Success Criteria

- Inventario completo generado.
- Estructura hexagonal implementada y compilable.
- CLI funcional con `typer`.
- Frontend React operativo y conectado a la API.
- Todas las pruebas pasan (`pytest -q`).