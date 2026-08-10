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
import { useLayoutEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
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

  useLayoutEffect(() => {
    if ('scrollRestoration' in window.history) window.history.scrollRestoration = 'manual'

    let secondFrame
    let hashObserver
    let hashTimeout
    const firstFrame = window.requestAnimationFrame(() => {
      if (location.hash) {
        const scrollToHash = () => {
          const target = document.getElementById(decodeURIComponent(location.hash.slice(1)))
          if (!target) return false
          target.scrollIntoView({ behavior: 'smooth', block: 'start' })
          hashObserver?.disconnect()
          if (hashTimeout) window.clearTimeout(hashTimeout)
          return true
        }

        // Catalogue/backend có thể trả về sau khi RouteEffects đã mount. Theo dõi DOM
        // trong thời gian ngắn để anchor của section động (như model 3D) vẫn hoạt động.
        if (!scrollToHash()) {
          hashObserver = new MutationObserver(scrollToHash)
          hashObserver.observe(document.body, { childList: true, subtree: true })
          hashTimeout = window.setTimeout(() => hashObserver?.disconnect(), 5000)
        }
      } else {
        window.scrollTo({ top: 0, behavior: 'instant' })
        // Safari đôi khi phục hồi vị trí cũ sau frame đầu. Frame thứ hai giữ chắc
        // màn hình mở đầu ở hero thay vì nhảy xuống video trong trang chủ.
        secondFrame = window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: 'instant' }))
      }
    })
    return () => {
      window.cancelAnimationFrame(firstFrame)
      if (secondFrame) window.cancelAnimationFrame(secondFrame)
      if (hashTimeout) window.clearTimeout(hashTimeout)
      hashObserver?.disconnect()
    }
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

export default function App() {
  return (
    <BrowserRouter>
      <BackendStatusProvider>
        <BackendGate><AppRoutes /></BackendGate>
      </BackendStatusProvider>
    </BrowserRouter>
  )
}
