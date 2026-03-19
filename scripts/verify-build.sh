#!/usr/bin/env bash
# Matches .github/workflows/ci.yml (backend + frontend).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Python (requirements-dev + pytest) =="
pip install -q -r requirements-dev.txt
pytest -q

echo "== Frontend (npm ci + build) =="
(cd "$ROOT/product/web" && npm ci && npm run build)

echo "== verify-build: OK =="
