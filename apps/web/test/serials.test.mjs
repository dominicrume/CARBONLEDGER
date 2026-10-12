import { test } from 'node:test';
import assert from 'node:assert/strict';
import { tonneShares, shareOfTonne, tonneText, tonneShort } from '../js/core/serials.js';

test('a range inside one tonne names that tonne, counted from 1', () => {
  assert.deepEqual(tonneShares(11_712_279, 11_716_798), [{ tonne: 12, first: 712_279, last: 716_797, grams: 4_519 }]);
  assert.equal(tonneText(11_712_279, 11_716_798), 'pilot tonne 12 (grams 712,279 to 716,797 of it, 0.45%)');
});

test('the first gram of a batch is gram 0 of pilot tonne 1', () => {
  assert.deepEqual(tonneShares(0, 1), [{ tonne: 1, first: 0, last: 0, grams: 1 }]);
  assert.equal(shareOfTonne(1), 'under 0.01%');
});

test('a range across a tonne boundary names both tonnes, and the grams add up', () => {
  const s = tonneShares(999_000, 1_002_000);
  assert.deepEqual(s.map(x => [x.tonne, x.first, x.last, x.grams]), [[1, 999_000, 999_999, 1_000], [2, 0, 1_999, 2_000]]);
  assert.equal(s.reduce((a, x) => a + x.grams, 0), 3_000);
});

test('a whole tonne is 100%, and a long range is summarised', () => {
  assert.equal(shareOfTonne(1_000_000), '100%');
  assert.equal(tonneText(0, 5_000_000), 'pilot tonnes 1 to 5 (5 tonnes)');
});

test('missing or broken ranges give nothing rather than a wrong tonne', () => {
  for (const [a, b] of [[null, null], [5, 5], [9, 3], [-1, 4], [1.5, 9]]) assert.deepEqual(tonneShares(a, b), []);
  assert.equal(tonneText(undefined, undefined), '');
});

test('the receipt line is short, and honest across a boundary', () => {
  assert.equal(tonneShort(11_712_279, 11_716_798), 'pilot tonne 12, 0.45% of it');
  assert.equal(tonneShort(999_000, 1_002_000), 'pilot tonnes 1 and 2');
  assert.equal(tonneShort(0, 3_000_001), 'pilot tonnes 1 to 4');
  assert.equal(tonneShort(null, null), '');
});
