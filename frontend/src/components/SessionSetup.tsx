import { useAppContext } from '../context/AppContext'

export default function SessionSetup() {
  const { setSessionName, sessionInputValue, setSessionInputValue } = useAppContext()
  const isValid = sessionInputValue.trim().length >= 5

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setSessionInputValue(value)
    setSessionName(value.trim().length >= 5 ? value.trim() : '')
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
          value={sessionInputValue}
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
