#!/usr/bin/env bash
# One entrypoint: full stack (Docker) or local API + Vite.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: ./start.sh [docker|local]"
  echo "  docker (default) — Ollama, API, Vite shell, Open WebUI (docker compose up --build)"
  echo "  local            — .venv + uvicorn :8000 + npm dev :5173 (LLM_BACKEND=heuristic unless set)"
  exit "${1:-0}"
}

MODE="${1:-docker}"
case "$MODE" in
  -h | --help | help) usage 0 ;;
esac

start_docker() {
  echo "Operator One — starting full stack with Docker Compose…"
  echo "  • Operator shell   http://localhost:5173"
  echo "  • API              http://localhost:8000"
  echo "  • Open WebUI       http://localhost:8080"
  echo "  • Ollama           http://localhost:11434"
  echo ""
  echo "First time with Ollama: docker compose exec ollama ollama pull llama3.2"
  echo ""
  exec docker compose up --build
}

start_local() {
  echo "Operator One — starting local API + Vite (no Docker)…"
  if ! command -v python3 >/dev/null 2>&1; then
    echo "error: python3 not found" >&2
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "error: npm not found" >&2
    exit 1
  fi

  if [ ! -d "$ROOT/.venv" ]; then
    echo "Creating .venv…"
    python3 -m venv "$ROOT/.venv"
  fi
  # shellcheck source=/dev/null
  source "$ROOT/.venv/bin/activate"
  echo "Installing Python deps…"
  pip install -q -r "$ROOT/requirements.txt"
  echo "Installing npm deps…"
  (cd "$ROOT/product/web" && npm install --silent)

  export LLM_BACKEND="${LLM_BACKEND:-heuristic}"

  cleanup() {
    local p
    for p in "${PIDS[@]:-}"; do
      kill "$p" 2>/dev/null || true
    done
  }
  PIDS=()
  trap 'cleanup; exit 0' INT TERM
  trap cleanup EXIT

  echo "  • API   http://127.0.0.1:8000  (LLM_BACKEND=$LLM_BACKEND)"
  echo "  • Web   http://127.0.0.1:5173"
  echo "Ctrl+C stops both processes."
  echo ""

  (cd "$ROOT" && exec uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000) &
  PIDS+=("$!")
  (cd "$ROOT/product/web" && exec npm run dev -- --host 127.0.0.1 --port 5173) &
  PIDS+=("$!")

  # wait for both (portable; no bash 4.3 `wait -n` — macOS ships bash 3.2)
  wait "${PIDS[0]}" "${PIDS[1]}" || true
}

case "$MODE" in
  docker | all) start_docker ;;
  local | dev) start_local ;;
  *) echo "Unknown mode: $MODE" >&2; usage 1 ;;
esac
