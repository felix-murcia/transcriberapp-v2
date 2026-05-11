
<!-- markdownlint-disable-file -->

# Investigación: Migración de TranscriberApp (legacy) a nueva estructura

## Fecha
2026-05-11

## Alcance
Documentar todo lo necesario para migrar la aplicación legacy ubicada en `~/Public/transcriberapp` a la nueva estructura descrita en `TODO.md`.

## Herramientas y Entorno
- Sistema operativo: Linux
- Python 3.11 (virtualenv `venv_transcriber`)
- Dependencias del proyecto (`requirements.txt`)
- Docker & Docker‑Compose (para entornos de desarrollo y producción)
- FastAPI, Uvicorn, ffmpeg, Gemini API, Groq Whisper API

## Análisis de la Estructura Actual
*(Revisar árbol de directorios y archivos clave del proyecto legacy)*

### Archivos y Directorios Principales
- `transcriber_app/` – paquete Python principal
  - `modules/` – módulos de audio, IA, etc.
  - `web/` – capa FastAPI y frontend estático
  - `config.py` – configuración de modos de resumen
  - `main.py` – CLI de procesamiento
- `requirements.txt` – dependencias Python
- `docker-compose.yml` – definición de contenedores
- `README.md` – instrucciones de uso

## Nueva Estructura Deseada (según TODO.md)
*(Copiar aquí la lista de carpetas/archivos esperados en la nueva arquitectura)*

## Comparación de Estructuras
| Elemento | Legacy | Nuevo | Acción requerida |
|----------|--------|-------|------------------|
| `modules/` | Sí | `src/` (separar dominio, infraestructura, aplicación) | Reorganizar paquetes
| `web/` | Sí | `frontend/` (React/Vite) | Migrar a SPA moderna
| Configuración | `.env` + `config.py` | `config/` (YAML) | Convertir
| Docker | `docker-compose.yml` | `infra/` (K8s manifests) | Adaptar

## Pasos Propuestos de Migración
1. **Inventario de código** – generar listado de módulos y dependencias.
2. **Diseño de nueva arquitectura** – definir paquetes `src/domain`, `src/application`, `src/infrastructure` siguiendo principios hexagonales.
3. **Refactorizar módulos** – mover lógica de IA a `src/application`, adaptadores de audio a `src/infrastructure`.
4. **Actualizar CLI** – usar `typer` y apuntar a nuevos paquetes.
5. **Migrar API FastAPI** – reorganizar routers bajo `src/api`, mantener compatibilidad.
6. **Frontend** – crear proyecto React/Vite, consumir API `/api`.
7. **Configuración** – migrar variables a `config/settings.yaml` y usar `pydantic-settings`.
8. **Docker/K8s** – crear `Dockerfile` modular, Helm charts.
9. **Pruebas** – actualizar/añadir pruebas unitarias y de integración.
10. **Documentación** – actualizar `README.md`, generar diagramas de arquitectura.

## Evidencia y Referencias
- **Código fuente**: revisar archivos en `transcriber_app/`.
- **Documentación existente**: `CLAUDE.md`, `README.md`, `doc/`.
- **Ejemplos de migración**: buscar en internet proyectos similares (FastAPI + React).
- **Buenas prácticas**: hexagonal architecture, clean architecture, Docker best practices.

## Preguntas Abiertas / Sugerencias
- ¿Se mantiene el mismo modelo de IA (Gemini/Groq) o se cambiará?
- ¿Se desea mantener el mismo endpoint `/api` o redefinirlo?
- ¿Qué nivel de compatibilidad con versiones anteriores se requiere?
- ¿Se migrará a Kubernetes o se quedará con Docker‑Compose?

## Próximos Pasos
1. Completar el inventario de archivos (script `tree` y `grep`).
2. Definir el esquema de paquetes en `src/`.
3. Generar plan de tareas detallado (se crearán archivos de plan, detalles y prompt).
