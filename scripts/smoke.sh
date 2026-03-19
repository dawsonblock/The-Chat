#!/usr/bin/env bash
set -euo pipefail
curl -sf http://localhost:8000/api/health >/dev/null
curl -sf http://localhost:8000/api/ready >/dev/null
curl -sf http://localhost:5173 >/dev/null
printf 'smoke ok
'
