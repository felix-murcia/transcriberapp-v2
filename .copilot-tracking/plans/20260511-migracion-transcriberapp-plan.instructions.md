---
applyTo: ".copilot-tracking/changes/20260511-migracion-transcriberapp-changes.md"
---

<!-- markdownlint-disable-file -->

# Task Checklist: Migración de TranscriberApp a nueva estructura

## Overview

Migrar la aplicación legacy `transcriberapp` a la arquitectura propuesta en `TODO.md`.

## Objectives

- Reorganizar el código fuente siguiendo una arquitectura hexagonal.
- Migrar el frontend a una SPA moderna (React/Vite).
- Actualizar la configuración a archivos YAML y usar `pydantic-settings`.
- Adaptar la infraestructura a Docker‑Compose o Kubernetes según decisión.
- Mantener la funcionalidad de IA (Gemini/Groq) sin interrupciones.

## Research Summary

### Project Files
- `transcriber_app/` – paquete principal con módulos de audio, IA y API en legacy.
- `requirements.txt`, `docker-compose.yml`, `CLAUDE.md`.

### External References
- #file:../research/20260511-migracion-transcriberapp-research.md - Investigación completa de la migración.
- #githubRepo:"github.com/felix/transcriberapp" "fastapi react migration" - Patrón de migración FastAPI + React.
- #fetch:https://fastapi.tiangolo.com/ - Documentación oficial de FastAPI.

### Standards References
- #file:../../copilot/python.md - Convenciones de código Python.
- #file:../../.github/instructions/python-project.instructions.md - Guía de proyecto Python.

## Implementation Checklist

### [ ] Phase 1: Inventario y Diseño de Arquitectura

- [ ] Task 1.1: Generar listado de módulos y dependencias.
  - Details: .copilot-tracking/details/20260511-migracion-transcriberapp-details.md (Lines 1-30)
- [ ] Task 1.2: Definir paquetes `src/domain`, `src/application`, `src/infrastructure`.
  - Details: .copilot-tracking/details/20260511-migracion-transcriberapp-details.md (Lines 31-60)

### [ ] Phase 2: Refactorización del Backend

- [ ] Task 2.1: Mover lógica de IA a `src/application`.
  - Details: .copilot-tracking/details/20260511-migracion-transcriberapp-details.md (Lines 61-90)
- [ ] Task 2.2: Reubicar adaptadores de audio a `src/infrastructure`.
  - Details: .copilot-tracking/details/20260511-migracion-transcriberapp-details.md (Lines 91-120)
- [ ] Task 2.3: Actualizar CLI usando `typer`.
  - Details: .copilot-tracking/details/20260511-migracion-transcriberapp-details.md (Lines 121-150)

### [ ] Phase 3: Migración del Frontend

- [ ] Task 3.1: Crear proyecto React/Vite en `frontend/`.
  - Details: .copilot-tracking/details/20260511-migracion-transcriberapp-details.md (Lines 151-180)
- [ ] Task 3.2: Consumir API `/api` desde la SPA.
  - Details: .copilot-tracking/details/20260511-migracion-transcriberapp-details.md (Lines 181-210)

## Dependencies

- Python 3.11, virtualenv `venv_transcriber`
- Node.js 20, npm
- Docker & Docker‑Compose (o Helm para K8s)
- ffmpeg instalado en el host

## Success Criteria

- Código compilado y pruebas unitarias pasan.
- API funciona con el nuevo frontend.
- Documentación actualizada y diagramas generados.