/**
 * hooks/useSiteData.js — 3 hook để các trang lấy dữ liệu backend mà không phải tự viết fetch.
 *
 * Mỗi hook tự lo: gọi API → đổi tên trường qua adapters → trả về { loading, error }
 * và tự huỷ request khi người dùng rời trang (AbortController).
 *
 * Chứa gì:
 * - useVehicleCatalog(): danh sách xe, đã sắp xếp theo sortOrder của backend.
 *   Dùng ở HomePage, CarDetailPage (để tìm "xe tiếp theo") và BookingPage.
 * - useVehicleDetail(id): chi tiết một mẫu xe. Dùng ở CarDetailPage.
 * - usePageContent(page): nội dung trang home / charging / after-sales.
 *
 * LƯU Ý: không có dữ liệu dự phòng. Backend chết thì cars = [] và trang hiện rỗng —
 * đây là chủ ý để giao diện không bịa ra catalogue giả.
 */
import { useEffect, useMemo, useState } from 'react'
import { getPageContent } from '../api/content'
import { vehicleDetailToCar, vehicleSummaryToCar } from '../api/adapters'
import { getVehicle, getVehicles } from '../api/vehicles'

export function useVehicleCatalog() {
  const [remote, setRemote] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    getVehicles({}, { signal: controller.signal })
      .then((items) => setRemote(items.map(vehicleSummaryToCar)))
      .catch((reason) => {
        if (reason.name !== 'AbortError') setError(reason)
      })
    return () => controller.abort()
  }, [])

  const cars = useMemo(
    () => (remote || []).sort((left, right) => (left.sortOrder || 0) - (right.sortOrder || 0)),
    [remote],
  )

  return { cars, loading: remote === null && error === null, error, source: remote ? 'backend' : 'unavailable' }
}

export function useVehicleDetail(vehicleId) {
  const [car, setCar] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    setCar(null)
    setError(null)
    getVehicle(vehicleId, { signal: controller.signal })
      .then((vehicle) => setCar(vehicleDetailToCar(vehicle)))
      .catch((reason) => {
        if (reason.name !== 'AbortError') setError(reason)
      })
    return () => controller.abort()
  }, [vehicleId])

  return { car, loading: !car && !error, error }
}

export function usePageContent(page) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    getPageContent(page, { signal: controller.signal })
      .then(setData)
      .catch((reason) => {
        if (reason.name !== 'AbortError') setError(reason)
      })
    return () => controller.abort()
  }, [page])

  return { data, loading: data === null && error === null, error }
}
