import { useRef, useState } from 'react'
import Header from '../components/Header'
import SessionSetup from '../components/SessionSetup'
import FormConfig from '../components/FormConfig'
import AudioRecorder from '../components/AudioRecorder'
import ResultsPanel from '../components/ResultsPanel'
import ChatPanel from '../components/ChatPanel'
import HistoryPanel from '../components/HistoryPanel'
import { AppProvider, useAppContext } from '../context/AppContext'

interface ProcessingResult {
  transcription: string
  summaries: Record<string, string>
  mode: string
  jobId: string
}

function MainAppContent() {
  const { sessionName, setSessionName, setSessionInputValue } = useAppContext()

  const [showChat, setShowChat] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [hasAudio, setHasAudio] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [results, setResults] = useState<ProcessingResult | null>(null)
  const [email, setEmail] = useState('')
  const [modo, setModo] = useState('resumen')
  const handleSetModo = (m: string) => { setModo(m); setStatusText('') }
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [statusText, setStatusText] = useState('')
  const [processedModes, setProcessedModes] = useState<Set<string>>(new Set())
  // transcription text available from history (no audio needed to re-summarize)
  const [historyTranscription, setHistoryTranscription] = useState<string | null>(null)

  const [activeMode, setActiveMode] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const isSessionActive = sessionName.length >= 5
  const modoAlreadyProcessed = processedModes.has(modo)
  const hasContent = hasAudio || historyTranscription !== null
  const canProcess = isSessionActive && hasContent && !isProcessing && !modoAlreadyProcessed

  // ── Polling ──────────────────────────────────────────────────────────────

  const pollJobStatus = (jobId: string) => {
    if (pollingRef.current) clearTimeout(pollingRef.current)

    const check = async () => {
      try {
        const res = await fetch(`/api/status/${jobId}`)
        const data = await res.json()

        if (data.status === 'completed') {
          const resultMode = data.mode || modo
          setResults(prev => {
            const prevSummaries = prev?.summaries || {}
            const newSummaries = { ...prevSummaries, [resultMode]: data.summary || '' }
            return {
              transcription: data.transcription || prev?.transcription || '',
              summaries: newSummaries,
              mode: resultMode,
              jobId,
            }
          })
          setIsProcessing(false)
          setStatusText('')
          setActiveMode(resultMode)
          setProcessedModes(prev => new Set(prev).add(resultMode))
          saveToDb({ transcription: data.transcription || '', summaries: { [resultMode]: data.summary || '' }, mode: resultMode, jobId }, jobId)
        } else if (data.status === 'failed') {
          setIsProcessing(false)
          setStatusText(`❌ Error: ${data.error || 'El procesamiento falló'}`)
        } else {
          pollingRef.current = setTimeout(check, 3000)
        }
      } catch {
        pollingRef.current = setTimeout(check, 5000)
      }
    }

    check()
  }

  const saveToDb = async (result: ProcessingResult, jobId: string) => {
    try {
      const summary = result.summaries[result.mode] || ''
      await fetch('/api/transcriptions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          audio_filename: sessionName,
          mode: result.mode,
          transcription_text: result.transcription,
          summary_output: summary,
          email: email || null,
        }),
      })
    } catch {
      // Non-critical
    }
  }

  // ── Process ──────────────────────────────────────────────────────────────

  const handleProcess = async () => {
    if (!canProcess) return

    setIsProcessing(true)

    // Re-summarize from existing transcription text (loaded from history)
    if (historyTranscription !== null && !hasAudio) {
      setStatusText('Generando resumen…')
      try {
        const res = await fetch('/api/process-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: historyTranscription,
            mode: modo,
            filename: sessionName,
            email: email || null,
          }),
        })
        const data = await res.json()
        const summary = data.markdown || data.summary || ''
        if ((data.success || data.status === true) && summary) {
          const resultMode = data.mode || modo
          setResults(prev => {
            const prevSummaries = prev?.summaries || {}
            return {
              transcription: historyTranscription,
              summaries: { ...prevSummaries, [resultMode]: summary },
              mode: resultMode,
              jobId: data.job_id,
            }
          })
          setIsProcessing(false)
          setStatusText('')
          setActiveMode(resultMode)
          setProcessedModes(prev => new Set(prev).add(resultMode))
          saveToDb({ transcription: historyTranscription, summaries: { [resultMode]: summary }, mode: resultMode, jobId: data.job_id }, data.job_id)
        } else {
          setIsProcessing(false)
          setStatusText(`❌ Error: ${data.error || 'No se pudo generar el resumen. Inténtalo de nuevo.'}`)
        }
      } catch (err: any) {
        setIsProcessing(false)
        setStatusText(`❌ Error de red: ${err.message}`)
      }
      return
    }

    // Normal audio processing
    if (!audioBlob) return
    setStatusText('Enviando audio…')

    try {
      const fd = new FormData()
      fd.append('file', audioBlob, 'audio.webm')
      fd.append('mode', modo)
      if (email) fd.append('email', email)

      const res = await fetch('/api/process-audio', { method: 'POST', body: fd })
      const data = await res.json()

      if (data.success && (data.transcription || data.summary)) {
        const resultMode = data.mode || modo
        const summary = data.summary || ''
        setResults(prev => {
          const prevSummaries = prev?.summaries || {}
          return {
            transcription: data.transcription || prev?.transcription || '',
            summaries: { ...prevSummaries, [resultMode]: summary },
            mode: resultMode,
            jobId: data.job_id,
          }
        })
        setIsProcessing(false)
        setStatusText('')
        setActiveMode(resultMode)
        setProcessedModes(prev => new Set(prev).add(resultMode))
        saveToDb({ transcription: data.transcription || '', summaries: { [resultMode]: summary }, mode: resultMode, jobId: data.job_id }, data.job_id)
      } else {
        setIsProcessing(false)
        setStatusText(`❌ Error: ${data.error || 'No se obtuvo resultado. Inténtalo de nuevo.'}`)
      }
    } catch (err: any) {
      setIsProcessing(false)
      setStatusText(`❌ Error de red: ${err.message}`)
    }
  }

  // ── Callbacks ─────────────────────────────────────────────────────────────

  const handleAudioAvailable = (available: boolean, blob?: Blob) => {
    setHasAudio(available)
    setAudioBlob(blob ?? null)
    if (available) {
      setProcessedModes(new Set())
      setHistoryTranscription(null)
    }
  }

  const handleJobStarted = (jobId: string) => {
    setIsProcessing(true)
    setStatusText('Procesando en el servidor…')
    pollJobStatus(jobId)
  }

  const handleLoadHistory = (item: ProcessingResult & { audioFilename: string }) => {
    setResults(item)
    setActiveMode(null)
    setProcessedModes(new Set(Object.keys(item.summaries || {})))
    setHistoryTranscription(item.transcription)
    setHasAudio(false)
    setAudioBlob(null)
    setStatusText('')
    setSessionInputValue(item.audioFilename)
    setSessionName(item.audioFilename)
    setShowHistory(false)
  }

  return (
    <div className="app-container">
      <Header jobId={results?.jobId} />
      <main className="main-content">
        <SessionSetup />
        <FormConfig
          disabled={!isSessionActive}
          email={email}
          setEmail={setEmail}
          modo={modo}
          setModo={handleSetModo}
        />
        <AudioRecorder
          disabled={!isSessionActive}
          onAudioAvailable={handleAudioAvailable}
          onJobStarted={handleJobStarted}
        />
        <div className="process-section">
          {statusText && <p className="status-message">{statusText}</p>}
          <button
            className="btn btn-primary btn-process"
            onClick={handleProcess}
            disabled={!canProcess}
            title={
              modoAlreadyProcessed
                ? 'Este modo ya fue procesado para este audio'
                : canProcess
                ? 'Enviar y procesar'
                : 'Requiere sesión activa y audio o transcripción cargada'
            }
          >
            {isProcessing ? '⏳ Procesando…' : '🚀 Enviar y Procesar'}
          </button>
        </div>
      </main>

      <ResultsPanel results={results} activeMode={activeMode} />

      <ChatPanel
        isOpen={showChat}
        onClose={() => setShowChat(false)}
        transcription={results?.transcription ?? ''}
        summary={results ? (results.summaries[results.mode] ?? Object.values(results.summaries)[0] ?? '') : ''}
        jobId={results?.jobId ?? ''}
      />

      <HistoryPanel
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        onLoad={handleLoadHistory}
      />

      <button
        className="floating-btn chat-toggle"
        onClick={() => setShowChat(!showChat)}
        disabled={!results}
        title={results ? 'Chat con IA' : 'Requiere una transcripción activa'}
      >
        💬
      </button>
      <button
        className="floating-btn history-toggle"
        onClick={() => setShowHistory(!showHistory)}
        title="Historial"
      >
        📋
      </button>
    </div>
  )
}

export default function MainApp() {
  return (
    <AppProvider>
      <MainAppContent />
    </AppProvider>
  )
}
