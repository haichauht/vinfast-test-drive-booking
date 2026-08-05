import { apiGet } from './client'

export const getBookingHealth = (options = {}) => apiGet('/booking/health', {
  ...options,
  cacheKey: 'booking-health',
  fallbackToCache: false,
})
