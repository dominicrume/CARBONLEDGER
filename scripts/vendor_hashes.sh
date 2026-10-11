#!/usr/bin/env bash
# Prints the SHA-384 integrity value for every vendored script (D7, T17). index.html must carry these exact values;
# tests/test_web_supply_chain.py checks it. Re-run after changing a vendored file on purpose.
set -euo pipefail
cd "$(dirname "$0")/../apps/web/vendor"
for f in *.js; do printf "%s sha384-%s\n" "$f" "$(openssl dgst -sha384 -binary "$f" | openssl base64 -A)"; done
