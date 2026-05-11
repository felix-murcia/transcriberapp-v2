# Guía Rápida de Módulos JavaScript

## 📂 Estructura de Archivos

```
modules/
├── domElements.js       ← Referencias a elementos HTML
├── utils.js            ← Funciones auxiliares
├── ui.js               ← Actualización de la interfaz visual
├── form.js             ← Validación del formulario
├── recording.js        ← Grabación de audio
├── fileHandling.js     ← Descarga/carga de archivos
├── api.js              ← Peticiones al servidor
├── audioProcessing.js  ← Procesamiento de audio
├── chat.js             ← Funcionalidad de chat
├── history.js          ← Panel de historial
└── historyStorage.js   ← Almacenamiento en IndexedDB
```

---

## 🔍 Cómo Usar Cada Módulo

### domElements.js - Referencias DOM
```javascript
import { elements, getModalElements } from "./modules/domElements.js";

// Acceder a elementos
elements.recordBtn.click();
const { modal, confirmBtn } = getModalElements();
```

### utils.js - Funciones Auxiliares
```javascript
import { parseMarkdown, normalizeText, isValidEmail } from "./modules/utils.js";

const html = parseMarkdown("# Título");
const normalized = normalizeText("José García"); // "jose garcia"
if (isValidEmail(email)) { /* ... */ }
```

### ui.js - Interfaz Visual
```javascript
import { showOverlay, updateSendButtonState } from "./modules/ui.js";

showOverlay();
updateSendButtonState(hasAudio, nombre, email, modo);
```

### form.js - Validación de Formulario
```javascript
import { validateSessionName, getFormValues } from "./modules/form.js";

const { nombre, email, modo } = getFormValues();
validateSessionName(nombre);
```

### recording.js - Grabación
```javascript
import { startRecording, stopRecording, getRecordingBlob } from "./modules/recording.js";

// Iniciar grabación
startRecording(); // Solicita permisos del micrófono

// Obtener blob después de detener
stopRecording();
const blob = getRecordingBlob();
```

### fileHandling.js - Archivos
```javascript
import { downloadRecording, deleteRecording } from "./modules/fileHandling.js";

// Descargar grabación
downloadRecording(audioBlob);

// Eliminar (pide confirmación)
deleteRecording(() => {
    // Callback después de eliminar
});
```

### api.js - Servidor
```javascript
import { uploadAudio, checkJobStatus } from "./modules/api.js";

// Enviar audio
const result = await uploadAudio(blob, nombre, modo, email);
if (result.success) {
    startJobPolling(result.jobId);
}

// Verificar estado
const status = await checkJobStatus(jobId);
```

### audioProcessing.js - Procesamiento
```javascript
import { startJobPolling } from "./modules/audioProcessing.js";

startJobPolling(jobId, 
    (data) => console.log("Completado", data),
    (error) => console.error("Error", error)
);
```

### chat.js - Chat
```javascript
import { sendMessage, addMessage } from "./modules/chat.js";

// Enviar mensaje
await sendMessage();

// Agregar mensaje manualmente
addMessage("Hola", "user");
```

### history.js - Historial
```javascript
import { loadTranscriptionFromHistory } from "./modules/history.js";

// Cargar transcripción del historial
await loadTranscriptionFromHistory(id);
```

### historyStorage.js - Almacenamiento
```javascript
import { saveTranscription, getAllTranscriptions } from "./modules/historyStorage.js";

// Guardar
await saveTranscription({
    id: "abc123",
    nombre: "reunion",
    fecha: new Date().toISOString(),
    transcripcion: ["texto..."],
    resumenes: { tecnico: "resumen..." }
});

// Obtener todas
const items = await getAllTranscriptions();
```

---

## 🔗 Flujos Comunes

### Flujo 1: Grabar y Enviar Audio

```javascript
// 1. Usuario hace click en grabar
await startRecording();

// 2. Usuario detiene
stopRecording();
const blob = getRecordingBlob();
lastRecordingBlob = blob;

// 3. Usuario hace click en enviar
const result = await uploadAudio(blob, nombre, modo, email);
if (result.success) {
    startJobPolling(result.jobId, async (data) => {
        // 4. Job completado
        await saveToHistoryIfComplete();
    });
}
```

### Flujo 2: Cargar del Historial

```javascript
// 1. Usuario abre panel de historial
await loadHistoryItems();

// 2. Usuario selecciona una transcripción
await loadTranscriptionFromHistory(id);

// 3. La transcripción se renderiza en la UI
// - Nombre se auto-completa
// - Transcripción aparece
// - Resúmenes aparecen en multiResults
```

### Flujo 3: Chatear

```javascript
// 1. Usuario escribe un mensaje
const msg = elements.chatInput.value;

// 2. Se envía al servidor
await sendMessage();

// 3. Se muestra respuesta con streaming
// - Primero en <pre> en vivo
// - Luego se renderiza como markdown
```

---

## 📋 Checklist para Nuevas Funcionalidades

- [ ] ¿Necesito referencias DOM? → Usa `domElements.js`
- [ ] ¿Es una validación? → Usa `form.js`
- [ ] ¿Es manipulación de UI? → Usa `ui.js`
- [ ] ¿Es una llamada al servidor? → Usa `api.js`
- [ ] ¿Es procesamiento de audio? → Usa `recording.js` o `audioProcessing.js`
- [ ] ¿Es texto/datos? → Usa `utils.js`
- [ ] ¿Debo guardar en BD? → Usa `historyStorage.js`

---

## 🐛 Debugging

### Verificar que los módulos están cargados
```javascript
// En consola del navegador
window.console.log("Modules loaded"); // Aparecerá en main.js init()
```

### Ver el estado global
```javascript
// En consola, en main.js context
// lastRecordingBlob, lastRecordingName, hasTranscript, etc.
```

### Validar referencias DOM
```javascript
import { validateElements } from "./modules/domElements.js";
validateElements(); // Muestra elementos faltantes en consola
```

---

## ⚡ Performance

- Los módulos se cargan bajo demanda (ES6 imports)
- Solo se cargan cuando se necesitan
- No hay código duplicado
- Cada función tiene una responsabilidad clara

---

## 📞 Soporte

En caso de problemas:
1. Revisa la consola del navegador (F12)
2. Verifica que todos los archivos están en `modules/`
3. Comprueba que `main.js` importa correctamente
4. Valida que el HTML importa `main.js` (no `recorder.js`)

Ver [REFACTORIZATION.md](./REFACTORIZATION.md) para más detalles.
