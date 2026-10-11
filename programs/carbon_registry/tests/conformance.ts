// Replays conformance/registry_vectors.json against the compiled program, in-process with LiteSVM (no validator;
// the x86 test validator cannot run under Rosetta on this Mac, and LiteSVM is faster anyway).
// Run: anchor build, then `npm test` (ts-mocha). Maps Anchor's "already in use" (a PDA init on an existing account)
// to DUPLICATE_LINK and EXISTS, as programs/carbon_registry/README.md says.
import { fromWorkspace, LiteSVMProvider } from "anchor-litesvm";
import { BN, Program, Wallet } from "@coral-xyz/anchor";
import { Keypair, PublicKey, SystemProgram } from "@solana/web3.js";
import { createHash } from "crypto";
import { readFileSync } from "fs";
import { expect } from "chai";

type Step = { op: string; args: any[]; expect: string };
type Vector = { name: string; steps: Step[] };
const VECTORS: Vector[] = JSON.parse(readFileSync("conformance/registry_vectors.json", "utf8"));
const IDL = JSON.parse(readFileSync("target/idl/carbon_registry.json", "utf8"));

const enc = (s: string, n: number) => { const b = Buffer.alloc(n); b.write(s); return [...b]; };
const u64 = (n: number) => new BN(n);
const idOf = (s: string) => new BN(createHash("sha256").update(s).digest("hex").slice(0, 12), 16);

describe("carbon_registry conformance (LiteSVM)", () => {
  const client = fromWorkspace(".");
  const auth = Keypair.generate(), ver = Keypair.generate(), mallory = Keypair.generate();
  for (const k of [auth, ver, mallory]) client.airdrop(k.publicKey, BigInt(10e9));
  const provider = new LiteSVMProvider(client, new Wallet(auth));
  const program = new Program(IDL as any, provider);
  const signers: Record<string, Keypair> = { auth, ver, mallory, alice: auth, bob: auth, carol: auth };

  const [registry] = PublicKey.findProgramAddressSync([Buffer.from("registry")], program.programId);
  const project = (pid: string) => PublicKey.findProgramAddressSync([Buffer.from("project"), idOf(pid).toArrayLike(Buffer, "le", 8)], program.programId)[0];
  const batch = (pid: string, bid: string) => PublicKey.findProgramAddressSync([Buffer.from("batch"), project(pid).toBuffer(), idOf(bid).toArrayLike(Buffer, "le", 8)], program.programId)[0];
  const linkKey = (reg: string, serial: string) => createHash("sha256").update(`${reg}:${serial}`).digest();
  const link = (reg: string, serial: string) => PublicKey.findProgramAddressSync([Buffer.from("link"), linkKey(reg, serial)], program.programId)[0];
  const batchProject: Record<string, string> = {};

  // Send without the bridge's error path (which trips on a failed transaction's missing signature): build the
  // transaction, sign it, hand it to LiteSVM, and read the logs of a failure ourselves.
  const run = async (builder: any, extra: Keypair[] = []) => {
    const tx = await builder.transaction();
    tx.recentBlockhash = client.latestBlockhash();
    tx.feePayer = auth.publicKey;
    tx.sign(auth, ...extra.filter(k => !k.publicKey.equals(auth.publicKey)));
    const res: any = client.sendTransaction(tx);
    if (typeof res?.err === "function") {
      const logs = (typeof res.meta === "function" ? res.meta().logs() : []) as string[];
      throw new Error(`${String(res.err())} ${logs.join(" | ")}`);
    }
    return res;
  };

  const codeOf = (e: any): string => {
    const s = String(e?.message || e) + " " + JSON.stringify(e?.logs || e?.transactionLogs || "");
    const m = /\b(UNAUTHORISED|NOT_ATTESTED|OVER_ISSUANCE|OVER_RETIREMENT|BAD_AMOUNT|SUSPENDED|NOT_SUSPENDED|UNKNOWN_BATCH|OVERFLOW|EXISTS|DUPLICATE_LINK|TOO_MANY_VERIFIERS|ANCHOR_GAP)\b/.exec(s);
    if (m) return m[1];
    if (/already in use/.test(s)) return "EXISTS";
    if (/ConstraintAddress|ConstraintRaw|unknown signer|Signature verification failed|Unauthorised|missing required signature/i.test(s)) return "UNAUTHORISED";
    return s.slice(0, 200);
  };

  before(async () => {
    await run(program.methods.initializeRegistry(ver.publicKey, u64(10 ** 15)).accounts({ registry, authority: auth.publicKey, systemProgram: SystemProgram.programId }));
  });

  for (const v of VECTORS) {
    it(v.name, async () => {
      const P = (pid: string) => `${v.name}:${pid}`;        // every vector gets its own project and batch ids
      for (const s of v.steps) {
        let outcome = "ok";
        // A negative amount cannot be encoded as a u64 at all: the wire type refuses it before any program runs.
        // That is the same answer the reference model gives (BAD_AMOUNT), enforced one layer earlier.
        if (s.args.some((a: any) => typeof a === "number" && a < 0)) { expect(s.expect, `${v.name}: ${s.op} negative`).to.equal("BAD_AMOUNT"); continue; }
        try {
          if (s.op === "register_project") {
            const [signer, pid, country, meth] = s.args;
            await run(program.methods.registerProject(idOf(P(pid)), enc(country, 3), enc(meth, 16)).accounts({ registry, project: project(P(pid)), authority: signers[signer].publicKey, systemProgram: SystemProgram.programId }), [signers[signer]]);
          } else if (s.op === "attest_project") {
            const [signer, pid, g] = s.args;
            await run(program.methods.attestProject(u64(g)).accounts({ registry, project: project(P(pid)), verifier: signers[signer].publicKey }), [signers[signer]]);
          } else if (s.op === "issue_batch") {
            const [signer, pid, bid, vintage, g] = s.args;
            batchProject[P(bid)] = P(pid);
            await run(program.methods.issueBatch(idOf(P(bid)), vintage, u64(g)).accounts({ registry, project: project(P(pid)), batch: batch(P(pid), P(bid)), authority: signers[signer].publicKey, systemProgram: SystemProgram.programId }), [signers[signer]]);
          } else if (s.op === "retire") {
            const [, bid, g] = s.args;
            const pid = batchProject[P(bid)];
            if (!pid) throw new Error("UNKNOWN_BATCH");
            await run(program.methods.retire(u64(g)).accounts({ registry, project: project(pid), batch: batch(pid, P(bid)), operator: auth.publicKey }));
          } else if (s.op === "link_external") {
            const [signer, reg, serial, bid] = s.args;
            const pid = batchProject[P(bid)];
            if (!pid) throw new Error("UNKNOWN_BATCH");
            try {
              await run(program.methods.linkExternalCredit([...linkKey(reg, serial)]).accounts({ registry, batch: batch(pid, P(bid)), link: link(reg, serial), authority: signers[signer].publicKey, systemProgram: SystemProgram.programId }), [signers[signer]]);
            } catch (e) { if (codeOf(e) === "EXISTS") throw new Error("DUPLICATE_LINK"); throw e; }
          } else if (s.op === "suspend_project") {
            const [signer, pid] = s.args;
            await run(program.methods.suspendProject().accounts({ registry, project: project(P(pid)), authority: signers[signer].publicKey }), [signers[signer]]);
          } else throw new Error(`unknown op ${s.op}`);
        } catch (e) { outcome = codeOf(e); }
        expect(outcome, `${v.name}: ${s.op} ${JSON.stringify(s.args)}`).to.equal(s.expect);
      }
    });
  }

  it("the link key is unique per (registry, serial): the same serial in another registry links", async () => {
    expect(link("RegistryX", "SER-0001").toBase58()).to.not.equal(link("RegistryY", "SER-0001").toBase58());
  });
});
