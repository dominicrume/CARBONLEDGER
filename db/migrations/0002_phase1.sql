-- Phase 1 persistence (D4, D9). Written 2026-10-11. Applied by scripts/migrate.py, tested by tests/test_db_migrations.py.

-- Receipts carry their public id and anchor state. History stays append-only (trigger from 0001).
ALTER TABLE receipts ADD COLUMN receipt_id text GENERATED ALWAYS AS (receipt->>'receipt_id') STORED;
CREATE UNIQUE INDEX receipts_receipt_id ON receipts (receipt_id);
CREATE INDEX receipts_owner ON receipts ((receipt->>'owner'));

-- The anchor outbox: one row per receipt, updated by the worker as it moves pending -> anchored | failed.
CREATE TABLE anchor_outbox (
  receipt_id   text PRIMARY KEY REFERENCES receipts(receipt_id),
  receipt_hash text NOT NULL,
  status       text NOT NULL CHECK (status IN ('pending','anchored','failed')),
  signature    text,
  explorer_url text,
  cluster      text,
  slot         bigint,
  attempts     int NOT NULL DEFAULT 0,
  last_error   text NOT NULL DEFAULT '',
  anchored_at  timestamptz,
  updated_at   timestamptz NOT NULL DEFAULT now()
);
-- An anchored row never goes back to pending or failed, and its signature never changes.
CREATE FUNCTION anchors_only_move_forward() RETURNS trigger AS $$
BEGIN
  IF OLD.status = 'anchored' AND (NEW.status <> 'anchored' OR NEW.signature IS DISTINCT FROM OLD.signature OR NEW.slot IS DISTINCT FROM OLD.slot) THEN
    RAISE EXCEPTION 'APPEND_ONLY: an anchored receipt cannot be changed';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER anchor_outbox_forward BEFORE UPDATE ON anchor_outbox FOR EACH ROW EXECUTE FUNCTION anchors_only_move_forward();
CREATE TRIGGER anchor_outbox_no_delete BEFORE DELETE ON anchor_outbox FOR EACH ROW EXECUTE FUNCTION forbid_change();

-- Idempotency: the key maps to the receipt it produced, bound to the request digest.
ALTER TABLE idempotency DROP COLUMN response;
ALTER TABLE idempotency ADD COLUMN receipt_id text NOT NULL REFERENCES receipts(receipt_id);
CREATE TRIGGER idempotency_append_only BEFORE UPDATE OR DELETE ON idempotency FOR EACH ROW EXECUTE FUNCTION forbid_change();

-- Retirements carry the public receipt id too.
ALTER TABLE retirements ADD COLUMN receipt_id text UNIQUE REFERENCES receipts(receipt_id);

-- API keys: only the salted hash is stored (packages/core/carbonledger/auth.py).
CREATE TABLE api_keys (
  key_id     text PRIMARY KEY,
  role       text NOT NULL CHECK (role IN ('personal','business','agent','verifier','authority')),
  owner      text NOT NULL CHECK (length(owner) BETWEEN 1 AND 64),
  key_hash   text NOT NULL UNIQUE CHECK (key_hash ~ '^[0-9a-f]{64}$'),
  revoked    boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Mandates name an agent by public key (KYA). The owner is the key owner who wrote it.
ALTER TABLE mandates RENAME COLUMN agent TO agent_pubkey;
ALTER TABLE mandates ADD CONSTRAINT mandates_agent_is_a_key CHECK (length(agent_pubkey) BETWEEN 32 AND 44);
ALTER TABLE mandates ADD COLUMN created_at timestamptz NOT NULL DEFAULT now();

-- Evidence records, the shape in docs/MRV-LAYERS.md. Raw files stay off this database and off any chain.
CREATE TABLE evidence (
  evidence_id       text PRIMARY KEY,
  project_id        text NOT NULL REFERENCES projects(id),
  kind              text NOT NULL CHECK (kind IN ('gps_photo','satellite','field_audit','document')),
  captured_at       timestamptz NOT NULL,
  coarse_location   text CHECK (coarse_location IS NULL OR length(coarse_location) <= 5),
  content_hash      text NOT NULL UNIQUE CHECK (content_hash ~ '^[0-9a-f]{64}$'),
  submitted_by      text NOT NULL,
  verifier_decision text NOT NULL DEFAULT 'pending' CHECK (verifier_decision IN ('pending','accepted','rejected')),
  decision_reason   text,
  verifier          text,
  decided_at        timestamptz,
  CHECK ((verifier_decision = 'pending') = (verifier IS NULL))
);
-- A decision is made once by a named verifier and never silently changed: only pending rows may be updated.
CREATE FUNCTION evidence_decided_once() RETURNS trigger AS $$
BEGIN
  IF OLD.verifier_decision <> 'pending' THEN RAISE EXCEPTION 'APPEND_ONLY: evidence % was already decided', OLD.evidence_id; END IF;
  IF NEW.content_hash <> OLD.content_hash OR NEW.project_id <> OLD.project_id THEN RAISE EXCEPTION 'APPEND_ONLY: evidence content cannot change'; END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER evidence_decided_once BEFORE UPDATE ON evidence FOR EACH ROW EXECUTE FUNCTION evidence_decided_once();
CREATE TRIGGER evidence_no_delete BEFORE DELETE ON evidence FOR EACH ROW EXECUTE FUNCTION forbid_change();

-- Which migrations ran.
CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
