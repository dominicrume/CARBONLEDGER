# Flows

Status: EXISTS means it is in the imported app. NEW means it needs building.

1. Scan and retire (EXISTS): scan a barcode, see the estimate and its source, add to basket, retire pilot units, get a receipt.
2. Travel (EXISTS): choose a mode and distance, see the estimate, retire.
3. Daily (EXISTS): partner-funded actions credit grams to the user. Needs a clear statement of who pays (SCALING).
4. Countries (EXISTS): pick a country or follow the Frontline. Wording must say "historical emissions 1850 to 2019".
5. Business (EXISTS): footprint for a period across six areas, then retire.
6. Verify a receipt (NEW): receipt id in, hash and serial range and chain status out.
7. Agent mandate (NEW): owner sets cap, projects and expiry. The agent retires within it. Owner can revoke at any time.
8. Failure paths (PARTLY): API down gives "Could not reach the CarbonLedger API. Nothing was recorded."

Each flow ends with one line the person can repeat to someone else: what they did, and what was recorded.
