const API_BASE = import.meta.env.VITE_HUMAN_REVIEW_API_BASE_URL || '/api/v1/human-review'

function messageFrom(payload, fallback) {
  return payload?.detail?.message || payload?.message || fallback
}

async function request(path, { token, body, method = 'GET', blob = false } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (response.status === 204) return null
  if (response.ok && blob) return response.blob()
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(messageFrom(payload, 'Không thể xử lý yêu cầu.'))
    error.code = payload?.detail?.code || 'REQUEST_FAILED'
    error.status = response.status
    throw error
  }
  return payload
}

export const api = {
  login: (username, password) => request('/auth/login', { method: 'POST', body: { username, password } }),
  logout: (token) => request('/auth/logout', { method: 'POST', token }),
  me: (token) => request('/me', { token }),
  queue: (token) => request('/reviews', { token }),
  detail: (token, caseId) => request(`/reviews/${caseId}`, { token }),
  save: (token, caseId, body) => request(`/reviews/${caseId}`, { token, method: 'PUT', body }),
  exportCsv: (token) => request('/reviews/export', { token, blob: true }),
}
