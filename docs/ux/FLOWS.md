# Flows

Status: EXISTS means it is in the imported app. NEW means it needs building.

1. Scan and retire (EXISTS): scan a barcode, see the estimate and its source, add to basket, retire pilot units, get a receipt.
2. Travel (EXISTS): choose a mode and distance, see the estimate, retire.
3. Daily (EXISTS): partner-funded actions credit grams to the user. Needs a clear statement of who pays (SCALING).
4. Countries (EXISTS): pick a country or follow the Frontline. Wording must say "historical emissions 1850 to 2019".
5. Business (EXISTS): footprint for a period across six areas, then retire.
6. Verify a receipt (EXISTS): receipt id in, outcome, rule, hash, serial range, anchor status and a Merkle proof recomputed in the browser out.
7. Agent mandate (EXISTS): owner sets cap, projects, expiry and the agent's public key. The agent retires within it. Owner can revoke at any time.
8. Failure paths (EXISTS): API down says nothing was recorded; a timeout says the outcome is unconfirmed; no login offers a demo login; a refused attempt names its refusal receipt.
9. The game loop (EXISTS): mission strip, XP on the retire button, reward moment, Me command centre, World clock with a celebration when a country is cleared. See DESIGN-SYSTEM.md.

Each flow ends with one line the person can repeat to someone else: what they did, and what was recorded.
