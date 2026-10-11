# CarbonLedger

A register for carbon units with a consumer and business app in front, a server that decides and records, and a
Solana ledger underneath. Each tonne of CO2e is one unit, each unit can be retired once, and every retirement
leaves a receipt that anyone can verify.

**Units are simulated pilot units until a named verifier attests a real project.** Nothing here is an offset, a
carbon-neutral claim or a verified credit. The API says so in every response and every screen says so.

## What it does
- Scan a basket, count a journey, add up a day, run a business footprint, retire pilot units, get a receipt.
- The server prices every retirement itself, from typed items and cited factor tables, and refuses a lower total.
- A gram is retired once: every retirement takes a fresh serial range. Nothing is issued unless a verifier attested
  the project, and issued never exceeds attested. An external credit can be linked once, ever.
- Receipts are KYA receipts (knowyouragenticai-receipts): every decided attempt is sealed to the one before it,
  refusals included with the rule that stopped them. One Merkle root per interval goes on Solana (devnet) as a
  memo; each receipt keeps a proof path, and the verify screen recomputes it in the browser. Export the chain at
  `/v1/audit/receipts.json` and check it with `python -m knowyouragenticai_receipts verify`.
- An AI agent may retire for a business only under a mandate: cap, allow-list, expiry, revoke. The agent is an
  ed25519 key and signs every request.
- Every write needs an API key. Reads stay public, so anyone can verify a receipt.

## Run it
```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
scripts/check.sh                     # tests, gates, web checks, exported data (needs node 22, npm ci in apps/web for the browser test)
scripts/dev.sh                       # API on 8000 (dry-run chain), app on 8080
```
Open http://127.0.0.1:8080/?ledger=solana-devnet and put an API key in Settings. In dev with no keys configured
the API prints one demo key at start. To talk to Solana devnet, follow docs/ENVIRONMENT.md and .env.example.

Other scripts: `scripts/e2e.sh` (browser tests), `scripts/drills.py` (break drills), `scripts/migrate.py`
(Postgres), `scripts/recheck.py` (nightly invariants), `scripts/make_api_key.py`.

## Verify a receipt
On the Verify tab, paste a receipt id. Or:
```
curl http://127.0.0.1:8000/v1/receipts/<id>         # the receipt entry and its anchor state
curl http://127.0.0.1:8000/v1/receipts/<id>/proof   # the Merkle path to the anchored root
curl http://127.0.0.1:8000/v1/audit/verify          # the whole chain: intact or the first bad index
```

## Architecture
```
 Browser app (apps/web)            shows and asks. No signing key. An API key is a login.
        |  HTTPS (loopback in dev)
        v
 API (services/api)                validates, prices, decides, records. Holds the signing key.
   |- estimator, activities        cited factor tables, golden vectors from the app's own code
   |- registry, mandate, agentsig  the rules: serial ranges, attested before issued, link once, signed mandates
   |- receipts, merkle, outbox     hash chain, one root per interval, a proof per receipt, confirm before claiming
   |- auth, store                  hashed API keys, rate limits; Postgres write-through with a second guard
        |
        v
 Solana devnet                     memo: carbonledger:v2:<anchor id>:<root>. Nothing personal, ever.
 Anchor program (later)            same rules on-chain; written, not compiled (programs/carbon_registry)
 Postgres                          db/migrations: exclusion on serial ranges, append-only history, issuance cap
```

## Honest limits
Read DEBT.md and ROOTS-SCORE.md. In short: no real verification exists (attestation is simulated), the Anchor
program is not compiled, the first devnet transaction has not been sent, CI has not run on a runner, there is no
TLS in front of the API, and the authority and verifier keys are not in a multisig. The design is for one pilot,
not for volume. The pitch facts you may state are in docs/PITCH-FACTS.md.

## Third-party code and data
Baseline app: imported, ownership to be recorded (docs/PROVENANCE.md). Vendored: ZXing 0.21.3 (MIT), D3 7.9.0
(ISC), topojson-client 3.1.0 (ISC). Python: FastAPI, pydantic, uvicorn, httpx, solders, psycopg (pinned in
requirements.txt). Dev: Playwright, axe-core. Data: Poore and Nemecek (2018) via Our World in Data (CC BY),
Agribalyse (Etalab open licence) via Open Food Facts (ODbL), UK Government GHG conversion factors (DESNZ),
Global Carbon Project via Our World in Data (CC BY), Natural Earth (public domain). Licence checks: COMPLIANCE C12
and C13 are open.

## Rules and reading order
CLAUDE.md, rules/, BREAK.md, docs/THREAT-MODEL.md, docs/DECISION-CHAIN.md, docs/MERKLE-ANCHORING.md.
