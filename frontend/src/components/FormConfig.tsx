import { useState } from 'react'

const MODO_OPTIONS = [
  { value: 'resumen', label: 'Resumen' },
  { value: 'tecnico', label: 'Técnico' },
  { value: 'refinamiento', label: 'Refinamiento' },
  { value: 'ejecutivo', label: 'Ejecutivo' },
  { value: 'bullet', label: 'Bullet' },
  { value: 'comparative', label: 'Comparativo' },
  { value: 'product_manager', label: 'Product Manager' },
  { value: 'project_manager', label: 'Project Manager' },
  { value: 'quality_assurance', label: 'Quality Assurance' },
]

interface FormConfigProps {
  disabled?: boolean
  email?: string
  setEmail?: (email: string) => void
  modo?: string
  setModo?: (modo: string) => void
}

export default function FormConfig({
  disabled = false,
  email = '',
  setEmail,
  modo = 'resumen',
  setModo,
}: FormConfigProps) {
  const localEmail = email || ''
  const localModo = modo || 'resumen'

  return (
    <section className={`card ${disabled ? 'disabled' : ''}`} aria-labelledby="formTitle">
      <h2 id="formTitle" className="visually-hidden">Configuración</h2>
      <div className="form-row-horizontal">
        <div className="form-group">
          <label htmlFor="email">Correo electrónico:</label>
          <input
            type="email"
            id="email"
            className="form-control"
            placeholder="ej: usuario@correo.com"
            value={localEmail}
            onChange={(e) => setEmail?.(e.target.value)}
            disabled={disabled}
            aria-required="true"
          />
        </div>
        <div className="form-group">
          <label htmlFor="modo">Modo de procesamiento:</label>
          <select
            id="modo"
            className="form-control"
            value={localModo}
            onChange={(e) => setModo?.(e.target.value)}
            disabled={disabled}
            aria-label="Selecciona el modo de procesamiento"
          >
            {MODO_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>
    </section>
  )
}
