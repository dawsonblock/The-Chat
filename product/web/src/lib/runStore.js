/** Normalize run bundle events by monotonic seq_no (stable ordering for UI + SSE replay). */

export function normalizeRunBundle(bundle) {
  if (!bundle) return null
  const events = [...(bundle.events || [])].sort((a, b) => (a.seq_no || 0) - (b.seq_no || 0))
  return { ...bundle, events }
}

export function maxEventSeq(events) {
  if (!events || !events.length) return 0
  return events.reduce((m, e) => Math.max(m, e.seq_no || 0), 0)
}
