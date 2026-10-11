# BREAK: A Hostile Review of Our Own Work

Five hats. Each one tries to hurt the product. Findings are numbered and carry a status.

## Planner
Question: is the plan honest about what is hard?
- The plan could say "own chain" and hide that verification is the hard part. It does not. MRV-LAYERS.md leads with it.
- The 53-hour clock makes Block C (the Anchor program) a gamble. HACKATHON-48H.md says to stop at the block's end and present the memo path as the integration.

## Builder
Question: what did we cut that will bite?
- F1 FIXED. The estimator took outside numbers on trust. A negative value gave -500 g, a huge one gave 100,000 tonnes for a 100 g item, a string crashed it. Fixed in the app and the server port, with seven hostile vectors.
- F2 FIXED 2026-10-11 (D1). The server prices every request from typed items with the same tables as the app (1,787 golden vectors) and refuses a lower total.
- F3 FIXED 2026-10-11 (D8). Labels are a closed vocabulary. Free text is hashed into the receipt and never stored. Drill 5 proves script tags and an address never come back.

## Thief
Question: how do I get value out or fake value in?
- F4 FIXED 2026-10-11 (D2). Every write needs an API key (hashed, with a role). Per-key rate limit, request size limit, server deadline. Drill 7.
- F5 OPEN (D6, T4, T5). Authority and verifier keys are not in a multisig yet, because they only exist in the model. The revised program holds three verifier keys and needs two above a threshold, but it is not compiled.
- Faked issuance without attestation is refused by the model (tested). The program is not yet tested.

- F12 FIXED 2026-10-11 (D16). The browser made a fresh idempotency key per call, so a retry after a timeout retired twice. One key per intent now.
- F13 FIXED 2026-10-11 (D16). The client timeout (8 s) was below the server's worst case (two RPC calls at 15 s) and the message said "Nothing was recorded" when the server may have recorded. Timeout raised to 40 s and the message now says the outcome is unconfirmed.
- F14 FIXED 2026-10-11 (D17). Sequential receipt ids in the public memo leaked the run rate. Ids now come from the receipt content.
- F15 FIXED 2026-10-11 (D1 part). Lines did not have to add up to the total. They must now.

## Firefighter
Question: what do we do at 3am?
- F6 FIXED 2026-10-11 (D5). The anchor worker confirms before anything says anchored; a dropped transaction is resubmitted; after five tries the receipt is shown as failed, in /health and in the audit.
- F7 FIXED 2026-10-11 (D9). With DATABASE_URL every commit is written to Postgres first; the server rebuilds from the rows at start and refuses to start on a broken chain. tests/test_db_store.py.
- Chain outage is handled: nothing is recorded and the person is told.

## Doubter
Question: which of our claims would a hostile reader take apart?
- F8 OPEN. "Single register." There are about 26 registries and the Climate Action Data Trust links their data. The claim must be about the retirement layer and the anti double-count rule. PITCH-FACTS.md bans the false version.
- F9 FIXED 2026-10-11 (D10). Every screen now says retire pilot units, with a simulated tag, and tests/test_web_wording.py fails if a banned word returns.
- F10 FIXED 2026-10-11 (D7). Scripts are self-hosted at pinned versions with SHA-384 integrity, and the page carries a Content-Security-Policy. tests/test_web_supply_chain.py.
- F11 POSITIVE. Product names from the lookup are escaped before they reach the page.
- F16 FOUND 2026-10-11, operational. A web server from a browser-test run interrupted by a folder rename kept the test port and served 404s, so every browser test failed until it was found. scripts/e2e.sh now checks that the API on its port is ours before testing; the stale-port case needs the same check for the web port (D25).
- F17 FOUND 2026-10-11, supply chain. npm audit flagged Playwright 1.49.1 (browser downloads without certificate verification). Moved to 1.64.0. CI runs npm audit at the high level.

## Drills, run 2026-10-11 with scripts/drills.py against a live API (dry-run chain)
| Drill | Result |
|---|---|
| 1,000 identical retire requests at once | PASS. 1,000 answers of 200, one retirement. |
| 1,000 distinct retire requests at once | PASS. No overlapping serial ranges, chain intact, 1,001 anchored. |
| Placeholder signing key with CHAIN_MODE=solana-devnet | PASS. The API refuses to start. |
| Chain unreachable at request time | PASS. 502, "Nothing was recorded", zero retirements. |
| Mandate cap 1,000 g with 1,001 g, then 1,000 g, then revoke | PASS. OVER_CAP, allowed, REVOKED. |
| Script tags and an address in free text | PASS. Hashed, never stored, never returned. |
| Free-text label, 70 kB body | PASS. 422 and 413, both say nothing was recorded. |
| No key, wrong key | PASS. 401 NO_KEY, 401 BAD_KEY. |
| Edit one receipt | PASS. verify names index 2. |
| Cut the tail | PASS. The chain verifies but the head disagrees with the anchored head. |
Also run in the browser (apps/web/test/e2e): a forged local record is dropped by the ledger mirror; the API-down path says nothing was recorded; axe finds no WCAG 2.1 AA violation on any screen.

## Drills to run next (need a person or a network)
1. The first real devnet transaction, then the same drills with CHAIN_MODE=solana-devnet.
2. Kill the RPC endpoint while a batch is pending and watch it resubmit, then fail after five tries, then re-anchor by hand (D24).
3. Restart the API on Postgres under load and check no receipt is lost and no serial reused (test_db_store does this cold).
4. A stranger with database access tries to edit history: the triggers refuse (tested), so try a superuser and watch recheck.py catch it (tested in test_db_store).
