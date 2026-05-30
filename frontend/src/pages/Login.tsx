import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

export default function Login() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const oauthError = searchParams.get('error')
    if (oauthError) setError(`Error de autenticación: ${oauthError}`)
  }, [searchParams])

  const handleLogin = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/auth/oauth2/start', { method: 'POST' })
      const data = await res.json()
      if (data.success && data.authorization_url) {
        window.location.href = data.authorization_url
      } else {
        setError(data.error || 'No se pudo iniciar la autenticación')
        setLoading(false)
      }
    } catch {
      setError('Error de red al conectar con el servidor')
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-box">
        <h2>Transcriber<span>App</span></h2>
        <p className="subtitle">Transcripción inteligente de audio</p>
        {error && <p className="error-msg">{error}</p>}
        <button type="button" className="oauth-btn" onClick={handleLogin} disabled={loading}>
          {loading ? 'Redirigiendo…' : 'Iniciar sesión'}
        </button>
      </div>
    </div>
  )
}
