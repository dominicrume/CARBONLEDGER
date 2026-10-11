// Replays conformance/registry_vectors.json against the deployed program on a local validator (Block 5 step 22).
// STATUS: written, not run. Needs `anchor build` first, then `anchor test`.
// Maps Anchor's "already in use" (a PDA init on an existing account) to DUPLICATE_LINK and EXISTS, as README.md says.
import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { Keypair, PublicKey, SystemProgram } from "@solana/web3.js";
import { createHash } from "crypto";
import { readFileSync } from "fs";
import { expect } from "chai";

type Step = { op: string; args: any[]; expect: string };
type Vector = { name: string; steps: Step[] };
const VECTORS: Vector[] = JSON.parse(readFileSync("conformance/registry_vectors.json", "utf8"));

const enc = (s: string, n: number) => { const b = Buffer.alloc(n); b.write(s); return [...b]; };
const u64 = (n: number) => new anchor.BN(n);
const idOf = (s: string) => u64(parseInt(createHash("sha256").update(s).digest("hex").slice(0, 12), 16));

describe("carbon_registry conformance", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);
  const program = anchor.workspace.carbonRegistry as Program<any>;
  const auth = (provider.wallet as anchor.Wallet).payer;          // "auth" in the vectors
  const ver = Keypair.generate();                                    // "ver"
  const mallory = Keypair.generate();
  const signers: Record<string, Keypair> = { auth, ver, mallory, alice: auth, bob: auth, carol: auth };

  const [registry] = PublicKey.findProgramAddressSync([Buffer.from("registry")], program.programId);
  const project = (pid: string) => PublicKey.findProgramAddressSync([Buffer.from("project"), idOf(pid).toArrayLike(Buffer, "le", 8)], program.programId)[0];
  const batch = (pid: string, bid: string) => PublicKey.findProgramAddressSync([Buffer.from("batch"), project(pid).toBuffer(), idOf(bid).toArrayLike(Buffer, "le", 8)], program.programId)[0];
  const link = (reg: string, serial: string) => PublicKey.findProgramAddressSync([Buffer.from("link"), createHash("sha256").update(`${reg}:${serial}`).digest()], program.programId)[0];
  const batchProject: Record<string, string> = {};

  const codeOf = (e: any): string => {
    const m = /\b(UNAUTHORISED|NOT_ATTESTED|OVER_ISSUANCE|OVER_RETIREMENT|BAD_AMOUNT|SUSPENDED|NOT_SUSPENDED|UNKNOWN_BATCH|OVERFLOW|EXISTS|ANCHOR_GAP)\b/.exec(String(e));
    if (m) return m[1];
    if (/already in use/.test(String(e))) return "EXISTS";
    return String(e);
  };

  before(async () => {
    for (const k of [ver, mallory]) await provider.connection.confirmTransaction(await provider.connection.requestAirdrop(k.publicKey, 2e9));
    await program.methods.initializeRegistry(ver.publicKey, u64(10 ** 15)).accounts({ registry, authority: auth.publicKey, systemProgram: SystemProgram.programId }).rpc();
  });

  for (const v of VECTORS) {
    it(v.name, async () => {
      // every vector gets its own project ids by prefixing with the vector name
      const P = (pid: string) => `${v.name}:${pid}`;
      for (const s of v.steps) {
        let outcome = "ok";
        try {
          if (s.op === "register_project") {
            const [signer, pid, country, meth] = s.args;
            await program.methods.registerProject(idOf(P(pid)), enc(country, 3), enc(meth, 16)).accounts({ registry, project: project(P(pid)), authority: signers[signer].publicKey, systemProgram: SystemProgram.programId }).signers([signers[signer]]).rpc();
          } else if (s.op === "attest_project") {
            const [signer, pid, g] = s.args;
            await program.methods.attestProject(u64(g)).accounts({ registry, project: project(P(pid)), verifier: signers[signer].publicKey }).signers([signers[signer]]).rpc();
          } else if (s.op === "issue_batch") {
            const [signer, pid, bid, vintage, g] = s.args;
            batchProject[P(bid)] = P(pid);
            await program.methods.issueBatch(idOf(P(bid)), vintage, u64(g)).accounts({ registry, project: project(P(pid)), batch: batch(P(pid), P(bid)), authority: signers[signer].publicKey, systemProgram: SystemProgram.programId }).signers([signers[signer]]).rpc();
          } else if (s.op === "retire") {
            const [, bid, g] = s.args;
            const pid = batchProject[P(bid)];
            if (!pid) throw new Error("UNKNOWN_BATCH");
            await program.methods.retire(u64(g)).accounts({ registry, project: project(pid), batch: batch(pid, P(bid)), operator: auth.publicKey }).rpc();
          } else if (s.op === "link_external") {
            const [signer, reg, serial, bid] = s.args;
            const pid = batchProject[P(bid)];
            if (!pid) throw new Error("UNKNOWN_BATCH");
            try {
              await program.methods.linkExternalCredit([...createHash("sha256").update(`${reg}:${serial}`).digest()]).accounts({ registry, batch: batch(pid, P(bid)), link: link(reg, serial), authority: signers[signer].publicKey, systemProgram: SystemProgram.programId }).signers([signers[signer]]).rpc();
            } catch (e) { if (codeOf(e) === "EXISTS") throw new Error("DUPLICATE_LINK"); throw e; }
          } else if (s.op === "suspend_project") {
            const [signer, pid] = s.args;
            await program.methods.suspendProject().accounts({ registry, project: project(P(pid)), authority: signers[signer].publicKey }).signers([signers[signer]]).rpc();
          } else throw new Error(`unknown op ${s.op}`);
        } catch (e) { outcome = codeOf(e); }
        expect(outcome, `${v.name}: ${s.op} ${JSON.stringify(s.args)}`).to.equal(s.expect);
      }
    });
  }
});
