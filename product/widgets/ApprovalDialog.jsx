import React from 'react'

export function ApprovalDialog({ approval, onDecision }) {
  if (!approval) return null
  return (
    <div className="approval-card">
      <div className="row space-between">
        <strong>{approval.title}</strong>
        <span className="status-badge waiting_approval">{approval.risk}</span>
      </div>
      <div>{approval.reason}</div>
      <pre className="small">{JSON.stringify(approval.argsPreview || approval.args_preview || {}, null, 2)}</pre>
      <div className="row">
        <button className="primary" onClick={() => onDecision('approve')}>Approve</button>
        <button className="secondary" onClick={() => onDecision('deny')}>Deny</button>
      </div>
    </div>
  )
}
