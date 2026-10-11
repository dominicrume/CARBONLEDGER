#!/usr/bin/env bash
# Container entry point. Migrates the database when one is configured, then serves the API and the app.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -n "${DATABASE_URL:-}" ]; then
  python scripts/migrate.py
fi
exec python -m uvicorn carbonledger_api.main:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="*"
