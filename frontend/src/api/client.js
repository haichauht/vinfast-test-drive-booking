/**
 * api/client.js — Lõi gọi API. MỌI request từ frontend tới backend đều đi qua file này.
 *
 * Chứa gì:
 * - API_BASE_URL: mặc định "/api/v1" (Vite proxy sang backend cổng 8000).
 *   Ghi đè bằng biến VITE_API_BASE_URL trong frontend/.env.local khi deploy.
 * - apiGet(): có cache trong bộ nhớ + ETag/If-None-Match. Backend trả 304 thì dùng lại bản cũ.
 *   Mất mạng mà đã có cache thì trả cache thay vì báo lỗi.
 * - apiPost(): gửi JSON, không cache.
 * - ApiError: kiểu lỗi chuẩn có code/status/retryable — các trang dựa vào đây để hiện thông báo.
 * - clearApiCache(): xoá toàn bộ cache.
 *
 * Sửa ở đây khi: đổi địa chỉ backend, đổi câu thông báo lỗi mạng, hoặc bật/tắt cache.
 */
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')
const memoryCache = new Map()

export class ApiError extends Error {
  constructor(message, { code = 'NETWORK_ERROR', status = 0, retryable = true } = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.retryable = retryable
  }
}

export async function apiGet(path, { signal, cacheKey = path, fallbackToCache = true } = {}) {
  const cached = memoryCache.get(cacheKey)
  const headers = cached?.etag ? { 'If-None-Match': cached.etag } : {}
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { headers, signal })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    if (cached && fallbackToCache) return cached.data
    throw new ApiError('Không thể kết nối đến máy chủ.')
  }
  if (response.status === 304 && cached) return cached.data
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new ApiError(body.error?.message || 'Yêu cầu không thành công.', {
      code: body.error?.code,
      status: response.status,
      retryable: body.error?.retryable ?? response.status >= 500,
    })
  }
  memoryCache.set(cacheKey, { data: body.data, etag: response.headers.get('etag') })
  return body.data
}

export async function apiPost(path, payload, { signal } = {}) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('Không thể kết nối đến máy chủ.')
  }
  const body = await response.json().catch(() => ({}))
  if (!response.ok || body.success === false) {
    const detail = body.detail || body.error || {}
    throw new ApiError(detail.message || body.message || 'Yêu cầu không thành công.', {
      code: detail.code,
      status: response.status,
      retryable: detail.retryable ?? response.status >= 500,
    })
  }
  return body.data ?? body
}

export function clearApiCache() {
  memoryCache.clear()
}
