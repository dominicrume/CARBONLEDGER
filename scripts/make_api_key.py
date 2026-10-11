#!/usr/bin/env python3
"""Make an API key. Prints the plaintext ONCE and the line to add to API_KEYS in .env (role:owner:hash).
Usage: API_KEY_PEPPER=... python scripts/make_api_key.py <role> <owner>
The pepper comes from the environment, never from an argument, so it never lands in shell history."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core"))
from carbonledger.auth import ROLES, ApiKeyStore  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ROLES:
        print(f"usage: API_KEY_PEPPER=<pepper> {sys.argv[0]} <{'|'.join(ROLES)}> <owner id>")
        sys.exit(2)
    pepper = os.environ.get("API_KEY_PEPPER", "")
    store = ApiKeyStore(pepper)
    key, rec = store.issue(sys.argv[1], sys.argv[2])
    print("Give this key to the caller once. It is not stored anywhere:")
    print(f"  {key}")
    url = os.environ.get("DATABASE_URL")
    if url:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from carbonledger_api.store import PostgresStore  # noqa: E402
        PostgresStore(url).insert_api_key(rec)
        print(f"Stored the hash in the database as {rec.key_id} ({rec.role}, owner {rec.owner}).")
    else:
        print("Add this to API_KEYS in .env (comma separated, role:owner:hash):")
        print(f"  {rec.role}:{rec.owner}:{rec.key_hash}")
