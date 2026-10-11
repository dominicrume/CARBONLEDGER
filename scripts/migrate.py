#!/usr/bin/env python3
"""Apply db/migrations/*.sql in order to DATABASE_URL_MIGRATOR (or DATABASE_URL), once each, in a transaction each.
Usage: python scripts/migrate.py [--reset]   --reset drops everything first (scratch databases only; it refuses
unless the database name ends with _test or ALLOW_RESET=1)."""
import os
import sys
from pathlib import Path

MIGRATIONS = sorted((Path(__file__).resolve().parents[1] / "db" / "migrations").glob("*.sql"))


def migrate(url: str, reset: bool = False) -> list:
    import psycopg
    applied = []
    with psycopg.connect(url, autocommit=True) as conn:
        dbname = conn.info.dbname
        if reset:
            if not (dbname.endswith("_test") or os.environ.get("ALLOW_RESET") == "1"):
                raise SystemExit(f"refusing to reset {dbname}: not a _test database and ALLOW_RESET is not 1")
            conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())")
        done = {r[0] for r in conn.execute("SELECT name FROM schema_migrations")}
        for path in MIGRATIONS:
            if path.name in done:
                continue
            with conn.transaction():
                conn.execute(path.read_text(encoding="utf-8"))
                conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
            applied.append(path.name)
    return applied


if __name__ == "__main__":
    url = os.environ.get("DATABASE_URL_MIGRATOR") or os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("set DATABASE_URL_MIGRATOR or DATABASE_URL")
    names = migrate(url, reset="--reset" in sys.argv)
    print("applied:", names or "nothing new")
