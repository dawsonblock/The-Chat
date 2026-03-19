import React from 'react'
import { ArtifactPreview } from './ArtifactPreview'

function SummaryRows({ output }) {
  if (!output) return null
  const rows = Object.entries(output).slice(0, 6)
  return <div className="panel-grid">{rows.map(([key, value]) => <div key={key} className="kv compact"><span>{key}</span><span>{typeof value === 'string' ? value.slice(0, 140) : JSON.stringify(value).slice(0, 140)}</span></div>)}</div>
}

export function ToolResultCard({ result }) {
  const artifacts = result?.artifacts || []
  return (
    <div className="result-card">
      <div className="row space-between wrap-mobile">
        <strong>{result?.ok ? 'Tool result' : 'Tool error'}</strong>
        <span className={result?.ok ? 'muted' : ''}>{result?.ok ? 'ok' : result?.error?.code || 'error'}</span>
      </div>
      {result?.ok ? (
        <>
          <SummaryRows output={result.output || {}} />
          <details>
            <summary className="small muted">Full output</summary>
            <pre className="small">{JSON.stringify(result.output || {}, null, 2)}</pre>
          </details>
        </>
      ) : <div className="small" style={{ color: 'var(--bad)' }}>{result?.error?.message || 'The tool failed.'}</div>}
      {artifacts.length > 0 && <div className="panel-grid">{artifacts.map((artifact) => <ArtifactPreview key={artifact.id} artifact={artifact} />)}</div>}
    </div>
  )
}
