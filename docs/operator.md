# Operator guide

## Local run

- Backend: `uvicorn backend.main:app --reload --port 8000`
- Frontend: `cd product/web && npm run dev`
- See [`DEPLOYMENT.md`](DEPLOYMENT.md) for env vars.

## Primary flows

1. **Chat** — create conversation, send message → `POST /api/runs/chat` → worker runs `extract_page` / `summarize_text` / `crawl_site` as needed.
2. **Approvals** — gated tools pause the run (`waiting_approval`); user calls `POST /api/runs/{id}/approve`.
3. **Artifacts** — listed under `/api/artifacts`; content at `/api/files/{id}/content` (optional `?preview_only=true`).
4. **Workflows** — register spec, `POST /api/workflows/{version_id}/run`, same worker queue.

## Observability

- `JSON_LOGS=true` for JSON log lines.
- `GET /api/health` (liveness), `GET /api/ready` (readiness hook).

## Import program (v0.8)

Per-repo audits: [`import-audit/`](import-audit/). Pass order: [`v08-PASSES.md`](v08-PASSES.md).
