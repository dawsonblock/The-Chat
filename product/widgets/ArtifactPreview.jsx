import React, { useMemo, useState } from 'react'
import { API_BASE } from '../web/src/api'

export function ArtifactPreview({ artifact }) {
  const [open, setOpen] = useState(false)
  const src = useMemo(() => artifact?.uri?.startsWith('http') ? artifact.uri : `${API_BASE}${artifact?.uri || ''}`, [artifact])
  const mime = artifact?.mime_type || artifact?.mimeType || ''
  return (
    <div className="artifact-card">
      <div className="row space-between wrap-mobile">
        <div>
          <strong>{artifact.name}</strong>
          <div className="muted small">{artifact.kind} · {mime || 'unknown'}</div>
        </div>
        <div className="row wrap-mobile">
          <a className="secondary" href={src} target="_blank" rel="noreferrer">Open</a>
          <button className="secondary" onClick={() => setOpen((v) => !v)}>{open ? 'Hide' : 'Preview'}</button>
        </div>
      </div>
      {artifact.preview && <div className="small muted line-clamp">{artifact.preview}</div>}
      {open && (mime.includes('html') ? <iframe title={artifact.name} src={src} style={{ width: '100%', minHeight: 260, border: '1px solid var(--border)', borderRadius: 12 }} /> : <pre className="small">{artifact.preview || 'Preview unavailable.'}</pre>)}
    </div>
  )
}
