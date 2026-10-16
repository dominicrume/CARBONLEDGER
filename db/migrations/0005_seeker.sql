-- Sign in with Seeker (2026-10-16). An account may be an email, a Solana wallet, or both. A verified Seeker Genesis
-- Token (a non-transferable Token-2022 NFT, one per Seeker phone) marks the account as a Seeker; each token mint can
-- belong to one account only, so one phone earns the Seeker perk once. Nothing here is ledger history.
ALTER TABLE accounts ALTER COLUMN email DROP NOT NULL;
ALTER TABLE accounts ADD COLUMN wallet text UNIQUE CHECK (wallet IS NULL OR wallet ~ '^[1-9A-HJ-NP-Za-km-z]{32,44}$');
ALTER TABLE accounts ADD COLUMN sgt_mint text UNIQUE CHECK (sgt_mint IS NULL OR sgt_mint ~ '^[1-9A-HJ-NP-Za-km-z]{32,44}$');
ALTER TABLE accounts ADD COLUMN seeker_verified_at timestamptz;
ALTER TABLE accounts ADD CONSTRAINT accounts_email_or_wallet CHECK (email IS NOT NULL OR wallet IS NOT NULL);
