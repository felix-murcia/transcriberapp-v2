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
  summary: string
  mode: string
  jobId: string
}

function MainAppContent() {
  const { sessionName } = useAppContext()

  const [showChat, setShowChat] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [hasAudio, setHasAudio] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [results, setResults] = useState<ProcessingResult | null>(null)
  const [email, setEmail] = useState('')
  const [modo, setModo] = useState('default')
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [statusText, setStatusText] = useState('')

  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const isSessionActive = sessionName.length >= 5
  const canProcess = isSessionActive && hasAudio && !isProcessing

  // ── Polling ──────────────────────────────────────────────────────────────

  const pollJobStatus = (jobId: string) => {
    if (pollingRef.current) clearTimeout(pollingRef.current)

    const check = async () => {
      try {
        const res = await fetch(`/api/status/${jobId}`)
        const data = await res.json()

        if (data.status === 'completed') {
          const result: ProcessingResult = {
            transcription: data.transcription || '',
            summary: data.summary || '',
            mode: data.mode || modo,
            jobId,
          }
          setResults(result)
          setIsProcessing(false)
          setStatusText('')
          saveToDb(result, jobId)
        } else if (data.status === 'failed') {
          setIsProcessing(false)
          setStatusText(`❌ Error: ${data.error || 'El procesamiento falló'}`)
        } else {
          // still processing
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
      await fetch('/api/transcriptions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          audio_filename: sessionName,
          mode: result.mode,
          transcription_text: result.transcription,
          summary_output: result.summary,
          email: email || null,
        }),
      })
    } catch {
      // Non-critical — don't surface to user
    }
  }

  // ── Process (small files / recordings) ──────────────────────────────────

  const handleProcess = async () => {
    if (!canProcess || !audioBlob) return

    setIsProcessing(true)
    setStatusText('Enviando audio…')

    try {
      const fd = new FormData()
      fd.append('file', audioBlob, 'audio.webm')
      fd.append('mode', modo)
      if (email) fd.append('email', email)

      const res = await fetch('/api/process-audio', { method: 'POST', body: fd })
      const data = await res.json()

      if (data.success) {
        const result: ProcessingResult = {
          transcription: data.transcription || '',
          summary: data.summary || '',
          mode: data.mode || modo,
          jobId: data.job_id,
        }
        setResults(result)
        setIsProcessing(false)
        setStatusText('')
        saveToDb(result, data.job_id)
      } else {
        setIsProcessing(false)
        setStatusText(`❌ Error: ${data.error || 'Procesamiento fallido'}`)
      }
    } catch (err: any) {
      setIsProcessing(false)
      setStatusText(`❌ Error de red: ${err.message}`)
    }
  }

  // ── Callbacks from AudioRecorder ─────────────────────────────────────────

  const handleAudioAvailable = (available: boolean, blob?: Blob) => {
    setHasAudio(available)
    setAudioBlob(blob ?? null)
  }

  // Called when a large file finishes chunked upload and the server starts processing
  const handleJobStarted = (jobId: string) => {
    setIsProcessing(true)
    setStatusText('Procesando en el servidor…')
    pollJobStatus(jobId)
  }

  // Called from HistoryPanel when user loads a past transcription
  const handleLoadHistory = (item: ProcessingResult) => {
    setResults(item)
    setShowHistory(false)
  }

  return (
    <div className="app-container">
      <Header />
      <main className="main-content">
        <SessionSetup />
        <FormConfig
          disabled={!isSessionActive}
          email={email}
          setEmail={setEmail}
          modo={modo}
          setModo={setModo}
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
            title={canProcess ? 'Enviar y procesar audio' : 'Requiere sesión activa y audio'}
          >
            {isProcessing ? '⏳ Procesando…' : '🚀 Enviar y Procesar'}
          </button>
        </div>
      </main>

      <ResultsPanel results={results} />

      <ChatPanel
        isOpen={showChat}
        onClose={() => setShowChat(false)}
        transcription={results?.transcription ?? ''}
        summary={results?.summary ?? ''}
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
        disabled={!isSessionActive}
        title={isSessionActive ? 'Chat con IA' : 'Requiere sesión activa'}
      >
        💬
      </button>
      <button
        className="floating-btn history-toggle"
        onClick={() => setShowHistory(!showHistory)}
        disabled={!isSessionActive}
        title={isSessionActive ? 'Historial' : 'Requiere sesión activa'}
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
