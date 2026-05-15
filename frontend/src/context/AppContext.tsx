import React, { createContext, useContext, useState } from 'react'

interface ProcessingResult {
  transcription: string
  summary: string
  mode: string
  jobId: string
}

interface AppState {
  sessionName: string
  setSessionName: (name: string) => void
  audioBlob: Blob | null
  setAudioBlob: (blob: Blob | null) => void
  audioUrl: string
  setAudioUrl: (url: string) => void
  processingResult: ProcessingResult | null
  setProcessingResult: (result: ProcessingResult | null) => void
  isProcessing: boolean
  setIsProcessing: (loading: boolean) => void
}

const AppContext = createContext<AppState>({
  sessionName: '',
  setSessionName: () => {},
  audioBlob: null,
  setAudioBlob: () => {},
  audioUrl: '',
  setAudioUrl: () => {},
  processingResult: null,
  setProcessingResult: () => {},
  isProcessing: false,
  setIsProcessing: () => {},
})

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [sessionName, setSessionName] = useState('')
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState('')
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  return (
    <AppContext.Provider value={{ 
      sessionName, 
      setSessionName, 
      audioBlob, 
      setAudioBlob,
      audioUrl,
      setAudioUrl,
      processingResult,
      setProcessingResult,
      isProcessing,
      setIsProcessing,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export function useAppContext() {
  return useContext(AppContext)
}
