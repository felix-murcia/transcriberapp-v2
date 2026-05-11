
![CI](https://github.com/FelixMarin/transcriberapp/actions/workflows/ci.yml/badge.svg) ![Coverage](./coverage.svg)
# **TranscriberApp**

TranscriberApp es una aplicación web moderna para transcribir audios, generar resúmenes inteligentes y conversar con un asistente IA contextual.  
Toda la inteligencia se ejecuta mediante **APIs externas**:

- **Groq Whisper** para transcripción  
- **Gemini** para resumen, análisis y chat  

La aplicación está diseñada para ejecutarse de forma estable en **Kubernetes**, con almacenamiento persistente y acceso seguro mediante **Tailscale + HTTPS**.

![Imagen de muestra](https://raw.githubusercontent.com/FelixMarin/transcriberapp/refs/heads/main/screen1.jpg)

---

## 🚀 Características principales

- Transcripción de audio vía **Groq Whisper API**  
- Resumen y análisis con **Gemini**  
- Chat IA con streaming de tokens  
- Interfaz web ligera (HTML/JS)  
- Resultados persistentes en PVCs  
- HTTPS automático con certificados de Tailscale  
- API REST con FastAPI  
- Arquitectura modular y extensible  

---

## **Time Line**
-  [Documentos de desarrollo](https://github.com/FelixMarin/transcriberapp/tree/main/doc)

---

## 🖥️ Compatibilidad

- Linux  
- macOS  
- Windows  
- Kubernetes (k3s, k8s estándar, MicroK8s, etc.)  
- Python 3.10  

> No requiere GPU, CUDA ni dependencias de hardware específicas.

---

## 📦 Stack tecnológico

### Backend
- FastAPI  
- Groq Whisper API  
- Gemini (Google Generative AI)  
- Requests / HTTPX  
- FastAPI-Mail  

### Frontend
- HTML / CSS / JavaScript  
- Streaming SSE  
- Renderizado Markdown  
- Overlay de carga  
- Impresión PDF  

### Infraestructura
- Kubernetes  
- PVCs para audios, transcripts y outputs  
- Tailscale para HTTPS  
- NodePort para exposición del servicio  

---

## 🏗️ Estructura del proyecto (carpetas principales)

```
TranscriberApp/
├── audios/
├── transcripts/
├── outputs/
├── k3s/
├── transcriber_app/
│   ├── modules/
│   ├── web/
│   ├── runner/
│   └── main.py
├── requirements.txt
├── README.md
└── .env
```

---

## ⚙️ Instalación (desarrollo local)

```bash
git clone <repositorio>
cd TranscriberApp

python3 -m venv venv_transcriber
source venv_transcriber/bin/activate

pip install -r requirements.txt
```

Configurar API Keys:

```bash
echo "GROQ_API_KEY=tu_clave" >> .env
echo "GOOGLE_API_KEY=tu_clave" >> .env
```

---

## 🎯 Modos disponibles

| Modo | Descripción |
|------|-------------|
| `default` | Resumen general |
| `tecnico` | Resumen técnico |
| `refinamiento` | Tareas, backlog, decisiones |
| `ejecutivo` | Resumen corto |
| `bullet` | Puntos clave |

---

## 🚀 Ejecución local

### CLI

```bash
python -m transcriber_app.main audio ejemplo tecnico
```

### Web API

```bash
uvicorn transcriber_app.web.web_app:app --host 0.0.0.0 --port 9000
```

Acceso:

```
http://localhost:9000
```

---

# ☸️ Despliegue en Kubernetes

TranscriberApp está diseñada para ejecutarse de forma estable en Kubernetes.

### Componentes incluidos:

- **Deployment**  
- **Service NodePort**  
- **PVCs**  
- **Secrets**  
- **Certificados Tailscale** montados desde el host  

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: transcriberapp-secrets
type: Opaque
stringData:
  groq_api_key: "GSK_XXXX"
  google_api_key: "AIzaXXXX"
```

### Certificados Tailscale

Montados desde:

```
/var/lib/tailscale/certs
```

### Acceso final

```
https://ubuntu.tailXXXX.ts.net:30090/
```

---

# 🔐 HTTPS con Tailscale

### Generar certificado

```
sudo tailscale cert ubuntu.tailXXXX.ts.net
```

Esto crea:

```
/var/lib/tailscale/certs/ubuntu.tailXXXX.ts.net.crt
/var/lib/tailscale/certs/ubuntu.tailXXXX.ts.net.key
```

El Deployment monta estos archivos en `/certs`.

---

# 📁 Estructura de salida

```
transcripts/
outputs/
```

---

# 🧪 Tests unitarios y de integración

TranscriberApp incluye una batería completa de tests:

- Tests unitarios de módulos internos  
- Tests de integración del pipeline  
- Tests del frontend (JS)  
- Tests del backend (FastAPI)  

### Ejecutar tests

```bash
pytest -q
```

### Ejecutar tests con cobertura

```bash
pytest --cov=transcriber_app
```

---

# 🧠 Configuración avanzada

Variables en `.env`:

```bash
GROQ_API_KEY=...
GOOGLE_API_KEY=...
SMTP_HOST=...
SMTP_PORT=465
SMTP_USER=...
SMTP_PASS=...
USE_MODEL=gemini-2.5-flash-lite
LANGUAGE=es
```

---

# 📌 Comandos útiles

Descargar audio desde YouTube:

```bash
python transcriber_app/modules/audio_downloader.py "URL"
```

Ejecutar pipeline completo:

```bash
python -m transcriber_app.main audio ejemplo tecnico
```

Ver logs en Kubernetes:

```bash
kubectl logs -l app=transcriberapp -f
```

Reiniciar la app:

```bash
kubectl delete pod -l app=transcriberapp
```

# TranscriberApp — Despliegue + Kubernetes (k3s) + Tailscale + HTTPS

Este documento describe **todo el proceso real** seguido para desplegar TranscriberApp en un usando:

- Docker optimizado para Jetson (L4T)
- Kubernetes k3s
- Tailscale para acceso remoto seguro
- HTTPS automático con certificados de Tailscale
- NodePort para exposición del servicio
- Persistencia con PVCs

Incluye además una sección completa de **troubleshooting**, basada en los problemas reales encontrados durante la instalación.

---

# 1. 🧱 Estructura del proyecto

```
TranscriberApp/
├── transcriber_app/
├── utils/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress/ (no usado)
│   └── storage/
├── audios/ (PVC)
├── transcripts/ (PVC)
├── outputs/ (PVC)
└── .dockerignore
```

---

# 2. 🐳 Construcción de la imagen Docker optimizada

## 2.1 Problema inicial
Las primeras imágenes pesaban **16.2 GB**, lo que hacía imposible:

- subirlas a Docker Hub  
- que containerd las extrajera  
- que k3s las ejecutara  

## 2.2 Solución
Se creó un Dockerfile optimizado basado en:

```
FROM nvcr.io/nvidia/l4t-base:r36.3.0
```

Este contenedor es:

- compatible con JetPack 6.x  
- mucho más ligero que `l4t-jetpack`  
- suficiente para Python + FFmpeg  

## 2.3 `.dockerignore` crítico
Para evitar copiar basura dentro de la imagen:

```
venv/
audios/
outputs/
transcripts/
wheels/
__pycache__/
*.pyc
k8s/secret.yaml
```

Esto redujo la imagen final a **~2 GB**.

---

# 3. 🚀 Despliegue en Kubernetes (k3s)

## 3.1 Deployment con HTTPS
El contenedor se arranca con Uvicorn en modo SSL:

```yaml
command:
  - uvicorn
  - transcriber_app.web.web_app:app
  - --host
  - "0.0.0.0"
  - --port
  - "9000"
  - --ssl-keyfile
  - /certs/ubuntu.tailXXXXXX.ts.net.key
  - --ssl-certfile
  - /certs/ubuntu.tailXXXXXX.ts.net.crt
```

Los certificados se montan desde el host:

```yaml
volumeMounts:
  - name: tailscale-certs
    mountPath: /certs
    readOnly: true

volumes:
  - name: tailscale-certs
    hostPath:
      path: /var/lib/tailscale/certs
      type: Directory
```

## 3.2 Service expuesto como NodePort
Para acceso desde Tailscale:

```yaml
type: NodePort
ports:
  - port: 9000
    targetPort: 9000
    nodePort: 30090
```

Acceso final:

```
https://ubuntu.tailXXXXXX.ts.net:30090/
```

---

# 4. 🔐 HTTPS con Tailscale

## 4.1 Generación del certificado
Tailscale solo permite certificados para **dominios válidos del tailnet**.

Comando correcto:

```
sudo tailscale cert ubuntu.tailXXXXXX.ts.net
```

Esto genera:

```
/var/lib/tailscale/certs/ubuntu.tailXXXXXX.ts.net.crt
/var/lib/tailscale/certs/ubuntu.tailXXXXXX.ts.net.key
```

## 4.2 Renovación automática
Tailscale renueva los certificados sin intervención manual.

---

# 6. ✔ Estado final del sistema

- TranscriberApp funcionando en Kubernetes  
- HTTPS real con certificados de Tailscale  
- Acceso remoto seguro desde cualquier dispositivo  
- Imagen Docker ligera y optimizada  
- PVCs funcionando  
- Traefik no necesario para este caso  
- Clúster estable  

---

# 7. 📡 Acceso final a la aplicación

```
https://ubuntu.tailXXXXXX.ts.net:30090/
```

---

# 8. 📦 Comandos útiles

Ver pods:

```
kubectl get pods -A
```

Ver logs:

```
kubectl logs -l app=transcriberapp -f
```

Reiniciar la app:

```
kubectl delete pod -l app=transcriberapp
```

---

# 9. 🧹 Limpieza de imágenes Docker

```
docker system df
docker rmi <imagen>
docker system prune -a
```

---

# 10. 📝 Notas finales

Este README documenta **todo el proceso real**, incluyendo errores, decisiones técnicas y soluciones aplicadas.  
Es una guía completa para reproducir el despliegue en cualquier Jetson con k3s + Tailscale.

```

---

# 🔐 Configuración de Autenticación OAuth2

TranscriberApp soporta autenticación mediante OAuth2. Esta sección documenta la configuración necesaria.

## Variables de Entorno Requeridas

Para que el login funcione correctamente, debes configurar las siguientes variables de entorno:

```bash
# URLs del servidor OAuth2
PUBLIC_OAUTH2_URL=https://oauth2.tudominio.com      # URL pública para el frontend
OAUTH2_URL=http://oauth2-server:8080                # URL interna para el backend

# Credenciales del cliente (deben coincidir con las registradas en el servidor OAuth2)
OAUTH2_CLIENT_ID=transcriberapp
OAUTH2_CLIENT_SECRET=tu_client_secret

# URI de callback
PUBLIC_REDIRECT_URI=https://transcriber.tudominio.com/oauth/callback
```

## Archivos de Configuración

Las variables se encuentran en:
- `.env` (desarrollo local)
- `.env.prod` (producción)

Ejemplo en `.env.prod`:
```bash
PUBLIC_OAUTH2_URL=https://oauth2.nbes.blog
OAUTH2_URL=http://oauth2-server-prod:8080
OAUTH2_CLIENT_ID=transcriberapp
OAUTH2_CLIENT_SECRET=transcriberapp
PUBLIC_REDIRECT_URI=https://transcriber.nbes.blog/oauth/callback
OAUTH2_TOKEN_ENDPOINT=/oauth2/token
OAUTH2_USERINFO_ENDPOINT=/user/me
```

## Flujo de Autenticación

El flujo OAuth2 con PKCE funciona así:

1. **Usuario** hace clic en "Iniciar sesión"
2. **Frontend** llama a `/api/auth/oauth2/start`
3. **Backend** genera:
   - `code_verifier` (secreto)
   - `code_challenge` (hash del verifier)
   - `state` codificado en Base64URL
4. **Backend** guarda la sesión en memoria (`OAUTH_SESSIONS`) y devuelve la URL de autorización
5. **Usuario** es redirigido al servidor OAuth2
6. **Usuario** se autentica en el servidor OAuth2
7. **Servidor OAuth2** redirige a `/oauth/callback?code=...&state=...`
8. **Backend** intercambia el código por tokens y establece cookies de sesión
9. **Usuario** es redirigido a la página principal

## Arquitectura de Sesiones

### Almacenamiento en Memoria

El `code_verifier` se guarda en un diccionario en memoria (`OAUTH_SESSIONS`) vinculado al `state` codificado. Esto es más seguro que las cookies porque:

- El `code_verifier` nunca se expone al navegador
- Evita problemas con cookies bloqueadas o no transmitidas
- Limpieza automática de sesiones expiradas (5 minutos)

**Nota**: En producción con múltiples instancias, considera usar Redis en lugar de memoria local.

### Cookies de Sesión

Tras un login exitoso, se establecen las siguientes cookies:

| Cookie | Descripción | Duración |
|--------|-------------|----------|
| `logged_in` | Indica sesión activa | 24 horas |
| `user_id` | ID del usuario | 24 horas |
| `email` | Email del usuario | 24 horas |
| `username` | Nombre de usuario | 24 horas |

Todas las cookies usan:
- `httponly=True` (no accesibles desde JS)
- `samesite="lax"` (compatibilidad)
- `secure=False` (HTTP) o `True` (HTTPS según configuración)

## Configuración del Servidor OAuth2

El servidor OAuth2 debe:

1. **Registrar el cliente** con:
   - `client_id`: `transcriberapp`
   - `client_secret`: debe coincidir con `OAUTH2_CLIENT_SECRET`
   - `redirect_uri`: debe coincidir con `PUBLIC_REDIRECT_URI`

2. **Soportar PKCE** (`code_challenge_method=S256`)

3. **Endpoints requeridos**:
   - `/oauth2/authorize` - Autorización
   - `/oauth2/token` - Intercambio de tokens
   - `/user/me` - Información del usuario

### Prueba del Servidor OAuth2

Puedes verificar que el servidor OAuth2 funciona correctamente:

```bash
# Intercambiar code por token (desde el servidor)
curl -X POST http://oauth2-server-prod:8080/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "transcriberapp:transcriberapp" \
  -d "grant_type=client_credentials"
```

Debe devolver `200 OK` con un token.

## Troubleshooting

### Problema: "Sesión expirada o inválida"

**Causa**: El `state` en el callback no coincide con lo guardado.

**Solución**:
1. Verifica que `OAUTH2_URL`sea accesible desde el contenedor
2. Revisa los logs buscando `[OAUTH_START] Session stored` y `[OAUTH_CALLBACK] State`
3. Asegúrate de que el `redirect_uri` coincida exactamente

### Problema: Cookies no se establecen

**Causa**: CORS o configuración de cookies.

**Solución**:
1. Verifica que `credentials: 'include'` está en el fetch del frontend
2. Asegúrate de que `expose_headers` incluye `Set-Cookie` en CORS
3. Revisa la configuración de cookies ( secure, samesite, path)

### Problema: "invalid_client"

**Causa**: Credenciales incorrectas o mal formateadas.

**Solución**:
1. Verifica que `OAUTH2_CLIENT_SECRET` coincida con el servidor
2. Usa Basic Auth en el header: `Authorization: Basic base64(client_id:client_secret)`
3. No envíes `client_id` y `client_secret` en el body

### Problema: Redirección infinita a /login

**Causa**: Cookie `logged_in` no se detecta.

**Solución**:
1. Verifica que el fetch usa `credentials: 'include'`
2. Revisa que las cookies tengan `path="/"`
3. En Chrome DevTools → Application → Cookies, verifica que las cookies existen después del login

---

# 📄 Licencia

MIT

---

## ✨ Agradecimientos

OpenAI, Google, NVIDIA, FastAPI, comunidad Jetson.
