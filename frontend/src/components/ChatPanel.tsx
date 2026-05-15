import { useState } from 'react'

interface ChatPanelProps {
  isOpen: boolean
  onClose: () => void
}

export default function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
  const [messages, setMessages] = useState<{ text: string; sender: string }[]>([])
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return
    setMessages([...messages, { text: input, sender: 'user' }])
    setInput('')
    // Simulate AI response
    setTimeout(() => {
      setMessages(prev => [...prev, { text: 'Respuesta de IA simulada', sender: 'ai' }])
    }, 500)
  }

  return (
    <div className={`chat-panel ${isOpen ? 'open' : ''}`}>
      <div className="chat-header">
        <span>Chat IA</span>
        <button className="btn-close" onClick={onClose}>✕</button>
      </div>
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`msg-${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <div className="chat-input-group">
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Escribe un mensaje..."
        />
        <button className="btn btn-primary" onClick={handleSend}>Enviar</button>
      </div>
    </div>
  )
}
