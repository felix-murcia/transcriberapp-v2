import { useState } from 'react'
import { marked } from 'marked'

interface ResultsPanelProps {
  results?: {
    transcription: string
    summary: string
    mode: string
    jobId: string
  } | null
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

export default function ResultsPanel({ results }: ResultsPanelProps) {
  if (!results) return null

  const summaryHtml = results.summary ? marked.parse(results.summary) as string : ''

  return (
    <section className="results-section">
      {results.transcription && (
        <details className="card" open>
          <summary className="section-title">Transcripción</summary>
          <div className="transcription-text">{results.transcription}</div>
        </details>
      )}

      {summaryHtml && (
        <details className="result-box" open>
          <summary>
            Modo: {results.mode}
            <span className="result-actions" onClick={e => e.stopPropagation()}>
              <CopyButton text={results.summary} />
              <PrintButton content={summaryHtml} />
            </span>
          </summary>
          <div className="markdown-body" dangerouslySetInnerHTML={{ __html: summaryHtml }} />
        </details>
      )}

      <div className="result-meta">
        <p>ID del Trabajo: <code>{results.jobId}</code></p>
      </div>
    </section>
  )
}
