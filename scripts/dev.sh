#!/usr/bin/env bash
# Starts the API (port 8000) and the web app (port 8080) for local work. Reads .env if present, else dry-run defaults.
# Usage: scripts/dev.sh        Stop with Ctrl-C.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f .env ]; then set -a; . ./.env; set +a; fi
export APP_ENV="${APP_ENV:-dev}" CHAIN_MODE="${CHAIN_MODE:-dry-run}" API_PORT="${API_PORT:-8000}" WEB_PORT="${WEB_PORT:-8080}"
export WEB_ORIGIN="${WEB_ORIGIN:-http://127.0.0.1:${WEB_PORT}}"
export PYTHONPATH=packages/core:services/api
PY="$PWD/.venv/bin/python"; [ -x "$PY" ] || PY=python3
echo "API on http://127.0.0.1:${API_PORT} (chain: ${CHAIN_MODE}), app on ${WEB_ORIGIN}"
"$PY" -m uvicorn carbonledger_api.main:create_app --factory --port "$API_PORT" &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT
echo "If port ${API_PORT} is taken by something else, run: API_PORT=8765 WEB_PORT=8787 scripts/dev.sh and open ${WEB_ORIGIN}/?ledger=solana-devnet&api=http://127.0.0.1:${API_PORT}"
(cd apps/web && "$PY" -m http.server "$WEB_PORT" --bind 127.0.0.1)
