import { useEffect, useRef, useState } from 'react'
import { marked } from 'marked'

const MODE_LABELS: Record<string, string> = {
  default: 'Resumen',
  tecnico: 'Técnico',
  ejecutivo: 'Ejecutivo',
  refinamiento: 'Refinamiento',
  bullet: 'Bullet Points',
  comparative: 'Comparativo',
  product_manager: 'Product Manager',
  project_manager: 'Project Manager',
  quality_assurance: 'Quality Assurance',
}

function modeLabel(mode: string) {
  return MODE_LABELS[mode] || mode
}

export interface ResultsData {
  transcription: string
  summaries: Record<string, string>
  mode: string
  jobId: string
}

interface ResultsPanelProps {
  results?: ResultsData | null
  activeMode?: string | null
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button className="result-action-btn" title="Copiar texto" onClick={handleCopy}>
      {copied ? '✅' : '📋'}
    </button>
  )
}

function PrintButton({ content }: { content: string }) {
  const handlePrint = (e: React.MouseEvent) => {
    e.stopPropagation()
    const win = window.open('', '_blank')
    if (!win) return
    win.document.write(`<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      body { font-family: sans-serif; padding: 2rem; max-width: 800px; margin: auto; }
    </style></head><body>${content}</body></html>`)
    win.document.close()
    win.print()
  }

  return (
    <button className="result-action-btn" title="Imprimir" onClick={handlePrint}>
      🖨️
    </button>
  )
}

export default function ResultsPanel({ results, activeMode = null }: ResultsPanelProps) {
  const activeRef = useRef<HTMLDetailsElement | null>(null)

  useEffect(() => {
    if (activeMode && activeRef.current) {
      setTimeout(() => activeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
    }
  }, [activeMode])

  if (!results) return null

  // activeMode=null means history load → all closed
  // activeMode=string means new processing → only that mode open
  const keySuffix = activeMode ?? 'history'
  const summaryEntries = Object.entries(results.summaries)

  return (
    <section className="results-section">
      {results.transcription && (
        <details className="card" open={!activeMode}>
          <summary className="section-title">Transcripción</summary>
          <div className="transcription-text">{results.transcription}</div>
        </details>
      )}

      {summaryEntries.map(([mode, summary]) => {
        const html = summary ? marked.parse(summary) as string : ''
        if (!html) return null
        const isActive = mode === activeMode
        return (
          <details
            key={`${mode}-${keySuffix}`}
            ref={isActive ? activeRef : null}
            className="result-box"
            open={isActive}
          >
            <summary>
              Modo: {modeLabel(mode)}
              <span className="result-actions" onClick={e => e.stopPropagation()}>
                <CopyButton text={summary} />
                <PrintButton content={html} />
              </span>
            </summary>
            <div className="markdown-body" dangerouslySetInnerHTML={{ __html: html }} />
          </details>
        )
      })}

    </section>
  )
}
