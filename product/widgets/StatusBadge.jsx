import React from 'react'

export function StatusBadge({ status }) {
  return <span className={`status-badge ${status || 'queued'}`}>{status || 'queued'}</span>
}
