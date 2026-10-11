#!/usr/bin/env bash
# The one gate. CI calls this. Exit non-zero on any failure.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
export PYTHONPATH=packages/core:services/api
"$PY" -m pytest -q
"$PY" rules/roots/check_roots.py .
"$PY" scripts/scan_secrets.py .
for f in $(find apps/web/js -name '*.js' ! -name 'geo.js'); do node --check "$f"; done
node scripts/export_estimator.mjs >/dev/null
git diff --exit-code -- conformance packages/core/carbonledger/data_factors.json
if [ -f apps/web/package-lock.json ] && [ -d apps/web/node_modules ]; then (cd apps/web && npm test --silent); fi
echo "check.sh: all green"
