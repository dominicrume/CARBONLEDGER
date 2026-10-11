#!/usr/bin/env bash
# Starts the API (port 8000) and the web app (port 8080) for local work. Reads .env if present, else dry-run defaults.
# Usage: scripts/dev.sh        Stop with Ctrl-C.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f .env ]; then set -a; . ./.env; set +a; fi
export APP_ENV="${APP_ENV:-dev}" CHAIN_MODE="${CHAIN_MODE:-dry-run}" WEB_ORIGIN="${WEB_ORIGIN:-http://127.0.0.1:8080}" API_PORT="${API_PORT:-8000}"
export PYTHONPATH=packages/core:services/api
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
echo "API on http://127.0.0.1:${API_PORT} (chain: ${CHAIN_MODE}), app on ${WEB_ORIGIN}"
"$PY" -m uvicorn carbonledger_api.main:create_app --factory --port "$API_PORT" &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT
(cd apps/web && "$PY" -m http.server 8080 --bind 127.0.0.1)
