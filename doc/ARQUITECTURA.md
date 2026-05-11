# Arquitectura de TranscriberApp - Versión Modular

## 📊 Diagrama de Dependencias

```
┌─────────────────────────────────────────────────────────────────┐
│                          main.js                                 │
│          (Punto de entrada - Orquestación)                      │
└────┬────────────────────────────────────────────────────────────┘
     │
     ├──→ domElements.js        [Referencias DOM]
     │
     ├──→ form.js              [Validación]
     │    └──→ utils.js
     │
     ├──→ recording.js         [Grabación]
     │    └──→ ui.js
     │        └──→ domElements.js
     │
     ├──→ fileHandling.js      [Archivos]
     │    ├──→ form.js
     │    ├──→ ui.js
     │    └──→ utils.js
     │
     ├──→ audioProcessing.js   [Procesamiento]
     │    ├──→ api.js
     │    ├──→ ui.js
     │    └──→ utils.js
     │
     ├──→ api.js               [Servidor]
     │    ├──→ ui.js
     │    └──→ utils.js
     │
     ├──→ chat.js              [Chat]
     │    ├──→ domElements.js
     │    ├──→ utils.js
     │    ├──→ api.js
     │    └──→ ui.js
     │
     ├──→ history.js           [Historial]
     │    ├──→ domElements.js
     │    ├──→ utils.js
     │    ├──→ historyStorage.js
     │    ├──→ form.js
     │    └──→ ui.js
     │
     └──→ historyStorage.js    [Base de datos]


```

## 🏗️ Capas de la Arquitectura

```
┌──────────────────────────────────────────────┐
│         PRESENTACIÓN (index.html)            │
├──────────────────────────────────────────────┤
│  UI Layer (ui.js, domElements.js)            │
│  - updateButton(), showOverlay()             │
│  - setStatusText(), togglePanel()            │
├──────────────────────────────────────────────┤
│  Business Logic (main.js)                    │
│  - handleSendAudio()                         │
│  - resetUI()                                 │
│  - saveToHistoryIfComplete()                 │
├──────────────────────────────────────────────┤
│  Feature Modules                             │
│  ┌──────────────────────────────────────┐   │
│  │ form.js  | recording.js | chat.js    │   │
│  │ history.js | fileHandling.js         │   │
│  └──────────────────────────────────────┘   │
├──────────────────────────────────────────────┤
│  Infrastructure                              │
│  ┌──────────────────────────────────────┐   │
│  │ api.js | historyStorage.js | utils.js│   │
│  └──────────────────────────────────────┘   │
├──────────────────────────────────────────────┤
│  External Services                           │
│  - Servidor Backend (/api/*)                 │
│  - IndexedDB                                 │
│  - MediaRecorder API                         │
│  - Fetch API                                 │
└──────────────────────────────────────────────┘
```

## 🔄 Flujos Principales

### 1. Flujo de Grabación y Envío

```
Usuario                 main.js                modules
  │                       │                       │
  ├─ Click "Grabar"───→ setupRecordingHandlers → recording.startRecording()
  │                       │                       │ (getUserMedia)
  │                       ├───────────────────→ ui.setStatusText("Grabando…")
  │                       │
  ├─ Click "Parar"────→ recording.stopRecording() → getRecordingBlob()
  │                       │
  │                       ├───────────────────→ ui.displayAudioPreview()
  │                       │
  ├─ Click "Enviar"───→ form.getFormValues()
  │                       │
  │                       ├───────────────────→ api.uploadAudio()
  │                       │                       │ (fetch POST)
  │                       │
  │                       ├───────────────────→ audioProcessing.startJobPolling()
  │                       │
  │                    (polling cada 3s)
  │                       │
  │                       ├───────────────────→ api.checkJobStatus()
  │                       │
  │                       ├─────────────────→ (cuando status="done")
  │                       │
  │                       ├───────────────────→ api.loadTranscriptionFile()
  │                       │
  │                       ├───────────────────→ historyStorage.saveTranscription()
  │
  │◀─────────────────────── UI actualizada
```

### 2. Flujo de Cargar del Historial

```
Usuario              main.js              history.js         historyStorage.js
  │                   │                      │                    │
  ├─ Click historial─→ setupHistoryHandlers  │                    │
  │                   │                      │                    │
  │                   ├─ toggleHistoryPanel──→ loadHistoryItems() │
  │                   │                      │                    │
  │                   │                      ├───────────────────→ getAllTranscriptions()
  │                   │                      │
  │                   │◀────── items ────────┤
  │
  │◀────── panel con items mostrado ────────┤
  │
  ├─ Click item───────→ loadTranscriptionFromHistory(id)
  │                      │
  │                      ├─────────────────────────────────→ getTranscriptionById(id)
  │                      │
  │                      ├─ renderiza nombre
  │                      ├─ renderiza transcripción
  │                      ├─ renderiza resúmenes en multiResults
  │
  │◀──────── transcripción cargada ────────┤
```

### 3. Flujo de Chat

```
Usuario              main.js            chat.js            api.js
  │                   │                   │                  │
  ├─ Escribe msg──→ setupChatHandlers    │                  │
  │                   │                   │                  │
  ├─ Click enviar─→ addMessage()       ─→ addMessage()     │
  │                   │                   │                  │
  │                   │                ─→ sendMessage()     │
  │                   │                   │                  │
  │                   │                   ├────────────────→ chatStream()
  │                   │                   │                  │ (fetch streaming)
  │                   │                   │ ◀───── parcial ──┤
  │                   │                   │
  │                   │                   ├─ actualiza UI
  │                   │                   │  (en vivo con <pre>)
  │                   │                   │
  │                   │                   ├─ renderiza markdown
  │                   │
  │◀──────── respuesta mostrada ────────┤
```

## 📦 Dependencias Entre Módulos

```
domElements.js
  ↑
  ├── ui.js
  ├── form.js
  ├── fileHandling.js
  ├── chat.js
  ├── history.js
  └── recording.js

utils.js
  ↑
  ├── ui.js
  ├── form.js
  ├── fileHandling.js
  ├── api.js
  ├── chat.js
  ├── history.js
  ├── audioProcessing.js
  └── recordning.js

api.js
  ↑
  ├── audioProcessing.js
  ├── chat.js
  ├── main.js
  └── history.js

historyStorage.js
  ↑
  ├── history.js
  └── main.js

Independientes (sin dependencias):
  - recording.js (solo usa domElements.js y ui.js)
  - fileHandling.js (múltiples dependencias)
```

## 🧬 Estructura de Estado

```
main.js (Estado Global)
  ├── lastRecordingBlob: Blob | null
  ├── lastRecordingName: string
  ├── lastRecordingDuration: number | null
  ├── hasTranscript: boolean
  └── ultimoModoProcesado: string | null

Elements (domElements.js)
  ├── Botones
  ├── Formulario
  ├── Chat
  ├── Historial
  └── Resultados

Almacenamiento (historyStorage.js)
  └── IndexedDB
      ├── id: string (SHA-256)
      ├── nombre: string
      ├── fecha: ISO string
      ├── duracion: number
      ├── grabacion: Blob
      ├── transcripcion: string[]
      └── resumenes: { [modo]: markdown }
```

## 🎯 Responsabilidades por Módulo

| Módulo | Responsabilidad | Entrada | Salida |
|--------|-----------------|---------|--------|
| domElements.js | Referencias DOM | - | { elements, functions } |
| utils.js | Funciones auxiliares | datos | datos procesados |
| ui.js | Actualizar interfaz | estado | DOM actualizado |
| form.js | Validar formulario | valores | { valid, values } |
| recording.js | Grabar audio | evento | Blob |
| fileHandling.js | Descargar/subir archivos | archivo | estado |
| api.js | Comunicar con servidor | datos | Promise<response> |
| audioProcessing.js | Procesar audio | jobId | estado final |
| chat.js | Panel de chat | mensaje | respuesta IA |
| history.js | Panel de historial | id | transcripción |
| historyStorage.js | Persistencia BD | registro | Promise<void> |
| main.js | Orquestación | eventos | aplicación corriendo |

## 🚀 Ventajas de esta Arquitectura

✅ **Separación de responsabilidades** - Cada módulo hace una cosa bien  
✅ **Bajo acoplamiento** - Los módulos son independientes  
✅ **Alta cohesión** - Funciones relacionadas en el mismo módulo  
✅ **Testeable** - Fácil hacer unit tests de cada módulo  
✅ **Mantenible** - Código legible y organizado  
✅ **Escalable** - Fácil agregar nuevos módulos  
✅ **Reutilizable** - Funciones pueden usarse en otros proyectos  

## 📋 Checklist de Calidad

- [x] Cada módulo tiene una responsabilidad clara
- [x] No hay código duplicado
- [x] Las funciones son pequeñas y enfocadas
- [x] Los imports son explícitos
- [x] No hay dependencias circulares
- [x] Hay documentación JSDoc
- [x] El flujo de datos es claro
- [x] Es fácil agregar tests

---

Versión: 1.0  
Última actualización: 5 de febrero de 2026
