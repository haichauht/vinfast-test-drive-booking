/**
 * App.jsx — Bộ định tuyến (router) của toàn site + cổng kiểm tra backend.
 *
 * Quyết định URL nào hiện trang nào, và chặn không cho vào site khi backend chưa chạy.
 *
 * Chứa gì:
 * - Bảng route:  "/" → HomePage  ·  "/models/:carId" → CarDetailPage  ·  "/booking" → BookingPage
 *                "/after-sales" → AfterSalesPage  ·  "/charging" → ChargingPage
 * - Route chuyển hướng: "/cars/:carId" → /booking?car=…  ·  "/agent" → /booking
 *                       "/home" và mọi URL lạ → "/"
 * - BackendGate: màn "Đang kết nối backend…" và màn "Backend hiện không khả dụng" + nút thử lại.
 *   LƯU Ý: backend chết thì KHÔNG trang nào hiện ra — đây là lý do web trắng khi quên chạy backend.
 * - RouteEffects: đổi trang thì cuộn lên đầu; URL có #anchor thì cuộn mượt tới đúng mục.
 *
 * Sửa ở đây khi: thêm/đổi đường dẫn trang, hoặc sửa giao diện 2 màn hình chờ/lỗi backend.
 */
import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { CarDetailPage } from './pages/CarDetailPage'
import { BookingPage } from './pages/BookingPage'
import { AfterSalesPage } from './pages/AfterSalesPage'
import { ChargingPage } from './pages/ChargingPage'
import { BackendStatusProvider, useBackendStatus } from './context/BackendStatusContext'

function BackendGate({ children }) {
  const { bookingStatus, retry } = useBackendStatus()

  if (bookingStatus === 'checking') {
    return <main className="backend-gate"><div className="backend-gate__loader" /><p>Đang kết nối backend…</p></main>
  }

  if (bookingStatus === 'unavailable') {
    return (
      <main className="backend-gate backend-gate--error">
        <div>
          <span>Không thể tải dữ liệu</span>
          <h1>Backend hiện không khả dụng.</h1>
          <p>Frontend chỉ sử dụng dữ liệu từ backend. Hãy khởi động service tại cổng 8000 rồi thử kết nối lại.</p>
          <button type="button" onClick={retry}>Thử kết nối lại</button>
        </div>
      </main>
    )
  }

  return children
}

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
        <Route path="/cars/:carId" element={<LegacyCarRedirect />} />
        <Route path="/models/:carId" element={<CarDetailPage />} />
        <Route path="/booking" element={<BookingPage />} />
        <Route path="/after-sales" element={<AfterSalesPage />} />
        <Route path="/charging" element={<ChargingPage />} />
        <Route path="/agent" element={<Navigate to="/booking" replace />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

function LegacyCarRedirect() {
  const { carId } = useParams()
  return <Navigate to={`/booking?car=${encodeURIComponent(carId)}`} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <BackendStatusProvider>
        <BackendGate><AppRoutes /></BackendGate>
      </BackendStatusProvider>
    </BrowserRouter>
  )
}
