# Import audit: Open WebUI

## Repo

- **name:** open-webui
- **commit pinned:** _TBD_
- **local path:** _e.g. `/path/to/open-webui-main`_

## Purpose (1–2 sentences)

Mature operator-facing shell: conversation layout, sidebar, uploads, settings, and transcript rendering—**UI only**; runtime and run model stay in Operator One backend.

## Target destination in operator-one

- `product/web/`

## Directory classification

| Path | Purpose | Action | Destination | Notes |
|------|---------|--------|-------------|-------|
| _(inspect)_ | chat / shell layout | ADAPT | `product/web/src/components/shell/` | Strip backend coupling |
| _(inspect)_ | uploads UX | ADAPT | `product/web/src/components/uploads/` | Use `/api/files/upload` |
| _(inspect)_ | settings UI | ADAPT | `product/web/routes/settings/` | Wire models to future `/api/models` |
| _(inspect)_ | markdown / transcript | ADAPT | `product/web/src/components/chat/` | |
| backend inference / RAG | second brain | IGNORE | — | |

## Subsystems

### Conversation shell

- **Destination:** `product/web/src/pages/`, layout components
- **Replaces:** minimal JSX shell pieces

### Transcript rendering

- **Destination:** chat components
- **Replaces:** plain `<div>` message bodies where richer rendering is needed

## Conflict detection

- [ ] second file / artifact truth
- [ ] second job / task engine
- [ ] second auth model (must remain `core/auth` + bearer)

## Data mapping

| Upstream (conceptual) | operator-one |
|-----------------------|--------------|
| Chat message | `ConversationMessage` + run-linked assistant rows |
| Attachment | `UploadedFile` + `Artifact` from tools |

## Deletions triggered by this import

- Replaced layout / upload / transcript components only after parity

## Integration checks

- [ ] Chat still creates `/api/runs/chat` (queued → worker)
- [ ] SSE + `last_event_id` still used
- [ ] No Open WebUI API routes mounted as authoritative
