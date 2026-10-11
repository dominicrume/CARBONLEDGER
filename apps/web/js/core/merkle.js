// Browser-side Merkle proof check, the same rules as packages/core/carbonledger/merkle.py:
// leaf = sha256(0x00 || hash bytes), node = sha256(0x01 || left || right), an odd node pairs with itself.
// Lets the verify screen show that a receipt's hash sits under the anchored root, with no trust in the API.
const hex = b => Array.from(new Uint8Array(b), x => x.toString(16).padStart(2, '0')).join('');
const bytes = h => new Uint8Array(h.match(/../g).map(x => parseInt(x, 16)));
const sha = async (...parts) => {
  const total = parts.reduce((s, p) => s + p.length, 0), buf = new Uint8Array(total);
  let o = 0; for (const p of parts) { buf.set(p, o); o += p.length; }
  return new Uint8Array(await crypto.subtle.digest('SHA-256', buf));
};

export async function leafHash(hexHash) { return sha(new Uint8Array([0]), bytes(hexHash)); }

// path: [[side, siblingHex], ...] where side is 'L' when the sibling sits on the left.
export async function verifyProof(hexHash, path, expectedRoot) {
  let cur = await leafHash(hexHash);
  for (const [side, sib] of path) {
    const s = bytes(sib);
    cur = side === 'L' ? await sha(new Uint8Array([1]), s, cur) : await sha(new Uint8Array([1]), cur, s);
  }
  return hex(cur) === expectedRoot;
}
