import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import Login from './pages/Login'
import MainApp from './pages/MainApp'

function AuthGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const [checked, setChecked] = useState(false)
  const [authenticated, setAuthenticated] = useState(false)

  useEffect(() => {
    fetch('/api/auth/check')
      .then(r => r.json())
      .then(data => {
        if (data.logged_in) {
          setAuthenticated(true)
        } else {
          navigate('/login', { replace: true })
        }
      })
      .catch(() => navigate('/login', { replace: true }))
      .finally(() => setChecked(true))
  }, [navigate])

  if (!checked) return null
  if (!authenticated) return null
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <AuthGuard>
            <MainApp />
          </AuthGuard>
        }
      />
    </Routes>
  )
}
