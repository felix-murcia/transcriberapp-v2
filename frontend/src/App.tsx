import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import MainApp from './pages/MainApp'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<MainApp />} />
    </Routes>
  )
}
