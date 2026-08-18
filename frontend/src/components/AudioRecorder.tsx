import { useRef, useState } from 'react'

const CHUNK_SIZE = 1024 * 1024 * 2 // 2MB

interface AudioRecorderProps {
  disabled?: boolean
  onAudioAvailable?: (available: boolean, blob?: Blob) => void
  onJobStarted?: (jobId: string) => void
}

export default function AudioRecorder({ disabled = false, onAudioAvailable, onJobStarted }: AudioRecorderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<BlobPart[]>([])

  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string>('')
  const [statusText, setStatusText] = useState('')
  const [uploadProgress, setUploadProgress] = useState<number>(-1)
  const [isRecording, setIsRecording] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const uploadIdRef = useRef<string>('')

  // ── Recording ────────────────────────────────────────────────────────────

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus']
      const mimeType = mimeTypes.find(t => MediaRecorder.isTypeSupported(t)) || 'audio/webm'

      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder
      audioChunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(audioChunksRef.current, { type: mimeType })
        const url = URL.createObjectURL(blob)
        setAudioBlob(blob)
        setAudioUrl(url)
        setStatusText('Grabación lista.')
        setIsRecording(false)
        onAudioAvailable?.(true, blob)
      }

      recorder.start(1000)
      setIsRecording(true)
      setStatusText('Grabando…')
    } catch {
      alert('No se pudo acceder al micrófono. Verifica los permisos.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }

  // ── File upload (chunked) ────────────────────────────────────────────────

  const uploadChunks = async (file: Blob, filename: string) => {
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE)
    const ext = (file instanceof File ? file.name.split('.').pop() : null) || 'webm'
    const sessionId = typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`
    uploadIdRef.current = sessionId

    setIsUploading(true)
    setUploadProgress(0)
    setStatusText(`Subiendo (0/${totalChunks} partes)…`)

    try {
      const MAX_CONCURRENCY = 3
      const MAX_RETRIES = 3
      let completedChunks = 0

      // Helper function to upload a single chunk with retries
      const uploadSingleChunk = async (i: number, retries = 0): Promise<void> => {
        const start = i * CHUNK_SIZE
        const chunkBlob = file.slice(start, Math.min(start + CHUNK_SIZE, file.size))

        const fd = new FormData()
        fd.append('chunk', new File([chunkBlob], `chunk_${i}`, { type: file.type }))
        fd.append('chunkIndex', String(i))
        fd.append('totalChunks', String(totalChunks))
        fd.append('uploadId', sessionId)
        fd.append('nombre', filename)
        fd.append('modo', 'resumen')
        fd.append('extension', ext)

        try {
          const res = await fetch('/api/upload-chunk', { method: 'POST', body: fd })
          if (!res.ok) throw new Error(`Status ${res.status}`)

          // Increment completed and update UI
          completedChunks++
          const progress = Math.round((completedChunks / totalChunks) * 100)
          setUploadProgress(progress)
          setStatusText(`Subiendo (${completedChunks}/${totalChunks} partes)…`)
        } catch (err: any) {
          if (retries < MAX_RETRIES) {
            console.warn(`Retry ${retries + 1} for chunk ${i} due to: ${err.message}`)
            // Exponential backoff buffer
            await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retries)))
            return uploadSingleChunk(i, retries + 1)
          }
          throw new Error(`Error en chunk ${i + 1} tras ${MAX_RETRIES} intentos`)
        }
      }

      // Concurrency Queue
      let currentChunkIndex = 0
      const workers = Array(MAX_CONCURRENCY).fill(null).map(async () => {
        while (currentChunkIndex < totalChunks) {
          const idx = currentChunkIndex++
          await uploadSingleChunk(idx)
        }
      })

      // Wait for all chunks to finish uploading
      await Promise.all(workers)

      setStatusText('Finalizando subida…')
      const completeForm = new FormData()
      completeForm.append('uploadId', sessionId)

      const completeRes = await fetch('/api/upload-complete', { method: 'POST', body: completeForm })
      const completeData = await completeRes.json()

      if (completeData.job_id) {
        setStatusText('Procesando en el servidor…')
        onJobStarted?.(completeData.job_id)
      } else {
        throw new Error(completeData.error || 'Error al completar la subida')
      }
    } catch (error: any) {
      setStatusText(`❌ Error: ${error.message}`)
      if (uploadIdRef.current) {
        const cfd = new FormData()
        cfd.append('uploadId', uploadIdRef.current)
        fetch('/api/upload-cancel', { method: 'POST', body: cfd }).catch(() => { })
      }
    } finally {
      setIsUploading(false)
      setUploadProgress(-1)
      uploadIdRef.current = ''
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''

    // Show local preview immediately
    const url = URL.createObjectURL(file)
    setAudioBlob(file)
    setAudioUrl(url)
    onAudioAvailable?.(true, file)

    if (file.size > CHUNK_SIZE) {
      // Large files go through chunked upload → job polling
      const nombre = file.name.replace(/\.[^/.]+$/, '')
      await uploadChunks(file, nombre)
    } else {
      setStatusText(`Archivo cargado: ${file.name}`)
    }
  }

  const handleDelete = () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setAudioBlob(null)
    setAudioUrl('')
    setStatusText('Grabación eliminada.')
    onAudioAvailable?.(false)
  }

  const handleCancelUpload = async () => {
    if (uploadIdRef.current) {
      const fd = new FormData()
      fd.append('uploadId', uploadIdRef.current)
      await fetch('/api/upload-cancel', { method: 'POST', body: fd }).catch(() => { })
      uploadIdRef.current = ''
    }
    setIsUploading(false)
    setUploadProgress(-1)
    setStatusText('Subida cancelada.')
  }

  return (
    <section className={`card recorder-section ${disabled ? 'disabled' : ''}`} aria-labelledby="recorderTitle">
      <h2 id="recorderTitle" className="section-title">Grabación de audio</h2>

      <div className="button-group">
        <button
          type="button"
          className="btn btn-record"
          onClick={startRecording}
          disabled={disabled || isRecording || isUploading}
        >
          🎤 Grabar
        </button>
        <button
          type="button"
          className="btn btn-stop"
          onClick={stopRecording}
          disabled={disabled || !isRecording}
        >
          ⏹ Detener
        </button>
        <button
          type="button"
          className="btn btn-upload"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isRecording || isUploading}
        >
          📁 Cargar archivo
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
        />
        {isUploading && (
          <button type="button" className="btn btn-cancel" onClick={handleCancelUpload}>
            ✕ Cancelar
          </button>
        )}
        {audioBlob && !isRecording && !isUploading && (
          <>
            <button type="button" className="btn btn-download" onClick={() => {
              const a = document.createElement('a')
              a.href = audioUrl
              a.download = 'grabacion.webm'
              a.click()
            }} disabled={disabled}>
              ⬇ Descargar
            </button>
            <button type="button" className="btn btn-delete" onClick={handleDelete} disabled={disabled}>
              🗑 Eliminar
            </button>
          </>
        )}
      </div>

      {uploadProgress >= 0 && (
        <div className="upload-progress">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
          </div>
          <span className="progress-text">{uploadProgress}%</span>
        </div>
      )}

      {audioUrl && !isRecording && (
        <audio controls src={audioUrl} className="audio-preview" />
      )}

      {statusText && <p className="status-message">{statusText}</p>}
    </section>
  )
}
