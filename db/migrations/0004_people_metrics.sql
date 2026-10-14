-- People and metrics (2026-10-14). Nothing here is ledger history: receipts stay append-only and carry only an owner id.
-- Personal data lives in two places only, accounts.email and profiles.display_name, and both are deleted on request.

-- A: privacy-first usage counts. One row per day and event name. No ids, no addresses, no devices.
CREATE TABLE event_counts (
  day   date   NOT NULL,
  name  text   NOT NULL CHECK (name ~ '^[a-z_]{2,32}$'),
  n     bigint NOT NULL DEFAULT 0 CHECK (n >= 0),
  PRIMARY KEY (day, name)
);

-- B: accounts. An account is an email address that signed in once; it owns one or more ledger owners
-- (the anonymous login a person played with first, and the key each signed-in device gets).
CREATE TABLE accounts (
  id          text PRIMARY KEY CHECK (id ~ '^acct-[0-9a-f]{12}$'),
  email       text NOT NULL UNIQUE CHECK (email = lower(email) AND length(email) BETWEEN 3 AND 254),
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE account_owners (
  owner       text PRIMARY KEY CHECK (length(owner) BETWEEN 1 AND 64),
  account_id  text NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  linked_at   timestamptz NOT NULL DEFAULT now()
);
-- One-time sign-in links. Only the hash of the token is kept; the link expires and is used once.
CREATE TABLE login_links (
  token_hash  text PRIMARY KEY CHECK (token_hash ~ '^[0-9a-f]{64}$'),
  email       text NOT NULL,
  expires_at  timestamptz NOT NULL,
  used        boolean NOT NULL DEFAULT false
);
-- Profiles, keyed by ledger owner (an account's main owner, or an anonymous login that chose a name).
CREATE TABLE profiles (
  owner          text PRIMARY KEY CHECK (length(owner) BETWEEN 1 AND 64),
  display_name   text CHECK (display_name IS NULL OR length(display_name) BETWEEN 1 AND 24),
  business_name  text CHECK (business_name IS NULL OR length(business_name) BETWEEN 1 AND 80),
  employees      integer CHECK (employees IS NULL OR employees BETWEEN 1 AND 10000000),
  updated_at     timestamptz NOT NULL DEFAULT now()
);
-- Least privilege, for the operator to run once (the app role may change and delete these, never the ledger):
-- GRANT SELECT, INSERT, UPDATE, DELETE ON event_counts, accounts, account_owners, login_links, profiles TO carbonledger_app;
