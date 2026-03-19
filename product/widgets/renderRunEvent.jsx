import React from 'react'
import { ToolCallCard } from './ToolCallCard'
import { ToolResultCard } from './ToolResultCard'
import { ApprovalDialog } from './ApprovalDialog'
import { StatusBadge } from './StatusBadge'
import { ArtifactPreview } from './ArtifactPreview'

/**
 * Single event → widget mapping for run timelines and chat activity.
 * @param {object} event — normalized run event (type, seq_no, …)
 * @param {{ onApprovalDecision?: (id: string, decision: string) => void }} handlers
 */
export function renderRunEvent(event, handlers = {}) {
  const { onApprovalDecision } = handlers
  const key = `${event.seq_no}-${event.type}`

  if (event.type === 'run.status') {
    return (
      <div key={key} className="panel">
        <StatusBadge status={event.status} />
      </div>
    )
  }
  if (event.type === 'tool.started') {
    return <ToolCallCard key={key} tool={event.tool} />
  }
  if (event.type === 'tool.finished') {
    return <ToolResultCard key={key} result={event.result} />
  }
  if (event.type === 'approval.requested') {
    return (
      <ApprovalDialog
        key={key}
        approval={event.approval}
        onDecision={(decision) => onApprovalDecision?.(event.approval.id, decision)}
      />
    )
  }
  if (event.type === 'artifact.created') {
    return <ArtifactPreview key={key} artifact={event.artifact} />
  }
  if (event.type === 'run.failed') {
    return (
      <div key={key} className="approval-card" style={{ color: 'var(--bad)' }}>
        {event.error?.message || 'Run failed.'}
      </div>
    )
  }
  return null
}
