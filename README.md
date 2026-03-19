# The Chat

**The Chat** is a full-stack AI operator shell: chat, workflow canvas, runs, artifacts, and optional **[Open WebUI](https://github.com/open-webui/open-webui)**—all backed by a single FastAPI runtime, durable run queue, and tool policies.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Node 22](https://img.shields.io/badge/node-22+-green.svg)](https://nodejs.org/)

Repository: **[github.com/dawsonblock/The-Chat](https://github.com/dawsonblock/The-Chat)**

---

## Highlights

| Area | What you get |
|------|----------------|
| **Chat & runs** | One `runs` model for chat and workflows; async worker, cancel, SSE replay with `last_event_id` |
| **Tools** | `summarize_text`, `extract_page`, `crawl_site` with DB-backed policies, retries, approvals |
| **Intake** | SSRF-aware fetch, allow/deny hosts, dedupe, safe HTML previews |
| **UI** | React + Vite light shell: Chat, Runs, Workflows, Artifacts, Dashboard, Settings |
| **Local AI** | Heuristic fallback, or **Ollama** / any OpenAI-compatible server via env |
| **Open WebUI** | Docker Compose service + `/v1` proxy on the API for external chat UI |

---

## Quick start

### One script

```bash
git clone https://github.com/dawsonblock/The-Chat.git
cd The-Chat
./start.sh              # Docker: Ollama + API + Vite + Open WebUI
./start.sh local        # Native: .venv + API :8000 + Vite :5173
```

| URL | Service |
|-----|---------|
| [http://localhost:5173](http://localhost:5173) | Operator shell (Vite) |
| [http://localhost:8000](http://localhost:8000) | API (`/api/*`, `/v1/*` for Open WebUI) |
| [http://localhost:8080](http://localhost:8080) | Open WebUI (Docker stack only) |
| [http://localhost:11434](http://localhost:11434) | Ollama (Docker stack only) |

**First time with Docker + Ollama:** pull a model, e.g. `docker compose exec ollama ollama pull llama3.2`.

### Manual dev

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

```bash
cd product/web && npm install && npm run dev
```

Set `VITE_API_BASE` if the API is not on `http://localhost:8000`.

---

## Configuration

Copy [`.env.example`](.env.example) to `.env` and adjust. Important keys:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy URL (default SQLite under `storage/`) |
| `LLM_BACKEND` | `heuristic` or `openai_compatible` (+ `LOCAL_LLM_*` for Ollama/LM Studio) |
| `OPENAI_PROXY_API_KEY` | Bearer token for `/v1/*` (Open WebUI must match) |
| `CORS_ORIGINS` | Allowed browser origins |

Full tables: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**.

---

## Auth

There is no fixed account. Enter any email on `/login`; the backend creates a local session (Bearer token + SSE `token_passthrough`).

---

## Tests & CI

```bash
pip install -r requirements-dev.txt
pytest -q
```

```bash
cd product/web && npm run build
```

GitHub Actions: `.github/workflows/ci.yml` (Python 3.12 + Node 22).

---

## Docs

| Doc | Topic |
|-----|--------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System map and deep links |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Env, Docker, Open WebUI, Ollama, lockfile |
| [docs/](docs/) | Run model, workflows, tools, intake security, import audit |

---

## Project layout (short)

```
backend/          # FastAPI app, lifespan, worker
api/              # public + internal + OpenAI-compat routes
core/             # runtime, tools, intake, events
product/web/      # React operator shell
storage/          # models, migrations path, artifacts root
scripts/          # migrate, smoke, dev helpers
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgments

- Chat dashboard integration inspired by **[Open WebUI](https://github.com/open-webui/open-webui)**.
- This tree is a **product-owned** merge (Operator One baseline); it does not vendor upstream apps as peer checkouts.
