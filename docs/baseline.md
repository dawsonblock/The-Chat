# Baseline snapshot (Phase 0)

**Branch:** `operator-one-hardening`  
**Recorded:** 2026-03-19  
**App version string:** `0.7.0` ([`backend/main.py`](../backend/main.py))

This document is the **as-built** inventory before enforcing a single runtime spine, unified event contract, and API cuts described in [`docs/HARDENING_ROADMAP.md`](HARDENING_ROADMAP.md).

---

## Target loop (authoritative for hardening)

```
input (chat | workflow)
  → run created
  → runtime executes
  → events emitted
  → persisted
  → streamed to UI
  → user interaction (approval if needed)
  → completion
```

**Gaps vs target:** see *Known alternative paths* below.

---

## Runtime entry points

| Location | Role |
|----------|------|
| [`backend/main.py`](../backend/main.py) | FastAPI app, CORS, `lifespan`: `init_db()`, `requeue_interrupted_runs()`, starts **async worker** `runtime_worker_loop` |
| [`core/runtime/worker.py`](../core/runtime/worker.py) | Polls DB for `queued` runs; dispatches `execute_chat_run` / `execute_workflow_run` with timeout |
| [`core/runtime/execution/chat_run.py`](../core/runtime/execution/chat_run.py) | Chat run body: may call **`dispatcher.run_tool`** and **`provider.generate`** (not only a single `RuntimeEngine.run`) |
| [`core/runtime/execution/workflow_run.py`](../core/runtime/execution/workflow_run.py) | Workflow run body |
| [`core/tools/dispatcher.py`](../core/tools/dispatcher.py) | Tool execution, policies, approvals, idempotency |
| [`core/runtime/executor.py`](../core/runtime/executor.py) | Re-exports cancel + execution helpers (compat layer) |
| [`api/openai_compat/router.py`](../api/openai_compat/router.py) | **`/v1/chat/completions`** → **`provider.generate`** (Open WebUI); **bypasses run queue** |

**Queue:** in-process asyncio worker + DB-backed `runs.status`, not Redis/RQ.

---

## HTTP surfaces

### App root (no prefix)

| Method | Path |
|--------|------|
| GET | `/api/health` |
| GET | `/api/ready` |

### Public API (`/api/...`)

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/auth/login` | |
| POST | `/api/auth/logout` | |
| GET | `/api/auth/me` | |
| GET | `/api/conversations` | |
| POST | `/api/conversations` | |
| GET | `/api/conversations/{id}` | |
| GET | `/api/conversations/{id}/runs` | |
| POST | `/api/files/upload` | |
| GET | `/api/files/uploaded/{file_id}` | |
| GET | `/api/files/{artifact_id}` | |
| GET | `/api/files/{artifact_id}/content` | |
| GET | `/api/artifacts` | |
| GET | `/api/artifacts/{artifact_id}` | |
| GET | `/api/runs` | |
| POST | `/api/runs/chat` | Creates **chat** run (`queued`) |
| GET | `/api/runs/{run_id}` | |
| GET | `/api/runs/{run_id}/bundle` | |
| POST | `/api/runs/{run_id}/approve` | |
| POST | `/api/runs/{run_id}/cancel` | |
| GET | `/api/runs/{run_id}/events` | SSE (+ `last_event_id`) |
| GET | `/api/tools` | |
| GET | `/api/tools/meta/policies` | |
| PUT | `/api/tools/meta/policies/{tool_name}` | |
| GET | `/api/tools/{tool_name}` | |
| GET | `/api/workflows` | |
| POST | `/api/workflows/validate` | |
| POST | `/api/workflows/register` | |
| POST | `/api/workflows/{workflow_version_id}/run` | Creates **workflow** run |

### Internal API

| Prefix | Purpose |
|--------|---------|
| `/internal/intake/*` | `POST extract`, `POST crawl`, `GET crawl/{job_id}`, `POST monitor` |

### OpenAI-compatible (external chat UI)

| Method | Path |
|--------|------|
| GET | `/v1/models` |
| POST | `/v1/chat/completions` |
| POST | `/v1/embeddings` | 501 |

---

## UI routes ([`product/web/src/App.jsx`](../product/web/src/App.jsx))

| Path | Page |
|------|------|
| `/` | → `/chat` |
| `/login` | Login (unauthenticated) |
| `/chat` | Chat |
| `/runs`, `/runs/:runId` | Runs |
| `/workflows` | Workflows |
| `/artifacts`, `/artifacts/:artifactId` | Artifacts |
| `/dashboard` | Dashboard (Open WebUI link + API probe) |
| `/settings` | Settings |

Authenticated shell wraps all except login.

---

## Persistence model (actual tables)

Defined in [`storage/models/runtime.py`](../storage/models/runtime.py) (and related):

- **`runs`** — `id`, `user_id`, `conversation_id`, `kind` (`chat` \| `workflow`), `status`, `input_payload`, `output_text`, errors, `cancel_requested`, timestamps  
- **`run_events`** — `seq_no`, `event_type`, `payload` (SSE / timeline)  
- **`tool_calls`** / **`tool_results`** — structured tool rows (not only `run_events`)  
- **`approval_requests`** — approval state  
- **`artifacts`** — file metadata + `uri`  
- **`conversations`** — chat grouping (see [`storage/models/users.py`](../storage/models/users.py) / imports)  
- **`workflow_versions`** etc. — workflow registry  

**vs hardening target:** plan calls for collapsing tool/approval into event-only rows and JSONB Postgres shapes; current code is **SQLite-first** with SQLAlchemy `JSON` columns.

---

## Event / streaming

- **Persist:** `RunEvent` rows via event pipeline ([`core/events/`](../core/events/))  
- **In-memory bus:** [`core/events/bus.py`](../core/events/bus.py) for live SSE subscribers  
- **SSE:** [`core/events/sse/stream.py`](../core/events/sse/stream.py), [`api/public/runs.py`](../api/public/runs.py) `GET .../events`  
- **Schema helpers:** [`core/events/schema.py`](../core/events/schema.py) `build_event(...)` — **not** a single `emit(event: RunEvent)` as in the target doc

---

## Working features (manual / CI)

- Session auth (any email), bearer token, SSE token passthrough  
- Chat run: queue → worker → tools / heuristic LLM / crawl & extract paths in `chat_run`  
- Workflow run: queue → worker → `workflow_run`  
- Approvals, cancel, artifact APIs, file upload  
- Open WebUI integration via `/v1` + `OPENAI_PROXY_API_KEY`  
- `pytest` + `npm run build` in CI  

---

## Known alternative paths (to remove or fold)

1. **`/v1/chat/completions`** — executes LLM **without** creating a `Run` or emitting run events.  
2. **`/internal/intake/*`** — direct intake HTTP surface (target: internal-only behind tools / service layer).  
3. **Chat runtime** — `execute_chat_run` coordinates **dispatcher + provider** directly; not a single `RuntimeEngine.run(run_id)` entry.  
4. **Dual representation** — `tool_calls` / `tool_results` **and** `run_events` for overlapping information.  
5. **Conversations** — separate model from “everything is a run” (may remain as index over runs).  

---

## How to re-verify this baseline

```bash
# Routes from OpenAPI
curl -s http://127.0.0.1:8000/openapi.json | jq '.paths | keys'

# Health
curl -s http://127.0.0.1:8000/api/health
```

Regenerate endpoint list after refactors by searching `@router.` / `@app.` in `api/` and `backend/main.py`.
