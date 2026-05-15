import { useAppContext } from '../context/AppContext'

export default function Header() {
  const { sessionName } = useAppContext()
  const isActive = sessionName.length >= 5

  return (
    <header className="app-header">
      <h1 className="app-title">
        <span className="app-name">TranscriberApp</span>
        <span
          className={`session-status ${isActive ? 'session-active' : ''}`}
          title={isActive ? `Sesión activa: ${sessionName}` : 'No hay sesión activa'}
        >
          {isActive ? sessionName : 'Sin sesión'}
        </span>
      </h1>
    </header>
  )
}
