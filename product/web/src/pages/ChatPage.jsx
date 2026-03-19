import React, { useEffect, useRef, useState } from 'react'
import { api, API_BASE, eventStream, storage } from '../api'
import { maxEventSeq, normalizeRunBundle } from '../lib/runStore'
import { RunTimeline } from '@widgets/RunTimeline'

export function ChatPage({ user: _user }) {
  const [conversations, setConversations] = useState([])
  const [currentConversationId, setCurrentConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [runId, setRunId] = useState(null)
  const [runEvents, setRunEvents] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [conversationRuns, setConversationRuns] = useState([])
  const [attachedFiles, setAttachedFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [selectedRunId, setSelectedRunId] = useState(null)
  const streamRef = useRef(null)

  const loadConversations = async () => {
    const rows = await api('/api/conversations')
    setConversations(rows)
    if (!currentConversationId && rows[0]) setCurrentConversationId(rows[0].id)
  }

  const loadConversationRuns = async (conversationId) => {
    if (!conversationId) return
    const rows = await api(`/api/conversations/${conversationId}/runs`)
    setConversationRuns(rows)
    if (!runId && rows[0]) setSelectedRunId(rows[0].id)
  }

  useEffect(() => { loadConversations().catch(console.error) }, [])

  useEffect(() => {
    if (!currentConversationId) return
    api(`/api/conversations/${currentConversationId}`).then((data) => setMessages(data.messages || [])).catch(console.error)
    loadConversationRuns(currentConversationId).catch(console.error)
  }, [currentConversationId])

  useEffect(() => () => streamRef.current?.close(), [])

  useEffect(() => {
    if (!selectedRunId) return
    streamRef.current?.close()
    api(`/api/runs/${selectedRunId}/bundle`).then((bundle) => {
      const norm = normalizeRunBundle(bundle)
      setRunId(selectedRunId)
      setRunEvents(norm.events || [])
      const st = norm.run?.status
      const lastSeq = maxEventSeq(norm.events)
      if (['queued', 'running', 'waiting_approval'].includes(st)) {
        streamRef.current = eventStream(`/api/runs/${selectedRunId}/events`, (event) => {
          setRunEvents((current) => {
            if (current.some((item) => item.seq_no === event.seq_no)) return current
            return [...current, event]
          })
          if (event.type === 'message.delta') {
            setMessages((current) => {
              const copy = [...current]
              const last = copy[copy.length - 1]
              if (last && last.role === 'assistant' && last.run_id === selectedRunId) {
                last.content += event.text
              } else {
                copy.push({ id: `assistant-${Date.now()}`, role: 'assistant', content: event.text, run_id: selectedRunId })
              }
              return copy
            })
          }
          if (event.type === 'run.completed' || event.type === 'run.failed') {
            setBusy(false)
            loadConversations().catch(console.error)
            if (currentConversationId) loadConversationRuns(currentConversationId).catch(console.error)
          }
        }, { lastEventId: lastSeq })
      }
    }).catch(console.error)
    return () => streamRef.current?.close()
  }, [selectedRunId, currentConversationId])

  const ensureConversation = async () => {
    if (currentConversationId) return currentConversationId
    const convo = await api('/api/conversations', { method: 'POST', body: JSON.stringify({ title: 'New conversation' }) })
    setConversations((rows) => [convo, ...rows])
    setCurrentConversationId(convo.id)
    return convo.id
  }

  const startRunStream = (nextRunId) => {
    setRunId(nextRunId)
    setSelectedRunId(nextRunId)
  }

  const sendMessage = async () => {
    if (!draft.trim() && attachedFiles.length === 0) return
    setBusy(true)
    setError('')
    const conversationId = await ensureConversation()
    if (draft.trim()) {
      setMessages((current) => [...current, { id: `user-${Date.now()}`, role: 'user', content: draft }])
    }
    const text = draft
    const attachments = attachedFiles.map((file) => file.id)
    setDraft('')
    setAttachedFiles([])
    try {
      const created = await api('/api/runs', {
        method: 'POST',
        body: JSON.stringify({
          kind: 'chat',
          input: { message: text, conversation_id: conversationId, attachments },
        }),
      })
      startRunStream(created.run_id)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  const onApprovalDecision = async (approvalId, decision) => {
    const rid = selectedRunId || runId
    if (!rid) return
    await api(`/api/runs/${rid}/approve`, { method: 'POST', body: JSON.stringify({ approval_id: approvalId, decision }) })
  }

  const newConversation = async () => {
    const convo = await api('/api/conversations', { method: 'POST', body: JSON.stringify({ title: 'New conversation' }) })
    setConversations((rows) => [convo, ...rows])
    setCurrentConversationId(convo.id)
    setMessages([])
    setRunEvents([])
    setConversationRuns([])
    setSelectedRunId(null)
  }

  const uploadFile = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('file', file)
      const response = await fetch(`${API_BASE}/api/files/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${storage.token()}` },
        body: form,
      })
      if (!response.ok) throw new Error('Upload failed')
      const uploaded = await response.json()
      setAttachedFiles((current) => [...current, uploaded])
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const removeAttachment = (fileId) => setAttachedFiles((current) => current.filter((file) => file.id !== fileId))

  return (
    <div className="chat-layout">
      <div className="panel-grid">
        <div className="page-header">
          <strong>Conversations</strong>
          <button className="secondary" onClick={newConversation}>New</button>
        </div>
        <div className="conversation-list">
          {conversations.map((convo) => (
            <button key={convo.id} className={`conversation-item ${convo.id === currentConversationId ? 'active' : ''}`} onClick={() => setCurrentConversationId(convo.id)}>
              <div>{convo.title}</div>
              <div className="small muted">{new Date(convo.updated_at).toLocaleString()}</div>
            </button>
          ))}
        </div>
        <div className="panel-grid panel compact-panel">
          <strong>Conversation runs</strong>
          {conversationRuns.length === 0 ? <div className="small muted">No runs yet.</div> : conversationRuns.map((item) => (
            <button key={item.id} className={`mini-run ${selectedRunId === item.id ? 'active' : ''}`} onClick={() => setSelectedRunId(item.id)}>
              <span>{item.kind}</span>
              <span className="small muted">{item.status}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="chat-column">
        <div className="messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div>{message.content}</div>
            </div>
          ))}
          {error && <div className="approval-card" style={{ color: 'var(--bad)' }}>{error}</div>}
        </div>
        {selectedRunId && (
          <div className="panel compact-panel">
            <strong className="small">Run activity</strong>
            <p className="muted small" style={{ margin: '4px 0 8px' }}>Tool calls, results, and approvals from run events.</p>
            <RunTimeline events={runEvents} onApprovalDecision={onApprovalDecision} />
          </div>
        )}
        <div className="composer">
          <textarea placeholder="Paste a URL, upload a text file, or describe the task. Example: extract this page and summarize it https://example.com" value={draft} onChange={(e) => setDraft(e.target.value)} />
          <div className="row wrap-mobile composer-tools">
            <label className="secondary file-button">
              {uploading ? 'Uploading…' : 'Attach file'}
              <input type="file" onChange={uploadFile} hidden />
            </label>
            {attachedFiles.map((file) => (
              <div key={file.id} className="attachment-chip">
                <span>{file.original_name}</span>
                <button className="secondary small-button" onClick={() => removeAttachment(file.id)}>×</button>
              </div>
            ))}
          </div>
          <div className="row space-between wrap-mobile">
            <div className="muted small">Say “crawl” with a URL to trigger the approval path. Text attachments are summarized with the prompt.</div>
            <button className="primary" disabled={busy || uploading} onClick={sendMessage}>{busy ? 'Working…' : 'Send'}</button>
          </div>
        </div>
      </div>
    </div>
  )
}
