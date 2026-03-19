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

/** Build chat bubbles for the selected run from bundle + live SSE events (event-first transcript). */
export function transcriptFromRunEvents(run, events) {
  if (!run?.id) return []
  const ordered = [...(events || [])].sort((a, b) => (a.seq_no || 0) - (b.seq_no || 0))
  const out = []
  const msg = (run.input_payload && run.input_payload.message) || ''
  if (msg.trim()) {
    out.push({ id: `user-${run.id}`, role: 'user', content: msg, run_id: run.id })
  }
  let assistant = ''
  for (const e of ordered) {
    if (e.type === 'message.delta' && e.text) assistant += e.text
  }
  if (!assistant && run.output_text) assistant = run.output_text
  if (assistant) {
    out.push({ id: `assistant-${run.id}`, role: 'assistant', content: assistant, run_id: run.id })
  }
  return out
}
