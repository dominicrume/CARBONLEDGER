-- Merkle anchoring (D15, T22). Written 2026-10-11. One on-chain root per interval; each receipt keeps its proof path.
ALTER TABLE anchor_outbox ADD COLUMN anchor_id text;          -- the batch this receipt was anchored in, e.g. A-000012-000057
ALTER TABLE anchor_outbox ADD COLUMN anchor_root text CHECK (anchor_root IS NULL OR anchor_root ~ '^[0-9a-f]{64}$');
ALTER TABLE anchor_outbox ADD COLUMN proof jsonb;             -- [["L"|"R", hex], ...] from the leaf up to the root
CREATE INDEX anchor_outbox_anchor_id ON anchor_outbox (anchor_id);
-- Once anchored, the root and the proof are part of the record and never change.
CREATE OR REPLACE FUNCTION anchors_only_move_forward() RETURNS trigger AS $$
BEGIN
  IF OLD.status = 'anchored' AND (NEW.status <> 'anchored' OR NEW.signature IS DISTINCT FROM OLD.signature OR NEW.slot IS DISTINCT FROM OLD.slot
       OR NEW.anchor_root IS DISTINCT FROM OLD.anchor_root OR NEW.proof IS DISTINCT FROM OLD.proof) THEN
    RAISE EXCEPTION 'APPEND_ONLY: an anchored receipt cannot be changed';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;
