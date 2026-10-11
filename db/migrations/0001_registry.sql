-- STATUS: written but NOT executed in the sandbox that produced it (no Postgres there). Run it on a scratch database
-- and add a migration test before relying on it.
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE projects (
  id           text PRIMARY KEY,
  country_iso3 char(3) NOT NULL,
  methodology  text NOT NULL,
  status       text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed','attested','suspended')),
  attested_g   bigint NOT NULL DEFAULT 0 CHECK (attested_g >= 0),
  issued_g     bigint NOT NULL DEFAULT 0 CHECK (issued_g >= 0),
  CHECK (issued_g <= attested_g)
);

CREATE TABLE batches (
  id          text PRIMARY KEY,
  project_id  text NOT NULL REFERENCES projects(id),
  vintage     int  NOT NULL CHECK (vintage BETWEEN 1990 AND 2100),
  issued_g    bigint NOT NULL CHECK (issued_g > 0),
  retired_g   bigint NOT NULL DEFAULT 0,
  next_serial bigint NOT NULL DEFAULT 0,
  CHECK (retired_g <= issued_g),
  CHECK (next_serial = retired_g)
);

-- One external credit can be linked once, ever. This is the anti double-counting rule at database level.
CREATE TABLE linked_credits (
  registry_name text NOT NULL,
  serial        text NOT NULL,
  batch_id      text NOT NULL REFERENCES batches(id),
  PRIMARY KEY (registry_name, serial)
);

-- Serial ranges inside a batch can never overlap: a gram is retired once.
CREATE TABLE retirements (
  receipt_no   bigserial PRIMARY KEY,
  batch_id     text   NOT NULL REFERENCES batches(id),
  retiree      text   NOT NULL,
  grams        bigint NOT NULL CHECK (grams > 0),
  serial_start bigint NOT NULL CHECK (serial_start >= 0),
  serial_end   bigint NOT NULL,
  target_iso3  char(3),
  memo_hash    text NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  CHECK (serial_end - serial_start = grams),
  EXCLUDE USING gist (batch_id WITH =, int8range(serial_start, serial_end) WITH &&)
);

CREATE TABLE receipts (
  idx        int PRIMARY KEY,
  receipt    jsonb NOT NULL,
  prev_hash  text NOT NULL UNIQUE,
  hash       text NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE chain_records (
  receipt_id text PRIMARY KEY,
  signature  text NOT NULL,
  cluster    text NOT NULL
);

CREATE TABLE idempotency (
  key            text PRIMARY KEY,
  payload_digest text NOT NULL,
  response       jsonb NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE mandates (
  id             text PRIMARY KEY,
  owner          text NOT NULL,
  agent          text NOT NULL,
  cap_g          bigint NOT NULL CHECK (cap_g > 0),
  used_g         bigint NOT NULL DEFAULT 0,
  expires_at     timestamptz NOT NULL,
  allow_projects text[],
  revoked        boolean NOT NULL DEFAULT false,
  CHECK (used_g <= cap_g)
);

-- Issuance cap across all batches of a project.
CREATE FUNCTION enforce_issuance_cap() RETURNS trigger AS $$
BEGIN
  IF (SELECT COALESCE(SUM(issued_g),0) FROM batches WHERE project_id = NEW.project_id AND id <> NEW.id) + NEW.issued_g
     > (SELECT attested_g FROM projects WHERE id = NEW.project_id) THEN
    RAISE EXCEPTION 'OVER_ISSUANCE';
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER batches_issuance_cap BEFORE INSERT ON batches FOR EACH ROW EXECUTE FUNCTION enforce_issuance_cap();

-- History cannot be rewritten, even by the application role.
CREATE FUNCTION forbid_change() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'APPEND_ONLY: % on % is not allowed', TG_OP, TG_TABLE_NAME; END $$ LANGUAGE plpgsql;
CREATE TRIGGER receipts_append_only BEFORE UPDATE OR DELETE ON receipts FOR EACH ROW EXECUTE FUNCTION forbid_change();
CREATE TRIGGER retirements_append_only BEFORE UPDATE OR DELETE ON retirements FOR EACH ROW EXECUTE FUNCTION forbid_change();
CREATE TRIGGER chain_records_append_only BEFORE UPDATE OR DELETE ON chain_records FOR EACH ROW EXECUTE FUNCTION forbid_change();

-- Least privilege: the app role can insert and read history, never edit it.
-- CREATE ROLE carbonledger_app LOGIN PASSWORD '<from the secret store>';
-- GRANT SELECT, INSERT ON receipts, retirements, chain_records, linked_credits, idempotency TO carbonledger_app;
-- GRANT SELECT, INSERT, UPDATE ON batches, projects, mandates TO carbonledger_app;
