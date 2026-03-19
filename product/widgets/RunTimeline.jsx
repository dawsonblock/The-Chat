import React from 'react'
import { renderRunEvent } from './renderRunEvent'

export function RunTimeline({ events = [], onApprovalDecision }) {
  return (
    <div className="timeline">
      {events.map((event) => renderRunEvent(event, { onApprovalDecision }))}
    </div>
  )
}
