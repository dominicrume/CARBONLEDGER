# Hardening: Product

The product can fail people even when the code is perfect. These rules stop that.

## Claims discipline (the largest product risk)
Pilot units are simulated. Say so wherever a unit appears. Use these words:

| Use | Do not use, until verified and backed |
|---|---|
| "Retire pilot units" | "Offset your footprint" |
| "Pilot units, not verified credits" | "Carbon neutral", "net zero", "climate positive" |
| "Estimated footprint, rounded up" | "Your exact footprint" |
| "Recorded on Solana devnet, a test network" | "Permanently on the blockchain" |
| "Clearing a country's pilot target" | "Cleared this country's emissions" |

The app's current screens say "Offset" and "Confirm offset". Change them before any public demo (docs/ux/DESIGN-SYSTEM.md).
A judge, a regulator or a journalist reads the screen, not the code.

## Estimates
- Every estimate shows its tier and source, and errs high. The app already does this. Keep it.
- A model never invents a factor. It may suggest a category, and a person can overrule it.
- Show "how we worked this out" on every receipt line.

## The game must not pull people into harm
- Leaderboards use server totals only. A browser total is never a score.
- No pressure copy ("you are letting the country down"). No streak that punishes a missed day.
- No real-money step until payments, consumer-law checks and refunds exist.

## Trust
- Every receipt can be verified by anyone: hash, serial range, and explorer link when on-chain.
- Say plainly what is recorded (an id and a hash) and what is not (names, places, baskets).
- A failed action says "Nothing was recorded." and means it.

## People and data
- Personal data never goes on a public chain. Coordinates from farmers are coarse (geohash) and raw files stay off-chain.
- Users can delete their off-chain data. The chain keeps a hash that cannot be turned back into the data.
- If children can reach the app, ask counsel about the UK Children's Code before launch (COMPLIANCE.md).

## Access
- Colour contrast at least 4.5 to 1 for text. Keyboard reach for every action. Respect reduced motion.
- The globe and the game must work without colour alone and without a mouse.

## Product break drills
- Ask five strangers to explain what "pilot unit" means. If two guess wrong, change the words.
- Screenshot every screen. Circle every sentence that could read as a promise. Fix or remove each one.
- Try to top the leaderboard with a browser edit. It must fail once totals come from the server.
