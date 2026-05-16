import { marked } from 'marked'

interface ResultsPanelProps {
  results?: {
    transcription: string
    summary: string
    mode: string
    jobId: string
  } | null
}

export default function ResultsPanel({ results }: ResultsPanelProps) {
  if (!results) return null

  const summaryHtml = results.summary ? marked.parse(results.summary) as string : ''

  return (
    <section className="results-section">
      {results.transcription && (
        <div className="card">
          <h2 className="section-title">Transcripción</h2>
          <div className="transcription-text">{results.transcription}</div>
        </div>
      )}

      {summaryHtml && (
        <details className="result-box" open>
          <summary>Modo: {results.mode}</summary>
          <div className="markdown-body" dangerouslySetInnerHTML={{ __html: summaryHtml }} />
        </details>
      )}

      <div className="result-meta">
        <p>ID del Trabajo: <code>{results.jobId}</code></p>
      </div>
    </section>
  )
}
