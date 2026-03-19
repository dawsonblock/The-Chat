import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, API_BASE, storage } from '../api'

function ArtifactContent({ artifact }) {
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!artifact?.id) return
    setPreview(null)
    setError('')
    api(`/api/files/${artifact.id}/content?preview_only=true`)
      .then(setPreview)
      .catch((e) => setError(e.message))
  }, [artifact?.id])

  if (!artifact) return <div className="panel">Select an artifact.</div>

  const token = storage.token()
  const rawUrl = token ? `${API_BASE}${artifact.uri}?token_passthrough=${encodeURIComponent(token)}` : `${API_BASE}${artifact.uri}`
  const mime = artifact.mime_type || ''
  const htmlish = mime.includes('html')

  if (error) return <div className="panel" style={{ color: 'var(--bad)' }}>{error}</div>

  if (htmlish && preview?.snippet) {
    return (
      <div className="panel-grid panel artifact-html-preview">
        <div className="row space-between wrap-mobile">
          <strong>{artifact.name}</strong>
          <a className="secondary" href={rawUrl} target="_blank" rel="noreferrer">Open sanitized view</a>
        </div>
        {preview.truncated && <div className="small muted">Showing preview; full length {preview.full_length} chars.</div>}
        <div className="artifact-html" dangerouslySetInnerHTML={{ __html: preview.snippet }} />
      </div>
    )
  }

  return (
    <div className="panel-grid panel">
      <div className="row space-between wrap-mobile">
        <strong>{artifact.name}</strong>
        <a className="secondary" href={rawUrl} target="_blank" rel="noreferrer">Open raw</a>
      </div>
      {preview?.truncated && <div className="small muted">Truncated preview; full length {preview.full_length} chars.</div>}
      <pre>{preview?.snippet || artifact.preview || 'No preview available.'}</pre>
    </div>
  )
}

export function ArtifactsPage() {
  const { artifactId } = useParams()
  const [artifacts, setArtifacts] = useState([])
  const [selected, setSelected] = useState(artifactId || null)
  const [detail, setDetail] = useState(null)

  const load = async () => {
    const rows = await api('/api/artifacts')
    setArtifacts(rows)
    if (!selected && rows[0]) setSelected(rows[0].id)
  }

  useEffect(() => { load().catch(console.error) }, [])
  useEffect(() => { if (artifactId) setSelected(artifactId) }, [artifactId])
  useEffect(() => {
    if (!selected) return
    api(`/api/artifacts/${selected}`).then(setDetail).catch(console.error)
  }, [selected])

  return (
    <div className="grid-two artifact-browser">
      <div className="panel-grid">
        <div className="page-header"><strong>Artifacts</strong><button className="secondary" onClick={load}>Refresh</button></div>
        <div className="panel artifact-list">
          {artifacts.map((artifact) => (
            <Link key={artifact.id} to={`/artifacts/${artifact.id}`} className={`artifact-list-item ${artifact.id === selected ? 'active' : ''}`} onClick={() => setSelected(artifact.id)}>
              <div className="row space-between wrap-mobile">
                <strong>{artifact.name}</strong>
                <span className="small muted">{artifact.kind}</span>
              </div>
              <div className="small muted">Run {artifact.run_id.slice(0, 8)} · {new Date(artifact.created_at).toLocaleString()}</div>
              <div className="small line-clamp">{artifact.preview}</div>
            </Link>
          ))}
        </div>
      </div>
      <div className="panel-grid">
        <div className="page-header"><strong>Artifact detail</strong></div>
        {detail ? (
          <>
            <div className="panel-grid panel">
              <div className="kv"><span>ID</span><span>{detail.id}</span></div>
              <div className="kv"><span>Run</span><span><Link to={`/runs/${detail.run_id}`}>{detail.run_id}</Link></span></div>
              <div className="kv"><span>Type</span><span>{detail.kind} · {detail.mime_type || 'n/a'}</span></div>
            </div>
            <ArtifactContent artifact={detail} />
          </>
        ) : <div className="panel">No artifact selected.</div>}
      </div>
    </div>
  )
}
