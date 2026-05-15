import { useState } from 'react'
import Header from '../components/Header'
import SessionSetup from '../components/SessionSetup'
import FormConfig from '../components/FormConfig'
import AudioRecorder from '../components/AudioRecorder'
import ResultsPanel from '../components/ResultsPanel'
import ChatPanel from '../components/ChatPanel'
import HistoryPanel from '../components/HistoryPanel'
import { AppProvider, useAppContext } from '../context/AppContext'

function MainAppContent() {
  const { sessionName } = useAppContext()
  const [isRecording, setIsRecording] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [hasAudio, setHasAudio] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [results, setResults] = useState<{
    transcription: string
    summary: string
    mode: string
    jobId: string
  } | null>(null)
  const [email, setEmail] = useState('')
  const [modo, setModo] = useState('default')
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)

  const isSessionActive = sessionName.length >= 5
  const canProcess = isSessionActive && hasAudio

  const handleProcess = async () => {
    if (!canProcess || !audioBlob) return

    setIsProcessing(true)
    try {
      const formData = new FormData()
      formData.append('file', audioBlob, 'audio.webm')
      formData.append('mode', modo)
      if (email) formData.append('email', email)

      const response = await fetch('/api/process-audio', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        setResults({
          transcription: data.transcription || '',
          summary: data.summary || '',
          mode: data.mode || modo,
          jobId: data.job_id,
        })
      } else {
        alert(`Error: ${data.error || 'Processing failed'}`)
      }
    } catch (error) {
      alert(`Error al procesar: ${error}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleAudioAvailable = (available: boolean, blob?: Blob) => {
    setHasAudio(available)
    if (blob) setAudioBlob(blob)
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
          isRecording={isRecording}
          setIsRecording={setIsRecording}
          disabled={!isSessionActive}
          onAudioAvailable={handleAudioAvailable}
        />
        <div className="process-section">
          <button
            className="btn btn-primary btn-process"
            onClick={handleProcess}
            disabled={!canProcess || isProcessing}
            title={canProcess ? "Enviar y procesar audio" : "Requiere sesión activa y audio"}
          >
            {isProcessing ? '⏳ Procesando...' : '🚀 Enviar y Procesar'}
          </button>
        </div>
      </main>
      <ResultsPanel results={results} />
      <ChatPanel isOpen={showChat} onClose={() => setShowChat(false)} />
      <HistoryPanel isOpen={showHistory} onClose={() => setShowHistory(false)} />
      <button
        className="floating-btn chat-toggle"
        onClick={() => setShowChat(!showChat)}
        disabled={!isSessionActive}
        title={isSessionActive ? "Chat con IA" : "Requiere sesión activa"}
      >
        💬
      </button>
      <button
        className="floating-btn history-toggle"
        onClick={() => setShowHistory(!showHistory)}
        disabled={!isSessionActive}
        title={isSessionActive ? "Historial" : "Requiere sesión activa"}
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
