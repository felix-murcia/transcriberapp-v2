import { useRef, useState, useCallback } from 'react'

const CHUNK_SIZE = 1024 * 1024 * 2 // 2MB por chunk

interface AudioRecorderProps {
  isRecording: boolean
  setIsRecording: (val: boolean) => void
  disabled?: boolean
  onAudioAvailable?: (available: boolean, blob?: Blob) => void
}

export default function AudioRecorder({ isRecording, setIsRecording, disabled = false, onAudioAvailable }: AudioRecorderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string>('')
  const [statusText, setStatusText] = useState('')
  const [uploadProgress, setUploadProgress] = useState<number>(-1)
  const [uploadId, setUploadId] = useState<string>('')
  const [isUploading, setIsUploading] = useState(false)

  const uploadChunks = async (file: File, modo: string, email: string, nombre: string) => {
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE)
    const extension = file.name.split('.').pop() || 'webm'
    const sessionId = crypto.randomUUID()

    setUploadId(sessionId)
    setIsUploading(true)
    setUploadProgress(0)

    try {
      // Upload chunks sequentially
      for (let i = 0; i < totalChunks; i++) {
        if (!sessionId) break

        const start = i * CHUNK_SIZE
        const end = Math.min(start + CHUNK_SIZE, file.size)
        const chunk = file.slice(start, end)

        const formData = new FormData()
        formData.append('chunk', new File([chunk], `chunk_${i}`, { type: file.type }))
        formData.append('chunkIndex', String(i))
        formData.append('totalChunks', String(totalChunks))
        formData.append('uploadId', sessionId)
        formData.append('nombre', nombre)
        formData.append('modo', modo)
        if (email) formData.append('email', email)
        formData.append('extension', extension)

        const response = await fetch('/api/upload-chunk', {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          throw new Error(`Error subiendo chunk ${i + 1}/${totalChunks}`)
        }

        setUploadProgress(Math.round(((i + 1) / totalChunks) * 100))
      }

      // Complete upload
      const completeForm = new FormData()
      completeForm.append('uploadId', sessionId)

      const completeResponse = await fetch('/api/upload-complete', {
        method: 'POST',
        body: completeForm,
      })

      const completeData = await completeResponse.json()

      if (completeData.success) {
        setStatusText(`✅ Audio procesado: ${nombre}`)
        setAudioBlob(file)
        const url = URL.createObjectURL(file)
        setAudioUrl(url)
        onAudioAvailable?.(true, file)
      } else {
        setStatusText(`❌ Error: ${completeData.error || 'Error en el procesamiento'}`)
      }
    } catch (error: any) {
      setStatusText(`❌ Error de subida: ${error.message}`)
      // Cancel upload on error
      if (sessionId) {
        try {
          await fetch('/api/upload-cancel', {
            method: 'POST',
            body: new URLSearchParams({ uploadId: sessionId }),
          })
        } catch {
          // Ignore cancel errors
        }
      }
    } finally {
      setIsUploading(false)
      setUploadProgress(-1)
      setUploadId('')
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // For small files, use simple upload
    if (file.size <= CHUNK_SIZE) {
      const blob = new Blob([file])
      setAudioBlob(blob)
      const url = URL.createObjectURL(blob)
      setAudioUrl(url)
      setStatusText(`Grabación cargada: ${file.name}`)
      onAudioAvailable?.(true, blob)
    } else {
      // For large files, use chunked upload
      const nombre = file.name.replace(/\.[^/.]+$/, '')
      const modo = 'default'
      const email = ''
      await uploadChunks(file, modo, email, nombre)
    }
  }

  const handleRecord = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      setStatusText('Grabando...')
      // Simplified recording - in production use MediaRecorder API
      alert('Grabación iniciada')
      onAudioAvailable?.(true)
    } catch {
      alert('No se pudo acceder al micrófono')
    }
  }

  const handleDelete = () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setAudioBlob(null)
    setAudioUrl('')
    setStatusText('Grabación borrada.')
    onAudioAvailable?.(false)
  }

  const handleCancelUpload = async () => {
    if (uploadId) {
      try {
        await fetch('/api/upload-cancel', {
          method: 'POST',
          body: new URLSearchParams({ uploadId }),
        })
      } catch {
        // Ignore errors
      }
      setUploadId('')
      setUploadProgress(-1)
      setIsUploading(false)
      setStatusText('Subida cancelada.')
    }
  }

  return (
    <section className={`card recorder-section ${disabled ? 'disabled' : ''}`} aria-labelledby="recorderTitle">
      <h2 id="recorderTitle" className="section-title">Grabación de audio</h2>

      <div className="button-group">
        <button
          type="button"
          className="btn btn-record"
          onClick={handleRecord}
          disabled={disabled || isRecording || isUploading}
        >
          🎤 Grabar
        </button>
        <button
          type="button"
          className="btn btn-stop"
          disabled={disabled || !isRecording}
        >
          ⏹ Detener
        </button>
        <button
          type="button"
          className="btn btn-upload"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isUploading}
        >
          📁 Cargar archivo
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          onChange={handleFileUpload}
          disabled={disabled || isUploading}
          style={{ display: 'none' }}
        />
        {isUploading && (
          <button type="button" className="btn btn-cancel" onClick={handleCancelUpload}>
            ✕ Cancelar
          </button>
        )}
        {audioBlob && !isUploading && (
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

      {/* Progress bar for chunk uploads */}
      {uploadProgress >= 0 && (
        <div className="upload-progress">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <span className="progress-text">{uploadProgress}%</span>
        </div>
      )}

      {audioUrl && !isUploading && (
        <audio controls src={audioUrl} className="audio-preview" />
      )}

      {statusText && (
        <p className="status-message">{statusText}</p>
      )}
    </section>
  )
}
