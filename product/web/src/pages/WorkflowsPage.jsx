import React, { useEffect, useRef, useState } from 'react'
import { api, eventStream } from '../api'
import { WorkflowCanvas } from '@workflow/WorkflowCanvas'
import { RunTimeline } from '@widgets/RunTimeline'

const starter = {
  name: 'Extract and summarize page',
  nodes: [
    { id: 'extract', kind: 'tool', type: 'extract_page', config: { url: '{{input.url}}' }, position: { x: 50, y: 120 } },
    { id: 'summarize', kind: 'tool', type: 'summarize_text', config: { text: '{{last.text_content}}' }, position: { x: 320, y: 120 } },
    { id: 'out', kind: 'output', type: 'output', config: { text: '{{last.summary}}' }, position: { x: 590, y: 120 } }
  ],
  edges: [{ from: 'extract', to: 'summarize' }, { from: 'summarize', to: 'out' }]
}

export function WorkflowsPage() {
  const [spec, setSpec] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('operator_workflow_draft') || 'null') || starter
    } catch {
      return starter
    }
  })
  const [validation, setValidation] = useState(null)
  const [registered, setRegistered] = useState([])
  const [runBundle, setRunBundle] = useState(null)
  const [runUrl, setRunUrl] = useState('https://example.com')
  const [loadingRunId, setLoadingRunId] = useState(null)
  const streamRef = useRef(null)

  const load = async () => {
    const items = await api('/api/workflows')
    setRegistered(items)
  }
  useEffect(() => { load().catch(console.error) }, [])
  useEffect(() => {
    localStorage.setItem('operator_workflow_draft', JSON.stringify(spec))
  }, [spec])
  useEffect(() => () => streamRef.current?.close(), [])

  const validate = async () => {
    const result = await api('/api/workflows/validate', { method: 'POST', body: JSON.stringify({ spec }) })
    setValidation(result)
  }

  const register = async () => {
    await api('/api/workflows/register', { method: 'POST', body: JSON.stringify({ spec }) })
    await load()
  }

  const run = async (versionId) => {
    setLoadingRunId(versionId)
    const created = await api(`/api/workflows/${versionId}/run`, { method: 'POST', body: JSON.stringify({ inputs: { url: runUrl } }) })
    const initial = await api(`/api/runs/${created.run_id}/bundle`)
    setRunBundle(initial)
    streamRef.current?.close()
    streamRef.current = eventStream(`/api/runs/${created.run_id}/events`, async () => {
      const refreshed = await api(`/api/runs/${created.run_id}/bundle`)
      setRunBundle(refreshed)
      if (!['queued', 'running', 'waiting_approval'].includes(refreshed.run.status)) {
        setLoadingRunId(null)
        streamRef.current?.close()
      }
    })
  }

  return (
    <div className="grid-two workflows-layout">
      <div className="panel-grid">
        <div className="page-header"><strong>Workflow editor</strong><div className="row wrap-mobile"><button className="secondary" onClick={validate}>Validate</button><button className="secondary" onClick={() => setSpec(starter)}>Reset</button><button className="primary" onClick={register}>Register</button></div></div>
        <div className="panel"><WorkflowCanvas spec={spec} setSpec={setSpec} /></div>
        {validation && <div className="panel workflow-validation"><pre>{JSON.stringify(validation, null, 2)}</pre></div>}
      </div>
      <div className="panel-grid">
        <div className="page-header"><strong>Registered workflows</strong></div>
        <div className="panel-grid">
          {registered.map((item) => (
            <div className="panel" key={item.version_id}>
              <div className="row space-between wrap-mobile">
                <div>
                  <strong>{item.name}</strong>
                  <div className="muted small">{item.version_id}</div>
                </div>
                <button className="primary" onClick={() => run(item.version_id)} disabled={loadingRunId === item.version_id}>{loadingRunId === item.version_id ? 'Running…' : 'Run'}</button>
              </div>
              <input className="input" value={runUrl} onChange={(e) => setRunUrl(e.target.value)} />
              <div className="small muted">Nodes execute on the same runtime spine as chat runs.</div>
            </div>
          ))}
        </div>
        {runBundle && (
          <div className="panel-grid">
            <div className="page-header"><strong>Workflow run</strong></div>
            <div className="panel"><div className="muted small">{runBundle.run.id}</div><div>{runBundle.run.output_text || 'Working…'}</div></div>
            <RunTimeline events={runBundle.events} />
          </div>
        )}
      </div>
    </div>
  )
}
