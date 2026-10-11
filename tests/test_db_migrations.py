"""The database enforces the registry rules a second time (D4). Needs a scratch Postgres: set DATABASE_URL_TEST
(a database whose name ends with _test). Skipped otherwise, and CI provides one. Runs scripts/migrate.py --reset first."""
import os
import sys
from pathlib import Path

import pytest

URL = os.environ.get("DATABASE_URL_TEST", "")
pytestmark = pytest.mark.skipif(not URL, reason="DATABASE_URL_TEST not set")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.fixture(scope="module")
def db():
    import psycopg
    from migrate import migrate
    migrate(URL, reset=True)
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("INSERT INTO projects (id, country_iso3, methodology, status, attested_g) VALUES ('p1','GBR','x','attested',1000)")
        conn.execute("INSERT INTO batches (id, project_id, vintage, issued_g) VALUES ('b1','p1',2026,600)")
        yield conn


def _fails(conn, sql, params=(), match=""):
    import psycopg
    with pytest.raises(psycopg.Error) as e:
        with conn.transaction():
            conn.execute(sql, params)
    assert match in str(e.value), str(e.value)


def test_every_migration_applied_once(db):
    names = [r[0] for r in db.execute("SELECT name FROM schema_migrations ORDER BY name")]
    assert names == ["0001_registry.sql", "0002_phase1.sql"]
    from migrate import migrate
    assert migrate(URL) == []


def test_overlapping_serial_ranges_are_refused_by_the_exclusion_constraint(db):
    db.execute("INSERT INTO receipts (idx, receipt, prev_hash, hash) VALUES (0, '{\"receipt_id\":\"CL-A\"}', '0', 'h0')")
    db.execute("INSERT INTO retirements (batch_id, retiree, grams, serial_start, serial_end, memo_hash, receipt_id) VALUES ('b1','a',100,0,100,'m','CL-A')")
    _fails(db, "INSERT INTO retirements (batch_id, retiree, grams, serial_start, serial_end, memo_hash) VALUES ('b1','b',50,50,100,'m')", match="exclusion")
    _fails(db, "INSERT INTO retirements (batch_id, retiree, grams, serial_start, serial_end, memo_hash) VALUES ('b1','b',50,0,51,'m')", match="retirements_check")
    db.execute("INSERT INTO retirements (batch_id, retiree, grams, serial_start, serial_end, memo_hash) VALUES ('b1','b',50,100,150,'m')")
    assert db.execute("SELECT count(*) FROM retirements").fetchone()[0] == 2


def test_history_cannot_be_edited_or_deleted(db):
    _fails(db, "UPDATE receipts SET receipt = '{\"receipt_id\":\"CL-A\",\"grams\":1}' WHERE idx = 0", match="APPEND_ONLY")
    _fails(db, "DELETE FROM receipts WHERE idx = 0", match="APPEND_ONLY")
    _fails(db, "DELETE FROM retirements WHERE serial_start = 0", match="APPEND_ONLY")
    _fails(db, "UPDATE retirements SET grams = 1 WHERE serial_start = 0", match="APPEND_ONLY")


def test_issuance_cannot_exceed_attestation_across_batches(db):
    _fails(db, "INSERT INTO batches (id, project_id, vintage, issued_g) VALUES ('b2','p1',2026,401)", match="OVER_ISSUANCE")
    db.execute("INSERT INTO batches (id, project_id, vintage, issued_g) VALUES ('b2','p1',2026,400)")
    _fails(db, "UPDATE projects SET issued_g = 1001 WHERE id = 'p1'", match="projects_check")


def test_an_anchored_receipt_never_moves_backwards(db):
    db.execute("INSERT INTO anchor_outbox (receipt_id, receipt_hash, status) VALUES ('CL-A','h0','pending')")
    db.execute("UPDATE anchor_outbox SET status='anchored', signature='sig', slot=5 WHERE receipt_id='CL-A'")
    _fails(db, "UPDATE anchor_outbox SET status='pending' WHERE receipt_id='CL-A'", match="APPEND_ONLY")
    _fails(db, "UPDATE anchor_outbox SET signature='other' WHERE receipt_id='CL-A'", match="APPEND_ONLY")
    _fails(db, "DELETE FROM anchor_outbox WHERE receipt_id='CL-A'", match="APPEND_ONLY")


def test_idempotency_rows_and_api_keys_hold_their_shape(db):
    db.execute("INSERT INTO idempotency (key, payload_digest, receipt_id) VALUES ('k1','d','CL-A')")
    _fails(db, "UPDATE idempotency SET receipt_id = 'CL-A' WHERE key = 'k1'", match="APPEND_ONLY")
    _fails(db, "INSERT INTO idempotency (key, payload_digest, receipt_id) VALUES ('k2','d','CL-NOPE')", match="foreign key")
    db.execute("INSERT INTO api_keys (key_id, role, owner, key_hash) VALUES ('key-1','personal','p1', repeat('a', 64))")
    _fails(db, "INSERT INTO api_keys (key_id, role, owner, key_hash) VALUES ('key-2','admin','p1', repeat('b', 64))", match="api_keys_role_check")
    _fails(db, "INSERT INTO api_keys (key_id, role, owner, key_hash) VALUES ('key-3','personal','p1', 'plaintext-key')", match="api_keys_key_hash_check")


def test_evidence_is_decided_once_by_a_named_verifier(db):
    db.execute("INSERT INTO evidence (evidence_id, project_id, kind, captured_at, coarse_location, content_hash, submitted_by) VALUES ('e1','p1','gps_photo',now(),'gcpvj', repeat('c', 64),'farmer-1')")
    _fails(db, "INSERT INTO evidence (evidence_id, project_id, kind, captured_at, content_hash, submitted_by) VALUES ('e2','p1','gps_photo',now(), repeat('c', 64),'farmer-2')", match="evidence_content_hash_key")
    _fails(db, "INSERT INTO evidence (evidence_id, project_id, kind, captured_at, coarse_location, content_hash, submitted_by) VALUES ('e3','p1','gps_photo',now(),'gcpvj2k', repeat('d', 64),'f')", match="evidence_coarse_location_check")
    _fails(db, "UPDATE evidence SET verifier_decision='accepted' WHERE evidence_id='e1'", match="evidence_check")       # a decision needs a named verifier
    db.execute("UPDATE evidence SET verifier_decision='accepted', verifier='Dr Example', decided_at=now() WHERE evidence_id='e1'")
    _fails(db, "UPDATE evidence SET verifier_decision='rejected' WHERE evidence_id='e1'", match="already decided")
    _fails(db, "DELETE FROM evidence WHERE evidence_id='e1'", match="APPEND_ONLY")
