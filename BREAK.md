# BREAK: A Hostile Review of Our Own Work

Five hats. Each one tries to hurt the product. Findings are numbered and carry a status.

## Planner
Question: is the plan honest about what is hard?
- The plan could say "own chain" and hide that verification is the hard part. It does not. MRV-LAYERS.md leads with it.
- The 53-hour clock makes Block C (the Anchor program) a gamble. HACKATHON-48H.md says to stop at the block's end and present the memo path as the integration.

## Builder
Question: what did we cut that will bite?
- F1 FIXED. The estimator took outside numbers on trust. A negative value gave -500 g, a huge one gave 100,000 tonnes for a 100 g item, a string crashed it. Fixed in the app and the server port, with seven hostile vectors.
- F2 OPEN (D1). The API trusts the grams the browser sends. A client can retire less than it owes.
- F3 OPEN (D8). A receipt label is free text and could carry personal data into the database.

## Thief
Question: how do I get value out or fake value in?
- F4 OPEN (D2). No login. Anyone who finds the API can retire pilot units and fill the chain with memos.
- F5 OPEN (D6, T4, T5). Authority and verifier keys are not in a multisig yet, because they only exist in the model.
- Faked issuance without attestation is refused by the model (tested). The program is not yet tested.

## Firefighter
Question: what do we do at 3am?
- F6 OPEN (D5). The API says "recorded" when a transaction is submitted, not confirmed. A dropped transaction would leave a receipt with no chain record.
- F7 OPEN (D9). State lives in memory. A restart forgets receipts and idempotency keys. Postgres exists as SQL only.
- Chain outage is handled: nothing is recorded and the person is told.

## Doubter
Question: which of our claims would a hostile reader take apart?
- F8 OPEN. "Single register." There are about 26 registries and the Climate Action Data Trust links their data. The claim must be about the retirement layer and the anti double-count rule. PITCH-FACTS.md bans the false version.
- F9 OPEN. The app says "Offset" and "Confirm offset". Until a verifier attests real units, that is a claim we cannot back (D10).
- F10 OPEN (D7). Three CDN scripts load without integrity hashes and the page has no Content-Security-Policy.
- F11 POSITIVE. Product names from the lookup are escaped before they reach the page.

## Drills to run next (the person running writes the result under the finding)
1. 1,000 identical retire requests at once.
2. Kill the chain client mid-request.
3. Edit a receipt and cut the tail, then run the verifier and compare the anchored head.
4. A mandate cap of 1,000 g with 1,001 g requested, then revoke.
