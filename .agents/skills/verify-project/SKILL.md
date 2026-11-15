---
name: verify-project
description: Anything about evidence, MRV, verifiers, attestation or turning pilot units into real credits for CarbonLedger. Use to prepare evidence records, explain the evidence model, draft questions for a verifier, or plan the intake build. An agent never attests; this skill keeps that line.
---

# Verify a project

A verifier (a person or an institution) attests projects. Software never does. Today there is no evidence intake,
no endpoint and no review screen (DEBT D11). This job is human work with agent support.

## Load
- `workspaces/verification/CLAUDE.md`, `docs/MRV-LAYERS.md`, `rules/COMPLIANCE.md` (C1, C2, C7, C8).
- The `evidence` table in `db/migrations/0002_phase1.sql`: kind (gps_photo, satellite, field_audit, document),
  a content hash, a coarse geohash of at most 5 characters, a decision taken once by a named verifier.

## What an agent may do
- AUTO: explain the model; draft an evidence checklist or verifier questions; design the intake build as a brief.
- ASK: anything sent to a partner, a farmer or a verifier; any build of intake code (it needs a decision entry).
- NEVER: attest, mark evidence accepted, issue units, or call units verified. Never store precise locations or
  people's photos in the repo (UK GDPR, COMPLIANCE C8).

## Open questions that block this job (owner and partner)
What backs a CLT; who verifies; Verra consent for tokens; the land trust. See `brain/COMPANY.md`.

## Report
One run record. Any request to "just verify" or "just issue" is a `refused` record with the reason.
