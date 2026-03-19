#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python - <<'PY'
from storage.bootstrap import init_db

init_db()
print("migrate: schema + ensure_schema ok")
PY
