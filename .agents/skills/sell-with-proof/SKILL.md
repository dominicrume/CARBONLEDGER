---
name: sell-with-proof
description: Write or review anything that sells for Rume Dominic, VOREM or CarbonLedger (LinkedIn or X post, caption, video script line, pitch line, landing copy, reply) under the house selling rules and the truth register, and pass the deterministic checker before showing it. Use for any marketing, sales or social copy.
---

# Sell with proof

Hard rule since 2026-10-28: every sale follows `media/brand/SELLING-RULES.md` and passes the checker.

## Load
`media/brand/SELLING-RULES.md`, `media/brand/BRAND-VOICE.md`, `brain/TRUTH.md`. For images: `media/brand/POST-STYLE.md`.

## The ten rules, short
One idea. A hook of 12 words or fewer that stands alone. Lines of 20 words or fewer. Reading grade 8 or lower.
A real number from Rume's own work. Lists of three (five at most). Show the swap ("It isn't X, it is Y").
End on a punch or a question, never a link (the link goes in the first comment). Simple image in brand colours.
Honesty beats simplicity.

## Steps
1. Find the one real number. If none is sourced, ask the owner. Never invent, borrow or round up a result.
2. Draft. Check every claim against `brain/TRUTH.md` "Never say".
3. Save the caption to a scratch file and run `python3 media/brand/check_post.py caption.txt [image.html]`.
   It must PASS. A WARN for no number means ask for a real one.
4. Label: pilot units are "pilot units, not yet verified credits"; a cloned voice or AI image is labelled; no
   verified tick, invented handle or fake urgency.
5. Show the draft. Posting or sending is ASK.

## Known checker flaw
It fails any text with "credits" that lacks the pilot label, even off topic. Do not reword the truth to dodge it;
note the reason in the run record (learning item 8 in `brain/loop/LEARNING.md`).

## Brand
Rume and VOREM: light blue #8FD3FF (deep #3FA9F5), white, transparent diamond glass, ink #071A2E for reading only.
Amber is retired. The CarbonLedger app keeps its green.

## Never
Name a client, publish a person's voice, face or words without consent, or use an unverified personal claim.
