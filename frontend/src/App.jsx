import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { CarDetailPage } from './pages/CarDetailPage'
import { BookingPage } from './pages/BookingPage'

// TODO [BACKEND/DEPLOY]: BrowserRouter requires the production web server to
// return index.html for every non-file route (/cars/:id, /booking). Keep /api
// outside this fallback and proxy it to the backend. See ../BACKEND_HANDOFF.md.
function RouteEffects() {
  const location = useLocation()

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      if (location.hash) {
        document.querySelector(location.hash)?.scrollIntoView({ behavior: 'smooth' })
      } else {
        window.scrollTo({ top: 0, behavior: 'instant' })
      }
    })
    return () => window.cancelAnimationFrame(frame)
  }, [location.pathname, location.hash])

  return null
}

function AppRoutes() {
  return (
    <>
      <RouteEffects />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/cars/:carId" element={<CarDetailPage />} />
        <Route path="/booking" element={<BookingPage />} />
        <Route path="/agent" element={<Navigate to="/booking" replace />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
