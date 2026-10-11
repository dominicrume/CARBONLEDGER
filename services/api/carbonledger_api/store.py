"""Persistence (D9). MemoryStore keeps nothing: state lives in the process (tests, dry runs). PostgresStore writes
through: every committed change goes to the database in one transaction BEFORE the in-memory state changes, so a
constraint in db/migrations is a second guard, and a restart rebuilds the same state from the rows.
The receipt chain is verified at load. A broken chain stops the server from starting: it never serves bad history."""
import json
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional


class StoreError(RuntimeError):
    pass


class MemoryStore:
    kind = "memory"

    def load(self) -> Optional[dict]:
        return None

    def seed(self, projects, batches) -> None:
        pass

    def write_retirement(self, entry: dict, ret, batch, idem_key: str, payload_digest: str) -> None:
        pass

    def update_outbox(self, e) -> None:
        pass

    def upsert_mandate(self, m) -> None:
        pass

    def insert_api_key(self, rec) -> None:
        pass


class PostgresStore:
    kind = "postgres"

    def __init__(self, url: str):
        import psycopg
        self._psycopg, self.url = psycopg, url
        with self._conn() as c:
            c.execute("SELECT 1 FROM schema_migrations WHERE name = '0003_merkle.sql'")
            if c.fetchone() is None:
                raise StoreError("database is not migrated: run python scripts/migrate.py")

    @contextmanager
    def _conn(self):
        with self._psycopg.connect(self.url) as conn:
            with conn.cursor() as cur:
                yield cur
            conn.commit()

    def load(self) -> Optional[dict]:
        with self._conn() as c:
            c.execute("SELECT id, country_iso3, methodology, status, attested_g, issued_g FROM projects ORDER BY id")
            projects = c.fetchall()
            if not projects:
                return None
            c.execute("SELECT id, project_id, vintage, issued_g, retired_g, next_serial FROM batches ORDER BY id")
            batches = c.fetchall()
            c.execute("SELECT receipt_no, batch_id, retiree, grams, serial_start, serial_end, target_iso3, memo_hash FROM retirements ORDER BY receipt_no")
            retirements = c.fetchall()
            c.execute("SELECT idx, receipt, prev_hash, hash FROM receipts ORDER BY idx")
            receipts = [{"index": i, "receipt": r, "prev_hash": p, "hash": h} for i, r, p, h in c.fetchall()]
            c.execute("""SELECT o.receipt_id, o.receipt_hash, o.status, o.signature, o.explorer_url, o.cluster, o.slot, o.attempts, o.last_error,
                                extract(epoch from o.anchored_at), r.idx, o.anchor_id, o.anchor_root, o.proof
                         FROM anchor_outbox o JOIN receipts r ON r.receipt_id = o.receipt_id ORDER BY r.idx""")
            outbox = c.fetchall()
            c.execute("SELECT key, payload_digest, receipt_id FROM idempotency")
            idem = c.fetchall()
            c.execute("SELECT id, owner, agent_pubkey, cap_g, used_g, extract(epoch from expires_at), allow_projects, revoked FROM mandates")
            mandates = c.fetchall()
            c.execute("SELECT key_id, role, owner, key_hash, revoked FROM api_keys")
            keys = c.fetchall()
        return {"projects": projects, "batches": batches, "retirements": retirements, "receipts": receipts, "outbox": outbox,
                "idem": idem, "mandates": mandates, "api_keys": keys}

    def seed(self, projects: Iterable, batches: Iterable) -> None:
        with self._conn() as c:
            for p in projects:
                c.execute("INSERT INTO projects (id, country_iso3, methodology, status, attested_g, issued_g) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                          (p.id, p.country_iso3, p.methodology, p.status, p.attested_g, p.issued_g))
            for b in batches:
                c.execute("INSERT INTO batches (id, project_id, vintage, issued_g, retired_g, next_serial) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                          (b.id, b.project_id, b.vintage, b.issued_g, b.retired_g, b.next_serial))

    def write_retirement(self, entry: dict, ret, batch, idem_key: str, payload_digest: str) -> None:
        """One transaction: receipt, retirement, batch counters, outbox row, idempotency row. Any constraint
        failure raises StoreError and nothing is written."""
        rid = entry["receipt"]["receipt_id"]
        try:
            with self._conn() as c:
                c.execute("INSERT INTO receipts (idx, receipt, prev_hash, hash) VALUES (%s,%s,%s,%s)",
                          (entry["index"], json.dumps(entry["receipt"], sort_keys=True), entry["prev_hash"], entry["hash"]))
                # receipt_no is the database's own sequence; the in-memory number is a local counter and never public
                c.execute("INSERT INTO retirements (batch_id, retiree, grams, serial_start, serial_end, target_iso3, memo_hash, receipt_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                          (ret.batch_id, ret.retiree, ret.grams, ret.serial_start, ret.serial_end, ret.target_iso3, ret.memo_hash, rid))
                c.execute("UPDATE batches SET retired_g = %s, next_serial = %s WHERE id = %s", (batch.retired_g, batch.next_serial, batch.id))
                c.execute("INSERT INTO anchor_outbox (receipt_id, receipt_hash, status) VALUES (%s,%s,'pending')", (rid, entry["hash"]))
                c.execute("INSERT INTO idempotency (key, payload_digest, receipt_id) VALUES (%s,%s,%s)", (idem_key, payload_digest, rid))
        except self._psycopg.Error as exc:
            raise StoreError(f"the database refused the retirement: {str(exc).splitlines()[0]}") from exc

    def update_outbox(self, e) -> None:
        try:
            with self._conn() as c:
                c.execute("""UPDATE anchor_outbox SET status=%s, signature=%s, explorer_url=%s, cluster=%s, slot=%s, attempts=%s, last_error=%s,
                                anchored_at=to_timestamp(%s), anchor_id=%s, anchor_root=%s, proof=%s WHERE receipt_id=%s""",
                          (e.status, e.signature, e.explorer_url, e.cluster, e.slot, e.attempts, e.last_error, e.anchored_at, e.anchor_id, e.anchor_root,
                           json.dumps(e.proof) if e.proof is not None else None, e.receipt_id))
        except self._psycopg.Error as exc:
            raise StoreError(f"the database refused the anchor update: {str(exc).splitlines()[0]}") from exc

    def upsert_mandate(self, m) -> None:
        with self._conn() as c:
            c.execute("""INSERT INTO mandates (id, owner, agent_pubkey, cap_g, used_g, expires_at, allow_projects, revoked)
                         VALUES (%s,%s,%s,%s,%s,to_timestamp(%s),%s,%s)
                         ON CONFLICT (id) DO UPDATE SET used_g = EXCLUDED.used_g, revoked = EXCLUDED.revoked""",
                      (m.id, m.owner, m.agent, m.cap_g, m.used_g, m.expires_at, list(m.allow_projects) if m.allow_projects is not None else None, m.revoked))

    def insert_api_key(self, rec) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO api_keys (key_id, role, owner, key_hash, revoked) VALUES (%s,%s,%s,%s,%s)", (rec.key_id, rec.role, rec.owner, rec.key_hash, rec.revoked))

    def revoke_api_key(self, key_id: str) -> None:
        with self._conn() as c:
            c.execute("UPDATE api_keys SET revoked = true WHERE key_id = %s", (key_id,))


def store_from_env(url: Optional[str]):
    return PostgresStore(url) if url else MemoryStore()
