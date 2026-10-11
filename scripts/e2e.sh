#!/usr/bin/env bash
# Browser smoke test (D13): starts the API in dry-run and the web server, runs Playwright headless, stops both.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="$PWD/.venv/bin/python"; [ -x "$PY" ] || PY=python3
API_PORT="${E2E_API_PORT:-8765}"; WEB_PORT="${E2E_WEB_PORT:-8787}"      # not 8000 and 8080: other things may live there
export E2E_API_KEY="clk_personal_e2e$(date +%s)000000000000000000000000000000"
export API_DEMO_KEY="$E2E_API_KEY"
export PYTHONPATH=packages/core:services/api APP_ENV=test CHAIN_MODE=dry-run WEB_ORIGIN="http://127.0.0.1:${WEB_PORT}" ANCHOR_WAIT_SECONDS=5
export APP_URL="http://127.0.0.1:${WEB_PORT}" API_URL="http://127.0.0.1:${API_PORT}"
"$PY" -m uvicorn carbonledger_api.main:create_app --factory --port "$API_PORT" --log-level warning &
API=$!
(cd apps/web && "$PY" -m http.server "$WEB_PORT" --bind 127.0.0.1 >/dev/null 2>&1) &
WEB=$!
trap 'kill $API $WEB 2>/dev/null || true' EXIT
for i in $(seq 1 40); do curl -sf "$API_URL/health" >/dev/null && curl -sf "$APP_URL/" >/dev/null && break; sleep 0.25; done
curl -sf "$API_URL/health" | grep -q '"chain"' || { echo "e2e: the API on $API_URL is not ours"; exit 1; }
(cd apps/web && npx playwright test "$@")
