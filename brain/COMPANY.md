# The Company

Checked against the code on 2026-11-09. Where a document and the code disagree, the code wins and the gap is
listed in TRUTH.md.

## Three lines of work, one owner
| Line | What it is | Stage | Where |
|---|---|---|---|
| CarbonLedger | One register for carbon units: people and businesses retire pilot units for what they buy, travel and use, and anyone can verify every receipt on Solana | Phase 1 demo, live on Railway and Solana devnet, no payments | carbonledger.world (site), /app (PWA), Solana dApp Store listing for Seeker |
| VOREM | A video and motion studio with a fixed method (the VOREM style) and a script director on the Claude API | Method proven on client work; Studio live behind an access code | studio.carbonledger.world, `services/api/carbonledger_api/studio.py`, the owner's vorem-video skill |
| Research | "AI Code Quality Auditor", an MSc study of AI coding agents, also shipped as a GitHub Action | Complete; the Action runs in this repo's CI | `.github/workflows/ci.yml` (job `audit`), `spec.yaml` |

The directly responsible individual for all three is the owner, Rume Dominic (Orume Dominic Uririe), until he names
others (DEBT.md header). CarbonLedger has a partner whose views appear in CONTEXT.md; decisions marked "awaiting
Rume and the partner" are proposals, not ratified (docs/DECISIONS.md).

## CarbonLedger in one breath
A gamified app on top of a strict register. The game (XP, levels, leagues, countries cleared on the World clock) is
the front door. The register (integer grams, serial ranges, a hash-chained receipt for every acceptance and every
refusal, Merkle roots anchored on Solana devnet) is the product. The wedge is not "the only registry": about 26
registries exist. The wedge is a retirement and receipt layer anyone can check, plus an anti double count rule
(ARCHITECTURE.md, docs/PITCH-FACTS.md).

## Who acts, and what they may decide
| Actor | How it proves itself | May | May never |
|---|---|---|---|
| Person (personal) | API key, email magic link, or Sign in with Solana on a Seeker | Retire for themselves, see own history, delete own data | Set a price or a footprint; the server prices |
| Business | Business key | Retire for the business, set and revoke agent mandates, export a statement | Exceed a mandate it gave |
| Agent | ed25519 key, every request signed and time-boxed | Retire within a mandate: cap, allow-list, expiry | Act without a mandate, or after revoke |
| Verifier | A named person or institution | Attest a project and its amount | Be replaced by software |
| Authority (trustee) | Authority key | Register projects, issue up to the attested amount, suspend | Issue beyond attestation |
| Browser | Nothing; it holds a login, never a signing key | Show and ask | Decide anything |
| Estimator | Code with cited factor tables | Return grams with a tier and source | Take a number from a model |

Sources: `packages/core/carbonledger/auth.py`, `mandate.py`, `agentsig.py`, `registry.py`, CLAUDE.md.

## The unit and its life
- 1 CLT = 1 tonne CO2e = 1,000,000 grams. Grams are integers; money is Decimal (`packages/core/carbonledger/units.py`).
- Life: estimate (tiers 1 to 4, rounded up) -> register project -> verifier attests -> authority issues a batch
  (never above attested) -> retire (a fresh serial range, the server recomputes the grams) -> receipt sealed into the
  chain -> anchored in a Merkle root by Solana memo -> verifiable by id, proof or full audit.
- Today one demo project (`demo-pilot-1`, methodology `SIMULATED-PILOT`) has 1,000 t issued against a simulated
  attestation (`services/api/carbonledger_api/state.py`). That is why every unit is "pilot units, not yet verified
  credits".
- Demo price in the app config: GBP 100 a tonne (`apps/web/js/config.js`). No payment is taken.

## What blocks the "real" version (owner and partner decisions, CONTEXT.md)
1. What backs a CLT: the trust's own projects under an accredited methodology, or retired registry credits (Verra
   needs written consent for tokens, COMPLIANCE C1, C2).
2. Who verifies, with what evidence (a farmer app with GPS photos plus satellite is offered verbally only).
3. The land trust structure, the real price, the open source licence versus patent application GB2611754.9.
4. Login and key custody for any public production URL; multisig for authority and verifier keys (DEBT D6, BREAK F5).
5. Ownership of the baseline app in the founders' agreement (docs/PROVENANCE.md).

## VOREM in one breath
Films where motion follows the words and the presenter speaks in their own voice. Every frame is code (`render(t)`),
every voice take is checked by speech to text and scored for likeness, every layout is audited every 0.1 s, every
master is -14 LUFS. A cloned voice is always labelled. The method lives in the owner's `vorem-video` skill; the
brand and selling rules live in `media/brand/`.

## Audiences and channels
- CarbonLedger: consumers (game, receipts), businesses (statement, mandates), Solana and hackathon judges, partners.
- Rume Dominic brand: builders, founders and enterprise tech leads on LinkedIn, X, YouTube, Reels and Shorts.
- Channel rules (length, close, where the link goes) are in `media/brand/BRAND-VOICE.md`.
