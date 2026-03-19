#!/usr/bin/env bash
# Deprecated alias — use ./start.sh local
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/start.sh" local
