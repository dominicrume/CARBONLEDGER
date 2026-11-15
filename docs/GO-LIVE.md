# Go-live plan: leaving development

Written 2026-11-15 for Rume and the partner. Real money and mainnet switch on only when every gate in sections 1 to 3
is ticked. Engineering items marked BUILT are on the branch `go-live` (built on `payments-test-mode`).

## The order
1. Something real to sell. 2. A company. 3. Counsel. Then 4. payments live, 5. mainnet, 6. launch. Payments and a live
chain are worth nothing until step 1 is solved, so it comes first.

## 1. Something real to sell (the true blocker, DEBT D11)
Today the units are pilot units, not yet verified credits. Two honest routes, not exclusive:
- [ ] **Route A, fastest: retire real credits for customers.** Buy credits that are already issued and certified
  (biochar credits are sold on registries such as Puro.earth, and by other certified suppliers), hold them, and retire
  them on each customer's behalf with the receipt naming the registry serial. Check each supplier's retirement and
  resale terms first. Owner: Rume and the partner.
- [ ] **Route B, own supply: a verified project.** A named verifier attests a real project (CharHarvest Nigeria can
  become this) and units are issued against the attestation, never more than attested. Owner: the partner, the
  verifier.
- [ ] A decision entry naming the route and the price per tonne. Owner: Rume.

## 2. A company
- [ ] Form the company (UK) that owns the IP, signs supplier contracts and takes payments. Owner: Rume and the partner.
- [ ] Business bank account; Stripe account in the company's name (test keys first). Owner: Rume.
- [ ] Brand: CarbonCoin replaces the holding name CarbonLedger, subject to counsel (docs/DECISIONS.md 2026-11-15
  CarbonCoin entry). Domain and trademark checked. Owner: Rume.

## 3. Counsel (docs/COUNSEL-BRIEF.md has the questions)
- [ ] C5 green claims: the wording table, now that units would be real.
- [ ] C6 token status: is a non-transferable receipt token, sold under the name "CarbonCoin", a cryptoasset for UK
  financial promotion rules?
- [ ] C10 taking payments: cards through Stripe, USDC through Solana Pay, refunds, terms of sale.
- [ ] C8 personal data: farmers' GPS photos, users' baskets and trips.
- [ ] C13 / D12 data licences: Open Food Facts, Our World in Data, Agribalyse credits in the app.

## 4. Payments (DEBT D29)
- [x] BUILT, test mode: Solana Pay on devnet (PAYMENTS_MODE=solana-devnet-test). Quote, wallet pays, the server finds
  the transfer on chain, then retires; one payment pays once; the payment goes on the receipt.
- [x] BUILT, test mode: Stripe Checkout (PAYMENTS_MODE=stripe-test) for cards, Apple Pay, Google Pay and bank. Only
  `sk_test_` keys are accepted; a live key is refused at start-up.
- [ ] Live mode: a new decision entry after sections 1 to 3, then live keys and a real-money mode added on purpose.
  Stripe can also take USDC on Solana from wallets (check Stripe's current UK terms). Owner: Rume, Engineering.

## 5. A live chain: Solana mainnet, not an own chain
docs/DECISION-CHAIN.md stands: going live means Solana mainnet. An own chain adds validators, a token, an explorer and
security to run, and buyers trust the verification, not who runs the chain.
- [ ] Independent review of the on-chain program (programs/). Owner: Rume, an external reviewer.
- [ ] Authority, verifier and upgrade keys in a multisig (DEBT D6). Owner: Rume and the partner as signers.
- [ ] The API calls the program instead of anchoring by memo (DEBT D3). A new brief: it changes the chain path.
- [ ] Funded mainnet treasury and fee payer; CHAIN_MODE for mainnet added on purpose (today the API refuses any
  value other than dry-run or solana-devnet). Owner: Engineering after the three items above.

## 6. Operations
- [x] BUILT: operator levers (DEBT D24 paid): suspend a project, re-queue a failed anchor; authority keys only.
- [x] BUILT: the clean count. /v1/metrics has a `real` block that leaves out internal logins (INTERNAL_OWNERS) and
  everything before the launch date (METRICS_SINCE). Set both on the day of launch.
- [x] Daily sweep with live health and chain checks (.github/workflows/sweep.yml).
- [ ] Alerting to a phone or email when the sweep fails. Owner: Rume (choose the channel).
- [ ] The Shop screen still says "Every gram retired is a point"; reword before launch (fair XP). Owner: Engineering.

## 7. Launch day
- [ ] Merge, deploy, set METRICS_SINCE and INTERNAL_OWNERS, switch payments to live, CHAIN_MODE to mainnet.
- [ ] Post the promo films (Downloads/CarbonLedger_promo_HOLD_until_live): 16:9, 9:16, 4:5, with the X post.
- [ ] Weekly: real visitors, real retirements, players returning in week 2 (the `real` block).
