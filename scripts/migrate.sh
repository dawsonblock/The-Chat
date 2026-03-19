#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python - <<'PY'
from storage.bootstrap import init_db

init_db()
print("migrate: schema + ensure_schema ok")
PY
if [[ "${BACKFILL_RUN_EVENTS:-}" == "1" ]]; then
  python - <<'PY'
from storage.migrate import backfill_run_events_from_tool_calls

print("backfill_run_events_from_tool_calls:", backfill_run_events_from_tool_calls())
PY
fi
