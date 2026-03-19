import React, { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, eventStream } from '../api'
import { maxEventSeq, normalizeRunBundle } from '../lib/runStore'
import { StatusBadge } from '@widgets/StatusBadge'
import { RunTimeline } from '@widgets/RunTimeline'

export function RunsPage() {
  const { runId: routeRunId } = useParams()
  const [runs, setRuns] = useState([])
  const [selected, setSelected] = useState(routeRunId || null)
  const [bundle, setBundle] = useState(null)
  const streamRef = useRef(null)

  const loadRuns = async () => {
    const data = await api('/api/runs')
    setRuns(data)
    if (!selected && data[0]) setSelected(data[0].id)
  }

  useEffect(() => { loadRuns().catch(console.error) }, [])
  useEffect(() => { if (routeRunId) setSelected(routeRunId) }, [routeRunId])

  useEffect(() => {
    streamRef.current?.close()
    if (!selected) return
    let cancelled = false
    api(`/api/runs/${selected}/bundle`).then((raw) => {
      if (cancelled) return
      const data = normalizeRunBundle(raw)
      setBundle(data)
      const st = data.run?.status
      const lastSeq = maxEventSeq(data.events)
      if (!['queued', 'running', 'waiting_approval'].includes(st)) return
      streamRef.current = eventStream(
        `/api/runs/${selected}/events`,
        (event) => {
          setBundle((prev) => {
            if (!prev) return prev
            const evs = [...(prev.events || [])]
            if (evs.some((x) => x.seq_no === event.seq_no)) return prev
            const next = { ...prev, events: [...evs, event] }
            if (event.type === 'run.completed' || event.type === 'run.failed') {
              api(`/api/runs/${selected}/bundle`).then((b) => { if (!cancelled) setBundle(normalizeRunBundle(b)) }).catch(console.error)
            }
            return next
          })
        },
        { lastEventId: lastSeq },
      )
    }).catch(console.error)
    return () => {
      cancelled = true
      streamRef.current?.close()
    }
  }, [selected])

  return (
    <div className="grid-two">
      <div className="panel-grid">
        <div className="page-header"><strong>Runs</strong><button className="secondary" onClick={loadRuns}>Refresh</button></div>
        <div className="panel">
          <table className="table">
            <thead><tr><th>ID</th><th>Kind</th><th>Status</th></tr></thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} onClick={() => setSelected(run.id)} style={{ cursor: 'pointer', background: run.id === selected ? 'var(--accent-soft)' : 'transparent' }}>
                  <td className="small"><Link to={`/runs/${run.id}`}>{run.id.slice(0, 8)}</Link></td>
                  <td>{run.kind}</td>
                  <td><StatusBadge status={run.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="panel-grid">
        <div className="page-header"><strong>Run detail</strong></div>
        {bundle ? (
          <>
            <div className="panel-grid panel">
              <div className="kv"><span>ID</span><span className="small">{bundle.run.id}</span></div>
              <div className="kv"><span>Kind</span><span>{bundle.run.kind}</span></div>
              <div className="kv"><span>Status</span><span><StatusBadge status={bundle.run.status} /></span></div>
              {bundle.run.failure_class && <div className="kv"><span>Failure</span><span className="small">{bundle.run.failure_class}</span></div>}
              {bundle.run.output_text && <div>{bundle.run.output_text}</div>}
              {bundle.run.error_message && <div style={{ color: 'var(--bad)' }}>{bundle.run.error_message}</div>}
            </div>
            <div className="panel-grid panel">
              <strong>Artifacts</strong>
              {(bundle.artifacts || []).length === 0 ? <div className="small muted">None</div> : (
                <ul className="small">
                  {(bundle.artifacts || []).map((a) => (
                    <li key={a.id}><Link to={`/artifacts/${a.id}`}>{a.name}</Link></li>
                  ))}
                </ul>
              )}
            </div>
            <RunTimeline
              events={bundle.events}
              onApprovalDecision={(approvalId, decision) => api(`/api/runs/${selected}/approve`, { method: 'POST', body: JSON.stringify({ approval_id: approvalId, decision }) })}
            />
          </>
        ) : <div className="panel">Select a run.</div>}
      </div>
    </div>
  )
}
