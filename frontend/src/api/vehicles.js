import { apiGet } from './client'

const toQuery = (filters) => {
  const query = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value))
  })
  const serialized = query.toString()
  return serialized ? `?${serialized}` : ''
}

export const getVehicles = (filters = {}, options = {}) => {
  const query = toQuery(filters)
  return apiGet(`/vehicles${query}`, { ...options, cacheKey: `vehicles:${query}` })
}

export const getVehicle = (vehicleId, options = {}) =>
  apiGet(`/vehicles/${encodeURIComponent(vehicleId)}`, { ...options, cacheKey: `vehicle:${vehicleId}` })

export const prefetchVehicle = (vehicleId) => getVehicle(vehicleId).catch(() => undefined)
