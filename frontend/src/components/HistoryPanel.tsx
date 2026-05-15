import { useState } from 'react'

interface HistoryPanelProps {
  isOpen: boolean
  onClose: () => void
}

interface HistoryItem {
  id: string
  nombre: string
  fecha: string
}

export default function HistoryPanel({ isOpen, onClose }: HistoryPanelProps) {
  const [items, setItems] = useState<HistoryItem[]>([
    { id: '1', nombre: 'reunion_enero', fecha: '2026-01-15' },
    { id: '2', nombre: 'cliente_demo', fecha: '2026-01-14' },
  ])

  return (
    <div className={`history-panel ${isOpen ? 'open' : ''}`}>
      <div className="history-header">
        <h2 className="history-title">Historial</h2>
        <button className="btn-close" onClick={onClose}>✕</button>
      </div>
      <ul className="history-list">
        {items.map(item => (
          <li key={item.id} onClick={() => alert(`Cargando: ${item.nombre}`)}>
            {item.nombre}
            <small>{item.fecha}</small>
          </li>
        ))}
      </ul>
    </div>
  )
}
