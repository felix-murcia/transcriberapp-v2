import { useEffect, useRef, useState } from 'react'
import { marked } from 'marked'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatPanelProps {
  isOpen: boolean
  onClose: () => void
  transcription: string
  summaries: Record<string, string>
  jobId: string
}

export default function ChatPanel({ isOpen, onClose, transcription, summaries, jobId }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const loadedJobRef = useRef<string>('')

  // Load conversation history from DB when jobId changes
  useEffect(() => {
    if (!jobId || jobId === loadedJobRef.current) return
    loadedJobRef.current = jobId
    setMessages([])

    fetch(`/api/conversations/${jobId}`)
      .then(r => r.ok ? r.json() : [])
      .then((history: Message[]) => setMessages(history))
      .catch(() => {})
  }, [jobId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const persistMessage = (role: 'user' | 'assistant', content: string) => {
    if (!jobId) return
    fetch('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, role, content }),
    }).catch(() => {})
  }

  const handleSend = async () => {
    const msg = input.trim()
    if (!msg || isStreaming) return

    if (!transcription && Object.keys(summaries).length === 0) {
      alert('No hay transcripción disponible. Procesa un audio primero.')
      return
    }

    const userMsg: Message = { role: 'user', content: msg }
    const history = [...messages, userMsg]
    setMessages(history)
    setInput('')
    persistMessage('user', msg)

    setIsStreaming(true)
    const aiMsg: Message = { role: 'assistant', content: '' }
    setMessages([...history, aiMsg])

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, transcription, summaries, history }),
      })

      if (!res.body) throw new Error('No stream body')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        fullText += decoder.decode(value, { stream: true })
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = { role: 'assistant', content: fullText }
          return updated
        })
      }

      persistMessage('assistant', fullText)
    } catch (err: any) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { role: 'assistant', content: `Error: ${err.message}` }
        return updated
      })
    } finally {
      setIsStreaming(false)
    }
  }

  const renderContent = (content: string) => {
    const html = marked.parse(content) as string
    return <div className="markdown-body" dangerouslySetInnerHTML={{ __html: html }} />
  }

  return (
    <div className={`chat-panel ${isOpen ? 'open' : ''}`}>
      <div className="chat-header">
        <span>Chat IA</span>
        <button className="btn-close" onClick={onClose}>✕</button>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="chat-empty">
            {transcription
              ? 'Haz preguntas sobre la transcripción o cualquiera de los resúmenes generados.'
              : 'Procesa un audio para comenzar el chat.'}
          </p>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`msg-${msg.role}`}>
            {msg.role === 'assistant' ? renderContent(msg.content) : msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-group">
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Escribe un mensaje…"
          disabled={isStreaming}
        />
        <button className="btn btn-primary" onClick={handleSend} disabled={isStreaming || !input.trim()}>
          {isStreaming ? '…' : 'Enviar'}
        </button>
      </div>
    </div>
  )
}
