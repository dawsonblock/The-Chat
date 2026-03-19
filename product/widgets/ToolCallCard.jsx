import React, { useMemo } from 'react'
import { StatusBadge } from './StatusBadge'

export function ToolCallCard({ tool }) {
  const argsText = useMemo(() => JSON.stringify(tool?.args || {}, null, 2), [tool])
  return (
    <div className="tool-card">
      <div className="row space-between">
        <strong>{tool?.toolName || tool?.tool_name}</strong>
        <StatusBadge status={tool?.status || 'running'} />
      </div>
      <pre className="small">{argsText}</pre>
    </div>
  )
}
