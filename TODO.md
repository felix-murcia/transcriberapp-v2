## Proyecto transcriberapp-v2

Se trata de rehacer la aplicación transcriberapp con tecnologías modernas backend python y frontend react.

Actualmente, en la aplicación legacy,  las sesiones se guardan a nivel de navegador en un indexdb. Necesitaría implementar un sistema de gestion de usuarios y gestionar las sesiones a nivel de usuario. Es decir, todas las transcripciones y conversaciones con el agente por cada transcripcion sería guardada en una bbdd no en el indexdb. para que el usuario pudiera ver sus transcripciones en cualquier dispositivo, no solamente donde en el dispositivo donde haya hecho la transcripcion. Necesito un informe de requisitos de negocio para llevar a cabo esta nueva adaptación

Antes de comenzar el desarrollo, hay que tener muy claro el funcionamiento de la aplicación legacy. El proyecto legacy lo puedes encontrar en ~/Public/transcriberapp. En el directorio actual está la documentación del en formato md del proyecto legacy, pero lo mejor es inspeccionar completamente la estructura del proyecto original en ~/Public/transcriberapp.

## Documentos de referencia

~/Public/transcriberapp$ ls *.md
AGENTS.md  CLAUDE.md  MIGRATION_SUMMARY.md  README.md

~/Public/transcriberapp$ ls doc/*.md
doc/ANTES_DESPUES_STATIC.md  doc/CHECKLIST_REORGANIZACION.md  doc/MODULOS_GUIA.md              doc/REFACTORIZACION_MODOS_PROCESADOS.md  doc/RESUMEN_EJECUTIVO.md
doc/ARQUITECTURA.md          doc/DOCUMENTACION_INDICE.md      doc/REFACTORIZACION_COMPLETA.md  doc/REFACTORIZATION.md                   doc/VERIFICACION_REFACTORACION.md
doc/CHECKLIST_MIGRACION.md   doc/ESTRUCTURA_STATIC.md         doc/REFACTORIZACION_MAIN_JS.md   doc/REFERENCIA_PROCESSEDMODES.md

## Informe de Requisitos de Negocio  
**Proyecto:** TranscriberApp – Persistencia de transcripciones y conversaciones a nivel de usuario  
**Fecha:** 11 de mayo de 2026  

---

### 1. Visión del producto
Permitir que los usuarios registrados accedan a todas sus transcripciones y chats con el agente IA desde cualquier dispositivo, sustituyendo el almacenamiento actual en **IndexedDB** (navegador) por una base de datos centralizada y segura.

### 2. Stakeholders
| Stakeholder | Necesidad / Valor |
|-------------|-------------------|
| **Usuario final** | Acceso a historial completo, sincronización entre dispositivos, posibilidad de buscar y organizar transcripciones. |
| **Equipo de producto** | Diferenciación competitiva, mayor retención de usuarios, datos para métricas de uso. |
| **Equipo de desarrollo** | Arquitectura clara, API reutilizable, pruebas automatizadas. |
| **Equipo de seguridad / cumplimiento** | Protección de datos personales (GDPR, CCPA), gestión de consentimientos, auditoría de accesos. |
| **Operaciones / DevOps** | Escalabilidad, monitoreo, backup y recuperación. |

### 3. Requisitos funcionales (RF)

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| **RF‑01** | **Registro y autenticación** de usuarios (email + contraseña, OAuth opcional – Google, GitHub). | Alta |
| **RF‑02** | **Gestión de sesión** mediante tokens JWT (acceso y refresh) con expiración configurable. | Alta |
| **RF‑03** | **Persistencia de transcripciones**: cada archivo de audio procesado genera un registro con: <br>• ID único, <br>• usuario ID, <br>• fecha/hora, <br>• modo de resumen, <br>• texto transcrito, <br>• metadata (duración, tamaño, modelo usado). | Alta |
| **RF‑04** | **Persistencia de conversaciones** (chat con Gemini): almacenar cada mensaje (role, contenido, timestamp) enlazado a la transcripción correspondiente. | Alta |
| **RF‑05** | **API REST** para crear, leer, actualizar y eliminar (CRUD) transcripciones y chats. Endpoints: `/api/v1/users`, `/api/v1/transcriptions`, `/api/v1/conversations`. | Alta |
| **RF‑06** | **Listado y filtrado**: paginación, búsqueda por nombre, fecha, modo, palabras clave. | Media |
| **RF‑07** | **Exportación**: permitir descargar una transcripción (JSON/Markdown/PDF). | Media |
| **RF‑08** | **Control de acceso**: solo el propietario puede leer/modificar sus datos; admins pueden ver métricas globales. | Alta |
| **RF‑09** | **Sincronización automática**: al iniciar sesión, la UI carga el historial del usuario desde la base de datos. | Alta |
| **RF‑10** | **Notificaciones** (opcional): alertar al usuario cuando una transcripción está lista. | Baja |
| **RF‑11** | **Gestión de cuenta**: cambiar contraseña, eliminar cuenta (borrado en cascada de sus datos). | Media |
| **RF‑12** | **Auditoría**: registrar eventos críticos (login, creación de transcripción, borrado). | Media |

### 4. Requisitos no funcionales (RNF)

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| **RNF‑01** | **Escalabilidad**: la solución debe soportar al menos **10 000 usuarios activos** y **100 000 transcripciones** sin degradación. |
| **RNF‑02** | **Disponibilidad**: 99.9 % de uptime del API de persistencia. |
| **RNF‑03** | **Seguridad**: cifrado en tránsito (TLS 1.3) y en reposo (AES‑256). Contraseñas con hashing bcrypt/argon2. |
| **RNF‑04** | **Cumplimiento**: GDPR‑ready – permitir exportar y borrar datos bajo solicitud del usuario. |
| **RNF‑05** | **Performance**: tiempo de respuesta < 300 ms para listados paginados; < 1 s para crear una transcripción (excluyendo tiempo de IA). |
| **RNF‑06** | **Observabilidad**: logs estructurados, métricas (requests, latencia, errores) y trazas distribuidas. |
| **RNF‑07** | **Portabilidad**: la capa de persistencia debe estar desacoplada (DAO) para poder cambiar de PostgreSQL a otro RDBMS o a un NoSQL en el futuro. |
| **RNF‑08** | **Mantenibilidad**: código con pruebas unitarias (≥ 80 % cobertura) y documentación OpenAPI. |
| **RNF‑09** | **Costo**: usar una base de datos gestionada (ej. **Supabase**, **Amazon RDS**, **Azure PostgreSQL**) con modelo de pago por uso. |

### 5. Arquitectura propuesta

```
+-------------------+          +-------------------+          +-------------------+
|  Frontend (SPA)   |  <--->   |  API FastAPI      |  <--->   |  PostgreSQL DB    |
|  (React/TS)      |  HTTP    |  (auth, trans‑   |  SQL     |  (users,         |
|  - Auth (JWT)     |  (REST)  |   cribe, chat)   |          |   transcriptions,|
|  - UI list/filter |          |  - Pydantic models|          |   conversations) |
+-------------------+          +-------------------+          +-------------------+

```

- **Auth**: FastAPI‑Users o custom JWT con `python-jose`.  
- **ORM**: SQLAlchemy + Alembic para migraciones.  
- **Persistencia de archivos**: los audios originales pueden seguir almacenándose en **PVC** (Kubernetes) o en **object storage** (S3‑compatible) y guardar solo la URL en la tabla de transcripciones.  
- **Background tasks**: el orquestador seguirá ejecutando la transcripción y, al terminar, guardará el resultado en la DB.  

### 6. Impacto en funcionalidades existentes

| Área | Cambios requeridos |
|------|--------------------|
| **Frontend** | Reemplazar llamadas a `localStorage/IndexedDB` por fetch a `/api/v1/transcriptions`. Añadir login/logout UI, pantalla de historial, filtros. |
| **Backend** | Añadir routers de usuarios y autenticación, modelos de DB, migraciones, middleware de autorización. Modificar `Orchestrator` para que, al finalizar, invoque un servicio de guardado (`TranscriptionRepository.save(...)`). |
| **Infraestructura** | Provisionar base de datos (PostgreSQL) y secret de conexión. Actualizar `docker‑compose.yml` y manifiestos K8s. |
| **Testing** | Nuevas pruebas de integración para endpoints protegidos y para la lógica de guardado. |
| **Documentación** | Actualizar README, OpenAPI spec y guías de despliegue. |

### 7. Roadmap (sprints de 2 semanas)

| Sprint | Objetivo | Entregables |
|--------|----------|-------------|
| **1** | **Fundamentos de Auth** | Registro, login, generación/validación de JWT; modelo `User`. |
| **2** | **Persistencia de transcripciones** | Tablas `transcriptions`, endpoint `POST /transcriptions`, guardado desde orquestador. |
| **3** | **Persistencia de conversaciones** | Tabla `conversations`, endpoint `GET /conversations/{transcription_id}`. |
| **4** | **Frontend – historial** | UI de listado, filtros, paginación; integración con API. |
| **5** | **Seguridad y cumplimiento** | Encriptado, GDPR export/delete, auditoría de eventos. |
| **6** | **Escalado y observabilidad** | Métricas Prometheus, logs estructurados, pruebas de carga. |
| **7** | **Beta interna** | Pruebas de usuarios reales, feedback, corrección de bugs. |
| **8** | **Release** | Deploy a producción, documentación final, plan de monitoreo. |

### 8. Métricas de éxito

| Métrica | Umbral objetivo |
|---------|-----------------|
| **Retención de usuarios** (30 d) | + 15 % respecto a la versión actual |
| **Tiempo medio de carga del historial** | < 500 ms |
| **Número de transcripciones por usuario** | ≥ 5 en 3 meses |
| **Incidentes de seguridad** | 0 críticos |
| **Cobertura de pruebas** | ≥ 80 % |

### 9. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Sobrecarga de la DB** | Media | Alta | Dimensionar autoscaling, usar índices en columnas de filtro (user_id, created_at). |
| **Fuga de datos personales** | Baja | Crítica | Encriptado, auditoría, pruebas de penetración, política de retención. |
| **Complejidad de migración** | Media | Media | Implementar migraciones con Alembic, pruebas de rollback. |
| **Resistencia del usuario a crear cuenta** | Media | Media | Ofrecer registro social (Google) y opción de “guest” que sincroniza al crear cuenta. |
| **Costos de almacenamiento** | Baja | Media | Guardar solo URLs a objetos en S3, aplicar lifecycle policies. |

### 10. Recomendación
Implementar la capa de gestión de usuarios y persistencia centralizada es **estratégicamente valiosa** y técnicamente viable con la stack actual (FastAPI, PostgreSQL). El esfuerzo estimado es de **≈ 8 semanas** (4 sprints) y aporta mejoras de usabilidad, retención y cumplimiento regulatorio.

--- 

**Próximos pasos sugeridos**

1. Aprobar el roadmap y asignar recursos.  
2. Crear la base de datos (PostgreSQL) y añadir los secrets al entorno (`DATABASE_URL`).  
3. Iniciar el Sprint 1 con la implementación de autenticación.  
 
