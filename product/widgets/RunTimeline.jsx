import React from 'react'
import { ToolCallCard } from './ToolCallCard'
import { ToolResultCard } from './ToolResultCard'
import { ApprovalDialog } from './ApprovalDialog'
import { StatusBadge } from './StatusBadge'
import { ArtifactPreview } from './ArtifactPreview'

export function RunTimeline({ events = [], onApprovalDecision }) {
  return (
    <div className="timeline">
      {events.map((event) => {
        if (event.type === 'run.status') {
          return <div key={`${event.seq_no}-${event.type}`} className="panel"><StatusBadge status={event.status} /></div>
        }
        if (event.type === 'tool.started') {
          return <ToolCallCard key={`${event.seq_no}-${event.type}`} tool={event.tool} />
        }
        if (event.type === 'tool.finished') {
          return <ToolResultCard key={`${event.seq_no}-${event.type}`} result={event.result} />
        }
        if (event.type === 'approval.requested') {
          return <ApprovalDialog key={`${event.seq_no}-${event.type}`} approval={event.approval} onDecision={(decision) => onApprovalDecision?.(event.approval.id, decision)} />
        }
        if (event.type === 'artifact.created') {
          return <ArtifactPreview key={`${event.seq_no}-${event.type}`} artifact={event.artifact} />
        }
        if (event.type === 'run.failed') {
          return <div key={`${event.seq_no}-${event.type}`} className="approval-card" style={{ color: 'var(--bad)' }}>{event.error?.message || 'Run failed.'}</div>
        }
        return null
      })}
    </div>
  )
}
