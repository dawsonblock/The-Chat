const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const storage = {
  token: () => localStorage.getItem('operator_token') || '',
  setToken: (token) => localStorage.setItem('operator_token', token),
  clearToken: () => localStorage.removeItem('operator_token')
}

function headers(extra = {}) {
  const token = storage.token()
  return { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...extra }
}

export async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...headers(options.headers || {}),
    },
  })
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`
    try {
      const body = await response.json()
      detail = body.detail?.errors ? JSON.stringify(body.detail) : body.detail || detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail)
  }
  const text = await response.text()
  return text ? JSON.parse(text) : null
}

export function eventStream(path, onEvent, opts = {}) {
  const token = storage.token()
  const url = new URL(`${API_BASE}${path}`)
  if (token) url.searchParams.set('token_passthrough', token)
  const last = opts.lastEventId != null ? String(opts.lastEventId) : '0'
  if (last && last !== '0') url.searchParams.set('last_event_id', last)
  const es = new EventSource(url)
  ;['run.created','run.status','message.delta','tool.started','tool.finished','artifact.created','approval.requested','run.failed','run.completed'].forEach((eventName) => {
    es.addEventListener(eventName, (evt) => onEvent(JSON.parse(evt.data)))
  })
  es.onmessage = (evt) => onEvent(JSON.parse(evt.data))
  return es
}

export { API_BASE }
