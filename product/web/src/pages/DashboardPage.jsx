import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { API_BASE } from '../api'

const defaultWebUiUrl = 'http://localhost:8080'

export function DashboardPage() {
  const webUiUrl = import.meta.env.VITE_OPEN_WEBUI_URL || defaultWebUiUrl
  const [apiStatus, setApiStatus] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetch(`${API_BASE}/api/health`)
      .then((r) => {
        if (!cancelled) setApiStatus(r.ok ? 'ok' : 'bad')
      })
      .catch(() => {
        if (!cancelled) setApiStatus('bad')
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="panel-grid">
      <header className="page-header">
        <h1>Dashboard</h1>
      </header>

      <section className="dashboard-hero">
        <h1>Your AI workspace</h1>
        <p className="dashboard-lead">
          Use the built-in chat and runs here, or open <strong>Open WebUI</strong> for a full chat UI. Open WebUI talks to this
          backend through the OpenAI-compatible API (<code>/v1/chat/completions</code>).
        </p>

        <div className="status-pills">
          <span
            className={
              apiStatus === null
                ? 'status-pill pending'
                : apiStatus === 'ok'
                  ? 'status-pill ok'
                  : 'status-pill bad'
            }
          >
            <span className="status-dot" aria-hidden />
            {apiStatus === null && 'Checking API…'}
            {apiStatus === 'ok' && 'Operator API reachable'}
            {apiStatus === 'bad' && 'Operator API unreachable — is the backend running?'}
          </span>
        </div>

        <div className="dashboard-actions">
          <a className="btn-external" href={webUiUrl} target="_blank" rel="noreferrer">
            Open Open WebUI
            <span aria-hidden>↗</span>
          </a>
          <Link to="/chat" className="btn-ghost">
            Chat in Operator
          </Link>
        </div>
      </section>

      <div className="dashboard-grid">
        <Link to="/runs" className="quick-card">
          <h3>Runs</h3>
          <p>Inspect chat and workflow runs, timelines, and tool output.</p>
        </Link>
        <Link to="/workflows" className="quick-card">
          <h3>Workflows</h3>
          <p>Design and validate workflow graphs on the canvas.</p>
        </Link>
        <Link to="/artifacts" className="quick-card">
          <h3>Artifacts</h3>
          <p>Browse files and previews produced by tools.</p>
        </Link>
        <Link to="/settings" className="quick-card">
          <h3>Settings</h3>
          <p>Session and environment notes for this shell.</p>
        </Link>
      </div>

      <div className="dashboard-note">
        <strong>Open WebUI URL:</strong> {webUiUrl}
        <br />
        Ensure <code>OPENAI_PROXY_API_KEY</code> on the backend matches <code>OPENAI_API_KEY</code> in Open WebUI (see{' '}
        <code>docker-compose.yml</code>). With Docker Compose, run{' '}
        <code>docker compose exec ollama ollama pull llama3.2</code> (or your chosen model) before first chat.
      </div>
    </div>
  )
}
