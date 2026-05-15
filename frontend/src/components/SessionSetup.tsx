import { useState } from 'react'
import { useAppContext } from '../context/AppContext'

export default function SessionSetup() {
  const { sessionName, setSessionName } = useAppContext()
  const [isValid, setIsValid] = useState(false)

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    const trimmed = value.trim()
    const valid = trimmed.length >= 5

    setSessionName(valid ? trimmed : '')
    setIsValid(valid)
  }

  return (
    <section className="card" aria-labelledby="sessionSetupTitle">
      <h2 id="sessionSetupTitle" className="section-title">Sesión actual</h2>
      <div className="form-group">
        <label htmlFor="nombre">Nombre de la sesión</label>
        <input
          type="text"
          id="nombre"
          className="form-control"
          placeholder="ej: reunion_enero"
          value={sessionName}
          onChange={handleNameChange}
          aria-required="true"
        />
        <small id="name-warning" className="warning-text" hidden={isValid}>
          El nombre es obligatorio para comenzar.
        </small>
      </div>
    </section>
  )
}
