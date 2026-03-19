# Deployment notes

## Local

- **All-in-one:** from repo root, `./start.sh` (Docker full stack) or `./start.sh local` (native API + Vite).
- Backend: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- Frontend: `cd product/web && npm run dev` (set `VITE_API_BASE` if API is not localhost:8000)
- DB bootstrap: `./scripts/migrate.sh` **after pulling** code that adds tables/columns (or rely on app startup `init_db()`, which runs the same `ensure_schema()` path).

Stale SQLite files from an older build may miss `tool_policies` or new columns until `migrate.sh` or a normal app start runs `ensure_schema()` (which calls `create_all` plus SQLite `ALTER`s).

## Environment

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy URL (default SQLite file under `storage/`) |
| `JSON_LOGS` | `true` for JSON log lines |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `SERVICE_TOKEN` | Shared secret; required as header **`X-Service-Token`** on `/internal/intake/*` |
| `WORKER_IN_PROCESS` | `true` (default): run `runtime_worker_loop` inside the API process. `false`: start a separate **`python -m worker`** process (same `DATABASE_URL` / env). |
| `OPENAI_PROXY_API_KEY` | Bearer token for `/v1/*` OpenAI-compatible API (Open WebUI) |
| `LLM_BACKEND` | `heuristic` (default) or `openai_compatible` / `ollama` / `local` for a real model |
| `LOCAL_LLM_BASE_URL` | OpenAI-compatible root, e.g. `http://127.0.0.1:11434/v1` (Ollama) |
| `LOCAL_LLM_MODEL` | Model id (e.g. `llama3.2`); run `ollama pull <name>` before first use |
| `LOCAL_LLM_API_KEY` | Optional `Bearer` token (LM Studio / cloud gateways) |
| `LOCAL_LLM_TIMEOUT_SECONDS` | HTTP timeout for chat completions (default `120`) |
| `INTAKE_ALLOW_PRIVATE_HOSTS` | `true` only in trusted dev networks |
| `INTAKE_ALLOW_DOMAINS` | Optional allow-list of hosts |
| `INTAKE_DENY_DOMAINS` | Deny-list (default blocks obvious local names) |
| `REDIS_URL` | Optional, e.g. `redis://localhost:6379/0` — `LPUSH` on new queued runs; worker uses `BRPOP` for faster wake-up (still uses DB as source of truth). |
| `OPENWEBUI_SYNTHETIC_RUNS` | `true`: non-stream `/v1/chat/completions` creates a real **chat** run and waits for the worker (Option B). |
| `OPENWEBUI_RUN_USER_ID` | User id string stored on synthetic Open WebUI runs (default `openwebui-proxy`). |

**Auth / permissions overview:** [`docs/AUTH_MATRIX.md`](AUTH_MATRIX.md).

## Open WebUI dashboard

Compose includes an `open-webui` service on port **8080**. It uses Operator One as an OpenAI-compatible backend:

- Backend routes: `GET /v1/models`, `POST /v1/chat/completions` (Bearer `OPENAI_PROXY_API_KEY`).
- **Default:** `/v1/chat/completions` calls the LLM directly (no `Run`). **`OPENWEBUI_SYNTHETIC_RUNS=true`** uses a real run for **non-stream** requests only (needs a worker). See [`docs/baseline.md`](baseline.md).
- Match `OPENAI_API_KEY` in the Open WebUI container to `OPENAI_PROXY_API_KEY` on the backend (see `docker-compose.yml`).
- Operator shell: **Dashboard** links to Open WebUI; override the URL with `VITE_OPEN_WEBUI_URL` for the web dev server.

Embeddings are not implemented; Open WebUI features that require `/v1/embeddings` will return 501 unless you point embedding calls elsewhere.

### Local AI (Ollama)

Compose includes **Ollama** on port **11434** and sets `LLM_BACKEND=openai_compatible` with `LOCAL_LLM_BASE_URL=http://ollama:11434/v1`. Pull a model once before chatting:

```bash
docker compose exec ollama ollama pull llama3.2
```

Without Docker, install [Ollama](https://ollama.com), run `ollama serve`, set `LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1`, and `LLM_BACKEND=openai_compatible`. LM Studio and other OpenAI-compatible servers work the same way; set `LOCAL_LLM_BASE_URL` to their `/v1` base and `LOCAL_LLM_API_KEY` if required.

## Docker / Compose

Use the repository `docker-compose.yml` as a starting point; verify `DATABASE_URL` and volume mounts for `artifacts_dir` match production storage. `docker compose up` starts backend, web, and Open WebUI.

**Separate worker (optional):** set `WORKER_IN_PROCESS=false` on the API service and run the `worker` service (Compose profile **`worker`**) so only one process polls the run queue: `docker compose --profile worker up`. Ensure both services share the same `DATABASE_URL` and `SERVICE_TOKEN`.

**Redis wake-up (optional):** `docker compose --profile redis up` starts Redis on **6379**. Set `REDIS_URL=redis://localhost:6379/0` (native) or `redis://redis:6379/0` (from backend container) so new queued runs `LPUSH` and the worker `BRPOP`s for lower latency.

## CI

GitHub Actions workflow `.github/workflows/ci.yml` runs `pytest` (Python 3.12) and `npm run build` (Node 22).

## Locked dependencies

[`requirements.lock`](requirements.lock) is a **clean** transitive pin for this app only (install with `pip install -r requirements.lock`). Regenerate after changing [`requirements.txt`](requirements.txt):

```bash
python -m venv .venv && . .venv/bin/activate
pip install -U pip && pip install -r requirements.txt
pip freeze | grep -v '^-e ' > requirements.lock
```

(Adjust the `grep` if you use editable installs.)
