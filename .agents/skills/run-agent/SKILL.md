---
name: run-agent
description: Set up, use, debug or explain AI agents that retire CarbonLedger units for a business under a mandate (cap, allow-list, expiry, revoke) with ed25519 signed, time-boxed requests. Use for mandate design, agent key handling, refusal codes like OVER_CAP or EXPIRED, and the KYA (Know Your Agent) story.
---

# Run an agent under a mandate

An agent retires only under a mandate. Every agent action, accepted or refused, becomes a sealed receipt.

## Load
- `workspaces/agent/CLAUDE.md` and the stage in hand (01-mandate, 02-act, 03-revoke).
- `packages/core/carbonledger/mandate.py`, `packages/core/carbonledger/agentsig.py`, `conformance/mandate_vectors.json`.

## Facts to hold
- A mandate names the owner, the agent's public key, a cap in grams, an expiry and an optional project allow-list.
  Cap and expiry are required. Only the owner revokes.
- Each request is signed over a canonical message with a timestamp window. The signature is checked before the
  mandate.
- Refusal codes: OVER_CAP, EXPIRED, REVOKED, WRONG_AGENT, PROJECT_NOT_ALLOWED. A refusal leaves state unchanged.

## Gates
- `python -m pytest -q tests/test_registry_mandate.py tests/test_api.py`
- `scripts/e2e.sh` covers the business mandate set and revoke flow.

## Policy
- AUTO: generate a test key on a dry-run server, explain a refusal, add a vector.
- ASK: create or revoke a mandate on the live server.
- NEVER: hold or print a business's private agent key; widen a mandate; act after expiry or revoke.

## Report
One run record.
