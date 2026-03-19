# Import audit: Tool UI

## Repo

- **name:** tool-ui
- **commit pinned:** _TBD_
- **local path:** _e.g. `/path/to/tool-ui-main`_

## Purpose (1–2 sentences)

Rich tool-call / tool-result cards, structured data viewers, approvals UX, and artifact previews—**presentational** components bound to Operator One event shapes.

## Target destination in operator-one

- `product/widgets/`
- `product/web/src/components/chat/`
- `product/web/src/components/runs/`

## Directory classification

| Path | Purpose | Action | Destination | Notes |
|------|---------|--------|-------------|-------|
| _(inspect)_ | tool / result cards | ADAPT | `product/widgets/` | No network inside widgets |
| _(inspect)_ | JSON / table viewers | ADAPT | `product/widgets/data-viewers/` | |
| _(inspect)_ | approvals UI | ADAPT | `product/widgets/ApprovalDialog.jsx` successor | Calls existing approve API |
| _(inspect)_ | artifact preview | ADAPT | `product/web/src/pages/ArtifactsPage.jsx` | |
| demo apps / stores | scaffolding | IGNORE | — | |

## Conflict detection

- [ ] widget-owned fetch clients
- [ ] parallel event stores

## Data mapping

| Upstream (conceptual) | operator-one |
|-----------------------|--------------|
| Tool step | `RunEvent` `tool.started` / `tool.finished` |
| Approval | `approval.requested` payload |

## Deletions triggered by this import

- `ToolCallCard` / `ToolResultCard` / `ApprovalDialog` placeholders when parity reached

## Integration checks

- [ ] Components render from real `bundle.events`
- [ ] Approve/deny hits `/api/runs/{id}/approve`
