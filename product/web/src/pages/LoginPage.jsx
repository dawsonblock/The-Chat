import React, { useState } from 'react'
import { api } from '../api'

export function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const session = await api('/api/auth/login', { method: 'POST', body: JSON.stringify({ email }) })
      onLogin(session)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="center-screen">
      <form className="login-shell" onSubmit={submit}>
        <div>
          <h2>Operator One</h2>
          <div className="muted">Enter any email to create a local session.</div>
        </div>
        <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@example.com" />
        {error && <div style={{ color: 'var(--bad)' }}>{error}</div>}
        <button className="primary">Login</button>
      </form>
    </div>
  )
}
