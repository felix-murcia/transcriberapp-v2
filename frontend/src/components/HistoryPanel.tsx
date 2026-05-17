import { useEffect, useState } from 'react'

interface HistoryItem {
  job_id: string
  audio_filename: string
  mode: string
  status: string
  summaries: Record<string, string>
  created_at: string | null
}

interface LoadedResult {
  transcription: string
  summaries: Record<string, string>
  mode: string
  jobId: string
  audioFilename: string
}

interface HistoryPanelProps {
  isOpen: boolean
  onClose: () => void
  onLoad: (result: LoadedResult) => void
}

export default function HistoryPanel({ isOpen, onClose, onLoad }: HistoryPanelProps) {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')

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
      const summaries: Record<string, string> = data.summaries || {}
      // fallback: if summaries empty but summary_output exists, use mode key
      if (Object.keys(summaries).length === 0 && data.summary_output) {
        summaries[data.mode || 'resumen'] = data.summary_output
      }
      onLoad({
        transcription: data.transcription_text || '',
        summaries,
        mode: data.mode,
        jobId: data.job_id,
        audioFilename: data.audio_filename || '',
      })
    } catch {
      alert('No se pudo cargar la transcripción.')
    }
  }

  const startEdit = (item: HistoryItem, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(item.job_id)
    setEditName(item.audio_filename)
  }

  const commitRename = async (jobId: string) => {
    const name = editName.trim()
    if (!name) { setEditingId(null); return }
    try {
      const res = await fetch(`/api/transcriptions/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio_filename: name }),
      })
      if (res.ok) {
        setItems(prev => prev.map(i => i.job_id === jobId ? { ...i, audio_filename: name } : i))
      }
    } catch { /* silent */ }
    setEditingId(null)
  }

  const handleDelete = async (jobId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('¿Eliminar esta transcripción?')) return
    try {
      const res = await fetch(`/api/transcriptions/${jobId}`, { method: 'DELETE' })
      if (res.ok) setItems(prev => prev.filter(i => i.job_id !== jobId))
    } catch { /* silent */ }
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
          <li key={item.job_id} className="history-item" onClick={() => handleSelect(item.job_id)}>
            <div className="history-item-body">
              {editingId === item.job_id ? (
                <input
                  className="history-rename-input"
                  value={editName}
                  autoFocus
                  onClick={e => e.stopPropagation()}
                  onChange={e => setEditName(e.target.value)}
                  onBlur={() => commitRename(item.job_id)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') commitRename(item.job_id)
                    if (e.key === 'Escape') setEditingId(null)
                  }}
                />
              ) : (
                <span className="history-name">{item.audio_filename}</span>
              )}
              <small className="history-meta">{Object.keys(item.summaries || {}).join(', ') || item.mode} · {formatDate(item.created_at)}</small>
            </div>
            <div className="history-item-actions">
              <button
                className="history-action-btn"
                title="Renombrar"
                onClick={e => startEdit(item, e)}
              >✏️</button>
              <button
                className="history-action-btn history-action-delete"
                title="Eliminar"
                onClick={e => handleDelete(item.job_id, e)}
              >🗑️</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
