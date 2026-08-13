import { useEffect, useState } from 'react'
import { api } from './api.js'
import { PageState } from './components/PageState.jsx'
import { Shell } from './components/Shell.jsx'
import { AuditPage, CatalogPage, NetworkPage } from './pages/ReferencePages.jsx'
import { BookingsPage } from './pages/BookingsPage.jsx'
import { DashboardPage } from './pages/DashboardPage.jsx'
import { FleetPage } from './pages/FleetPage.jsx'
import { LoginPage } from './pages/LoginPage.jsx'
import { ShowroomSchedulePage } from './pages/ShowroomSchedulePage.jsx'
import { TeamPage } from './pages/TeamPage.jsx'
import { TransfersPage } from './pages/TransfersPage.jsx'
import { UsersPage } from './pages/UsersPage.jsx'

const TOKEN_KEY = 'p053_internal_token'

export default function App() {
  const [token, setToken] = useState(() => {
    localStorage.removeItem(TOKEN_KEY)
    return sessionStorage.getItem(TOKEN_KEY) || ''
  })
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(token))
  const [sessionError, setSessionError] = useState('')
  const [page, setPage] = useState('dashboard')

  useEffect(() => {
    if (!token) { setLoading(false); setUser(null); return }
    let active = true
    setLoading(true)
    api.me(token).then((profile) => { if (active) { setUser(profile); setSessionError('') } }).catch((error) => {
      if (active) { sessionStorage.removeItem(TOKEN_KEY); setToken(''); setUser(null); setSessionError(error.message) }
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [token])

  const login = async (username, password) => {
    const session = await api.login(username, password)
    sessionStorage.setItem(TOKEN_KEY, session.access_token)
    setUser(session.user)
    setToken(session.access_token)
    setPage('dashboard')
  }

  const logout = async () => {
    try { await api.logout(token) } catch { /* Session may already be expired. */ }
    sessionStorage.removeItem(TOKEN_KEY)
    setToken(''); setUser(null); setPage('dashboard')
  }

  if (loading) return <div className="app-loading"><PageState loading /></div>
  if (!token || !user) return <><LoginPage onLogin={login} />{sessionError && <div className="session-toast">{sessionError}</div>}</>

  const pages = {
    dashboard: <DashboardPage token={token} user={user} />,
    bookings: <BookingsPage token={token} user={user} />,
    team: <TeamPage token={token} user={user} />,
    fleet: <FleetPage token={token} user={user} />,
    schedule: <ShowroomSchedulePage token={token} user={user} />,
    network: <NetworkPage token={token} />,
    catalog: <CatalogPage token={token} />,
    transfers: <TransfersPage token={token} />,
    audit: <AuditPage token={token} />,
    users: <UsersPage token={token} />,
  }

  return <Shell token={token} user={user} page={page} onNavigate={setPage} onLogout={logout}>{pages[page] || pages.dashboard}</Shell>
}
