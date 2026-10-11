# Environment: What Each Value Is, Where It Comes From, Who Holds It

The full template is .env.example. This page says how to obtain each value and what must never happen to it.
There is one .env for the server. The web app has no .env and no .env.local: its settings are in
apps/web/js/config.js (ENGINEERING rule 14). CI reads GitHub Actions secrets.

## Tools to install once (human, on your own machine)
| Tool | Why | Install |
|---|---|---|
| Python 3.12 or newer | API and core | python.org or `brew install python@3.12` |
| Node 22 | web checks, Playwright, estimator export | `brew install node@22` |
| Docker Desktop | Postgres for D4 and D9 | docker.com |
| Solana CLI | keys, airdrop, deploy | `sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"` |
| Rust and Anchor | the program (D3) | `curl https://sh.rustup.rs -sSf \| sh`, then `cargo install --git https://github.com/coral-xyz/anchor avm --force && avm install latest && avm use latest` |
| base58 (Python) | print the devnet secret once | `pip install base58` |

## Values by stage
| Variable | Stage | How to get it | Holder |
|---|---|---|---|
| APP_ENV, CHAIN_MODE, WEB_ORIGIN, API_PORT | 0 | type it | anyone |
| SOLANA_SECRET_KEY_B58 | 0b | `solana-keygen new` then the base58 one-liner in .env.example | Rume, laptop secret store, tiny balance |
| SOLANA_RPC_URL_FALLBACK | 0b | free tier at Helius, QuickNode or Triton, devnet endpoint | Rume |
| API_KEY_PEPPER | 1 | `openssl rand -hex 32` | server secret store |
| REGISTRY_AUTHORITY_PUBKEY | 1 | public key of a Squads multisig or hardware wallet | the trust, never a laptop |
| VERIFIER_PUBKEYS | 1 | each verifier makes their own key and sends the public half | each verifier |
| POSTGRES_PASSWORD, DATABASE_URL | 1b | `openssl rand -hex 24`, docker compose locally, Supabase or Neon hosted | server secret store |
| CARBON_REGISTRY_PROGRAM_ID | 1c | `anchor keys list` after the first build | public, goes in three places |
| OPEN_FOOD_FACTS_USER_AGENT | any | type it, include a contact | anyone |
| ANTHROPIC_API_KEY | later | console.anthropic.com | server secret store, only if category suggestion ships |

## Never
- A secret in the repo, a chat, a model prompt, a log line or a screenshot.
- The memo hot key used as authority or verifier.
- An authority or verifier private key on a laptop.
- CHAIN_MODE pointing at mainnet before an independent review and a multisig (SCALING stage 1 gate).

## Rotation
Rotate the hot key on any doubt (T13). Rotating API_KEY_PEPPER invalidates every API key, so plan it.
Verifier keys rotate through the program's rotate_verifier instruction once Block 5 lands.
