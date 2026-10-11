# Design System: Keep, Change, Add

The partner's app is the vision. Keep its character. Change only what makes a claim we cannot support or hides what
the system knows. Seek to understand first: the person on this screen wants to see their footprint honestly and do
something real about it, without being lectured or fooled.

## Keep (what works)
- DM Serif Display for headings, DM Sans for text, DM Mono for numbers and ids.
- Six tabs: Shop, Travel, Daily, Countries, Me, Business. Level chip. Receipts as a tidy sheet.
- Estimates that err high and name their source tier.
- The countries view and the game, with its labels for example players and simulated totals.

## Change
| Where | Now | Change to | Why |
|---|---|---|---|
| Offset button and sheet | "Offset 250 g for 0.06 pounds", "Confirm offset" | "Retire pilot units", "Confirm retirement" | HARDENING-PRODUCT claims table |
| Receipt footer | "Recorded on the demo ledger on this device. Solana recording comes next." | "Recorded on Solana devnet, a test network" with the explorer link, or "Recorded on this device only" in local mode | Say what is true |
| Every unit mention | none | A small "Simulated pilot units" tag beside CLT counts | Simulated until verified |
| Estimates | Source tier shown in the basket | Same, plus a "How we worked this out" line on the receipt | Show your working |
| Errors | Message from the API | Keep the API's "Nothing was recorded." sentence visible | Trust |
| Footer | none | Credits for data sources and a link to the receipt verifier | COMPLIANCE C13 |

## Add (not built)
1. Verify screen: paste a receipt id, see its hash, serial range and chain status.
2. Mandate screen for businesses: set a cap, choose projects, set expiry, revoke.
3. Connection state: show "Connected to the ledger" or "Working offline" when the mode is solana-devnet.

## Checks before any public demo
- Text contrast at least 4.5 to 1. Tab through every action without a mouse. Respect reduced motion.
- The globe has a text alternative. Colour is never the only signal.
- Screenshot every screen and circle each sentence that could read as a promise. Remove or fix it.
