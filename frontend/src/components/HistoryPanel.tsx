import { useEffect, useState } from 'react'

interface HistoryItem {
  job_id: string
  audio_filename: string
  mode: string
  status: string
  created_at: string | null
}

interface LoadedResult {
  transcription: string
  summary: string
  mode: string
  jobId: string
}

interface HistoryPanelProps {
  isOpen: boolean
  onClose: () => void
  onLoad: (result: LoadedResult) => void
}

export default function HistoryPanel({ isOpen, onClose, onLoad }: HistoryPanelProps) {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isOpen) return
    setLoading(true)
    fetch('/api/transcriptions')
      .then(r => r.ok ? r.json() : [])
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [isOpen])

  const handleSelect = async (jobId: string) => {
    try {
      const res = await fetch(`/api/transcriptions/${jobId}`)
      if (!res.ok) return
      const data = await res.json()
      onLoad({
        transcription: data.transcription_text || '',
        summary: data.summary_output || '',
        mode: data.mode,
        jobId: data.job_id,
      })
    } catch {
      alert('No se pudo cargar la transcripción.')
    }
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return ''
    return new Date(iso).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' })
  }

  return (
    <div className={`history-panel ${isOpen ? 'open' : ''}`}>
      <div className="history-header">
        <h2 className="history-title">Historial</h2>
        <button className="btn-close" onClick={onClose}>✕</button>
      </div>
      {loading && <p className="history-loading">Cargando…</p>}
      {!loading && items.length === 0 && (
        <p className="history-empty">No hay transcripciones guardadas.</p>
      )}
      <ul className="history-list">
        {items.map(item => (
          <li key={item.job_id} onClick={() => handleSelect(item.job_id)} className="history-item">
            <span className="history-name">{item.audio_filename}</span>
            <small className="history-meta">{item.mode} · {formatDate(item.created_at)}</small>
          </li>
        ))}
      </ul>
    </div>
  )
}
