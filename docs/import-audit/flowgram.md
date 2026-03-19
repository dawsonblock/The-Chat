# Import audit: Flowgram (flowgram.ai)

## Repo

- **name:** flowgram.ai
- **commit pinned:** _TBD_
- **local path:** _e.g. `/path/to/flowgram.ai-main`_

## Purpose (1–2 sentences)

Workflow **editor** UX: graph canvas, inspector, serialization, and optional execution overlays—compiled to Operator One `WorkflowSpec`, executed only by host runtime.

## Target destination in operator-one

- `product/workflow/editor/`
- `product/workflow/graph/`
- `product/workflow/inspector/`
- `product/workflow/export/`

## Directory classification

| Path | Purpose | Action | Destination | Notes |
|------|---------|--------|-------------|-------|
| _(inspect)_ | canvas / graph UI | COPY/ADAPT | `product/workflow/editor/` | Mount under app routes only |
| _(inspect)_ | inspector / forms | ADAPT | `product/workflow/inspector/` | |
| _(inspect)_ | graph JSON model | ADAPT | `product/workflow/graph/` | Compile → `WorkflowSpec` |
| _(inspect)_ | execution engine | IGNORE | — | Host `workflow_run` is sole executor |
| _(inspect)_ | standalone shell / auth | IGNORE | — | |

## Conflict detection

- [ ] second workflow persistence truth (`Workflow` / `WorkflowVersion` only)
- [ ] second execution loop
- [ ] second event model

## Data mapping

| Upstream (conceptual) | operator-one |
|-----------------------|--------------|
| Graph document | `WorkflowSpec` JSON |
| Node | `nodes[]` entry (`kind`, `type`, `config`) |
| Edge | _extend spec if needed in v0.9+_ |

## Deletions triggered by this import

- `WorkflowCanvas.jsx` stub when Flowgram-backed editor reaches parity

## Integration checks

- [ ] Save / export produces spec that passes `validate_workflow_spec`
- [ ] `/api/workflows/{id}/run` still enqueues `kind=workflow` runs for worker
