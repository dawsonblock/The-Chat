import React, { useEffect, useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { api, storage } from './api'
import { ChatPage } from './pages/ChatPage'
import { RunsPage } from './pages/RunsPage'
import { WorkflowsPage } from './pages/WorkflowsPage'
import { SettingsPage } from './pages/SettingsPage'
import { LoginPage } from './pages/LoginPage'
import { ArtifactsPage } from './pages/ArtifactsPage'
import { DashboardPage } from './pages/DashboardPage'

function Shell({ user, onLogout, children }) {
  const location = useLocation()
  const navItems = [['/chat', 'Chat'], ['/runs', 'Runs'], ['/workflows', 'Workflows'], ['/artifacts', 'Artifacts'], ['/dashboard', 'Dashboard'], ['/settings', 'Settings']]
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">Operator One</div>
        <div className="brand-tagline">Runs, workflows &amp; tools in one place.</div>
        <div className="nav-section-label">Workspace</div>
        <nav>
          {navItems.map(([path, label]) => (
            <Link key={path} to={path} className={location.pathname.startsWith(path) ? 'nav-link active' : 'nav-link'}>
              {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">{user?.email}</div>
          <button type="button" className="secondary" onClick={onLogout}>
            Log out
          </button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const token = storage.token()
    if (!token) {
      setLoading(false)
      return
    }
    api('/api/auth/me').then(setUser).catch(() => storage.clearToken()).finally(() => setLoading(false))
  }, [])

  const onLogin = (session) => {
    storage.setToken(session.token)
    setUser(session.user)
    navigate('/chat')
  }

  const onLogout = async () => {
    try {
      await api('/api/auth/logout', { method: 'POST' })
    } catch {
      /* ignore logout errors */
    }
    storage.clearToken()
    setUser(null)
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="center-screen">
        <div className="loading-screen">Loading…</div>
      </div>
    )
  }
  if (!user) {
    return <Routes><Route path="*" element={<LoginPage onLogin={onLogin} />} /></Routes>
  }

  return (
    <Shell user={user} onLogout={onLogout}>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="/login" element={<Navigate to="/chat" replace />} />
        <Route path="/chat" element={<ChatPage user={user} />} />
        <Route path="/runs" element={<RunsPage />} />
        <Route path="/runs/:runId" element={<RunsPage />} />
        <Route path="/workflows" element={<WorkflowsPage />} />
        <Route path="/artifacts" element={<ArtifactsPage />} />
        <Route path="/artifacts/:artifactId" element={<ArtifactsPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Shell>
  )
}
