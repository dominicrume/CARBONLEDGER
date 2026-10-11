# Decision: Which chain, and should we fork Solana?

Written 2026-10-11. Sources are named. VERIFIED means read in a source this session. Secondary means a news or blog page.

## Answer
Build on Solana. Use devnet for the demo. Do not fork Solana or start an own chain now. Keep the design portable so
an own chain stays possible later.

## Why not fork now
1. The hackathon scores the wrong thing for a fork. Colosseum's rules pay the Solana track ($100,000 across 10
   products, so $10,000 each) to products that integrate with the Solana blockchain. A forked chain is not Solana.
   (VERIFIED, official rules PDF.) The main awards ($30,000 grand prize, 20 teams at $15,000) do not depend on the
   chain. A fork risks the track money and gains nothing in the main awards.
2. Time. The deadline is 11:59pm Pacific on 12 October 2026, which is 06:59 UTC on 13 October. About 53 hours remained
   when this was written. Running even a test cluster is a project of its own. Tools exist, such as ABK Labs'
   SVMKit that launches a standalone cluster (secondary), but validators, a gas token, wallets, an explorer and
   security are still yours to run.
3. It can be done, so the question is real. About two dozen chains already run the Solana Virtual Machine (Blockworks,
   secondary). Pyth runs an application-specific SVM chain, shipped in August 2022. Eclipse launched mainnet in
   November 2024, and SOON and Sonic are SVM layer-2s. As of February 2026 the SVM rollup idea is technically
   viable but commercially early (BlockEden analysis, secondary).
4. A chain does not solve the hard problems. A register is only as honest as its inputs, and that is verification of
   real projects (see MRV-LAYERS.md). A chain run by one team is not neutral either, and registries will weigh who
   controls the validators.
5. The field is not empty. About 26 registries exist (Straits Times, quoting World Bank material). The Climate Action
   Data Trust links their data to help prevent double counting (World Bank blog). Verra requires its written consent
   for tokens built on its credits, and said in January 2026 it aims to finish a tokenization policy by end of 2026
   (Verra statement, quoted in a January 2026 post). So the winning move is a neutral, careful layer on an existing
   chain, with the anti double-count rule built in, not a new chain.

## What we do instead
- Registry rules as an Anchor program on Solana: PDAs make a double retirement or a double link impossible.
- The same rules as a tested reference model and vectors, so any future chain can be proven equal.
- The API signs receipts and anchors their hash on Solana now (memo), the program after.
- No Solana types in the core. The chain is an interface. A port to an SVM rollup or an EVM chain changes the client
  and the contract, not the rules.

## Your Solidity and Canton experience, and where it applies
- Solana programs are Rust (Anchor). Solidity does not run on Solana. The habits carry over: access control on every
  state change, checks before effects, explicit error names, no hidden admin powers, a pause or suspend lever.
- The Canton work contributes the mandate pattern: cap, allow-list, expiry, revoke. It is in mandate.py with vectors
  and can be ported to a Solana account later.
- An EVM version is possible later by porting the vectors to Solidity. It is not a hackathon task.
- Accuracy note for any pitch: the Canton result is third place ($1,500), user-stated. See PITCH-FACTS.md.

## When to revisit (all must be written down with data)
- A registry, regulator or standards body requires a permissioned validator set.
- Measured volume or finality needs exceed what a shared chain gives at acceptable cost.
- Registries want to run validators and set rules together.
- Data residency requires it.
Even then, prefer an SVM rollup or app-chain framework, or Climate Action Data Trust integration, over forking the base client.

## For the partner conversation
The partner wants an own chain first. Say it plainly: "A chain is a database that strangers trust. People trust the
data, not the chain. We win the data's trust first, on a chain that exists, and we design so an own chain stays open."
Then show the 53-hour clock and the track money.
