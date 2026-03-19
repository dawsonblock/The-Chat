import React, { useState } from 'react'

export function SettingsPage() {
  const [apiBase, setApiBase] = useState(import.meta.env.VITE_API_BASE || 'http://localhost:8000')
  return (
    <div className="panel-grid">
      <div className="page-header"><strong>Settings</strong></div>
      <div className="panel-grid panel">
        <label>Backend base URL</label>
        <input className="input" value={apiBase} onChange={(e) => setApiBase(e.target.value)} />
        <div className="muted small">Change <code>VITE_API_BASE</code> in the frontend environment for a persistent value.</div>
      </div>
      <div className="panel-grid panel">
        <strong>Build notes</strong>
        <div className="muted">This build uses one runtime/event spine, one intake layer, one artifact model, and one workflow model.</div>
      </div>
    </div>
  )
}
