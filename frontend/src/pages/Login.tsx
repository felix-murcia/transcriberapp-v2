import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const navigate = useNavigate()
  const [error, setError] = useState('')

  const handleLogin = () => {
    localStorage.setItem('token', 'mock-token')
    navigate('/')
  }

  return (
    <div className="login-page">
      <div className="login-box">
        <h2>Transcriber<span>App</span></h2>
        <p className="subtitle">Transcripción inteligente de audio</p>
        {error && <p className="error-msg">{error}</p>}
        <button type="button" className="oauth-btn" onClick={handleLogin}>
          Iniciar sesión
        </button>
      </div>
    </div>
  )
}
