// The browser verifier must agree with the Python tree. Vectors below were produced by packages/core/carbonledger/merkle.py
// (see tests/test_merkle_parity.py, which regenerates and compares them).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { verifyProof } from '../js/core/merkle.js';

const V = JSON.parse(readFileSync(new URL('../../../conformance/merkle_vectors.json', import.meta.url)));

test('every vector proves against its root, and a changed leaf does not', async () => {
  for (const v of V) {
    assert.equal(await verifyProof(v.leaf, v.path, v.root), true, v.name);
    assert.equal(await verifyProof(v.leaf.replace(/^./, c => (c === 'a' ? 'b' : 'a')), v.path, v.root), false, v.name);
  }
  assert.ok(V.length >= 10);
});
