import { createContext, useContext, useEffect, useState } from 'react'
import { getBookingHealth } from '../api/availability'

const BackendStatusContext = createContext({ bookingStatus: 'checking', retry: () => {} })

export function BackendStatusProvider({ children }) {
  const [bookingStatus, setBookingStatus] = useState('checking')
  const [retryKey, setRetryKey] = useState(0)

  useEffect(() => {
    let active = true
    const check = () => getBookingHealth()
      .then(() => { if (active) setBookingStatus('ready') })
      .catch(() => { if (active) setBookingStatus('unavailable') })

    check()
    const interval = window.setInterval(check, 30000)
    window.addEventListener('online', check)
    const offline = () => setBookingStatus('unavailable')
    window.addEventListener('offline', offline)
    return () => {
      active = false
      window.clearInterval(interval)
      window.removeEventListener('online', check)
      window.removeEventListener('offline', offline)
    }
  }, [retryKey])

  return (
    <BackendStatusContext.Provider value={{
      bookingStatus,
      retry: () => { setBookingStatus('checking'); setRetryKey((key) => key + 1) },
    }}>
      {children}
    </BackendStatusContext.Provider>
  )
}

export const useBackendStatus = () => useContext(BackendStatusContext)
