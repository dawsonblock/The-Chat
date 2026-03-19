import React, { useMemo, useState } from 'react'

const NODE_W = 170
const NODE_H = 86
const kinds = ['tool', 'output']
const toolTypes = ['extract_page', 'summarize_text', 'crawl_site']

function makeNode(index = 1) {
  return {
    id: `node_${Date.now()}_${index}`,
    kind: 'tool',
    type: 'extract_page',
    config: { url: '{{input.url}}' },
    position: { x: 40 + (index - 1) * 220, y: 80 + ((index - 1) % 2) * 140 },
  }
}

function nodeCenter(node) {
  return { x: (node.position?.x || 0) + NODE_W / 2, y: (node.position?.y || 0) + NODE_H / 2 }
}

export function WorkflowCanvas({ spec, setSpec }) {
  const [selectedNodeId, setSelectedNodeId] = useState(spec.nodes?.[0]?.id || null)
  const [dragging, setDragging] = useState(null)
  const [edgeDraft, setEdgeDraft] = useState({ from: '', to: '' })

  const nodes = spec.nodes || []
  const edges = useMemo(() => spec.edges || [], [spec.edges])
  const selected = nodes.find((n) => n.id === selectedNodeId) || nodes[0] || null

  const updateNode = (id, patch) => {
    setSpec((current) => ({ ...current, nodes: (current.nodes || []).map((node) => node.id === id ? { ...node, ...patch, position: patch.position || node.position } : node) }))
  }

  const addNode = () => {
    setSpec((current) => {
      const nextNode = makeNode((current.nodes || []).length + 1)
      return { ...current, nodes: [...(current.nodes || []), nextNode], edges: current.edges || [] }
    })
  }

  const removeSelected = () => {
    if (!selected) return
    setSpec((current) => {
      const nextNodes = (current.nodes || []).filter((node) => node.id !== selected.id)
      const nextEdges = (current.edges || []).filter((edge) => edge.from !== selected.id && edge.to !== selected.id)
      return { ...current, nodes: nextNodes, edges: nextEdges }
    })
    setSelectedNodeId(null)
  }

  const addEdge = () => {
    if (!edgeDraft.from || !edgeDraft.to || edgeDraft.from === edgeDraft.to) return
    setSpec((current) => {
      const exists = (current.edges || []).some((edge) => edge.from === edgeDraft.from && edge.to === edgeDraft.to)
      if (exists) return current
      return { ...current, edges: [...(current.edges || []), { from: edgeDraft.from, to: edgeDraft.to }] }
    })
    setEdgeDraft({ from: '', to: '' })
  }

  const removeEdge = (from, to) => {
    setSpec((current) => ({ ...current, edges: (current.edges || []).filter((edge) => !(edge.from === from && edge.to === to)) }))
  }

  const onPointerDown = (event, node) => {
    const rect = event.currentTarget.closest('.workflow-stage').getBoundingClientRect()
    setDragging({ id: node.id, dx: event.clientX - rect.left - (node.position?.x || 0), dy: event.clientY - rect.top - (node.position?.y || 0) })
    setSelectedNodeId(node.id)
  }

  const onPointerMove = (event) => {
    if (!dragging) return
    const rect = event.currentTarget.getBoundingClientRect()
    const nextX = Math.max(16, event.clientX - rect.left - dragging.dx)
    const nextY = Math.max(16, event.clientY - rect.top - dragging.dy)
    updateNode(dragging.id, { position: { x: nextX, y: nextY } })
  }

  const onPointerUp = () => setDragging(null)

  return (
    <div className="workflow-shell">
      <div className="row space-between wrap-mobile">
        <strong>Visual workflow graph</strong>
        <div className="row wrap-mobile">
          <button className="secondary" onClick={addNode}>Add node</button>
          <button className="secondary" onClick={removeSelected} disabled={!selected}>Remove selected</button>
        </div>
      </div>
      <div className="workflow-stage" onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerLeave={onPointerUp}>
        <svg className="workflow-svg" viewBox="0 0 960 520" preserveAspectRatio="none">
          {edges.map((edge) => {
            const from = nodes.find((node) => node.id === edge.from)
            const to = nodes.find((node) => node.id === edge.to)
            if (!from || !to) return null
            const a = nodeCenter(from)
            const b = nodeCenter(to)
            const mid = (a.x + b.x) / 2
            const path = `M ${a.x} ${a.y} C ${mid} ${a.y}, ${mid} ${b.y}, ${b.x} ${b.y}`
            return <path key={`${edge.from}-${edge.to}`} d={path} className="workflow-edge" />
          })}
        </svg>
        {nodes.map((node) => (
          <div key={node.id} className={`workflow-node ${selectedNodeId === node.id ? 'selected' : ''}`} style={{ left: node.position?.x || 0, top: node.position?.y || 0, width: NODE_W, height: NODE_H }} onPointerDown={(event) => onPointerDown(event, node)} onClick={() => setSelectedNodeId(node.id)}>
            <div className="workflow-node-kind">{node.kind}</div>
            <strong>{node.type || node.id}</strong>
            <div className="small muted">{node.id}</div>
          </div>
        ))}
      </div>
      <div className="grid-two workflow-inspector-grid">
        <div className="panel-grid panel">
          <strong>Node inspector</strong>
          {selected ? (
            <>
              <label className="small muted">Node id</label>
              <input className="input" value={selected.id} onChange={(e) => updateNode(selected.id, { id: e.target.value })} />
              <label className="small muted">Kind</label>
              <select className="input" value={selected.kind} onChange={(e) => updateNode(selected.id, { kind: e.target.value })}>
                {kinds.map((kind) => <option key={kind} value={kind}>{kind}</option>)}
              </select>
              <label className="small muted">Type</label>
              <input className="input" list="workflow-types" value={selected.type || ''} onChange={(e) => updateNode(selected.id, { type: e.target.value })} />
              <datalist id="workflow-types">{toolTypes.map((type) => <option key={type} value={type} />)}</datalist>
              <label className="small muted">Config JSON</label>
              <textarea value={JSON.stringify(selected.config || {}, null, 2)} onChange={(e) => { try { updateNode(selected.id, { config: JSON.parse(e.target.value) }) } catch {} }} />
            </>
          ) : <div className="muted">Select a node to edit it.</div>}
        </div>
        <div className="panel-grid panel">
          <strong>Connections</strong>
          <div className="row wrap-mobile">
            <select className="input" value={edgeDraft.from} onChange={(e) => setEdgeDraft((current) => ({ ...current, from: e.target.value }))}>
              <option value="">From…</option>
              {nodes.map((node) => <option key={node.id} value={node.id}>{node.id}</option>)}
            </select>
            <select className="input" value={edgeDraft.to} onChange={(e) => setEdgeDraft((current) => ({ ...current, to: e.target.value }))}>
              <option value="">To…</option>
              {nodes.map((node) => <option key={node.id} value={node.id}>{node.id}</option>)}
            </select>
            <button className="secondary" onClick={addEdge}>Add edge</button>
          </div>
          {edges.length === 0 ? <div className="muted">No edges yet.</div> : edges.map((edge) => <div key={`${edge.from}-${edge.to}`} className="kv compact"><span>{edge.from}</span><span className="row wrap-mobile"><span>{edge.to}</span><button className="secondary small-button" onClick={() => removeEdge(edge.from, edge.to)}>Remove</button></span></div>)}
          <div className="muted small">Execution follows the explicit edge list. Placeholders like {'{{input.url}}'} and {'{{last.summary}}'} are resolved at runtime.</div>
        </div>
      </div>
    </div>
  )
}
