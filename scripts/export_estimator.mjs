// Exports the web app's estimator data as JSON and records golden vectors from the app's OWN code.
// The Python estimator must reproduce every vector exactly (tests/test_estimate_parity.py).
import { writeFileSync } from 'node:fs';
import * as F from '../apps/web/js/data/factors.js';
import { estimateProduct } from '../apps/web/js/core/estimate.js';
import { CONFIG } from '../apps/web/js/config.js';

const rx = r => ({ src: r.source, flags: r.flags });
const data = {
  PN_SOURCE: F.PN_SOURCE,
  FOOD_FACTORS: F.FOOD_FACTORS,
  FOOD_RULES: F.FOOD_RULES.map(r => ({ ...rx(r.re), key: r.key, x: r.x ?? null })),
  ESTIMATE_GROUPS: F.ESTIMATE_GROUPS,
  GROUP_RULES: F.GROUP_RULES.map(r => ({ ...rx(r.re), id: r.id })),
  AGRIBALYSE_SKIP: rx(F.AGRIBALYSE_SKIP),
  CONFIG: { unknownWeightGrams: CONFIG.unknownWeightGrams, estimateUplift: CONFIG.estimateUplift, maxAgribalyseKgPerKg: CONFIG.maxAgribalyseKgPerKg },
};
writeFileSync('packages/core/carbonledger/data_factors.json', JSON.stringify(data, null, 1));

const hints = ['beef', 'lamb', 'instant-coffee', 'coffee', 'chocolate', 'prawns', 'salmon', 'bacon', 'chicken', 'cheddar', 'yoghurt',
  'eggs', 'olive-oil', 'palm-oil', 'rice', 'sugar', 'tofu', 'peanut', 'whole-milk', 'oat-based', 'porridge', 'wine', 'lager',
  'tomato', 'baked-beans', 'bread', 'peas', 'banana', 'apple-juice', 'apple', 'orange-juice', 'lemon', 'grape', 'crisps', 'unknown-thing'];
const vectors = [];
let n = 0;
for (const hint of hints) {
  for (const grams of [null, 100, 750]) {
    const product = { name: `v${++n}`, grams, hint, cats: [] };
    vectors.push({ product, expected: estimateProduct(product) });
  }
}
// Agribalyse competes with the study value; the higher figure must win. Prepared products skip Agribalyse.
for (const [hint, agri] of [['beef', 5], ['beef', 150], ['chocolate', 2], ['instant-coffee', 100], ['tea-bags', 40], ['rice', 9]]) {
  const product = { name: `a${++n}`, grams: 200, hint, cats: [], agribalyseKgPerKg: agri };
  vectors.push({ product, expected: estimateProduct(product) });
}
// Category tags only, no hint (group guess), and explicit groups for every tier-4 group.
for (const cats of [['beverages', 'sodas'], ['meat', 'poultry'], ['dairy'], ['snacks'], ['pizza'], ['bread', 'cereal'], ['teas'], []]) {
  const product = { name: `c${++n}`, grams: 330, hint: '', cats };
  vectors.push({ product, expected: estimateProduct(product) });
}
for (const g of F.ESTIMATE_GROUPS) {
  const product = { name: `g${++n}`, grams: 450, hint: '', cats: [], groupId: g.id };
  vectors.push({ product, expected: estimateProduct(product) });
}
// Hostile values from an outside lookup. Each must fall back safely (never negative, never absurd, never a crash).
for (const [label, extra] of [['agri-negative', { agribalyseKgPerKg: -5 }], ['agri-huge', { agribalyseKgPerKg: 1e9 }], ['agri-string', { agribalyseKgPerKg: '7' }],
  ['agri-zero', { agribalyseKgPerKg: 0 }], ['grams-negative', { grams: -50, agribalyseKgPerKg: 3 }], ['grams-zero', { grams: 0 }], ['grams-string', { grams: '100' }]]) {
  const product = { name: `h-${label}`, grams: 100, hint: '', cats: ['en:something'], ...extra };
  vectors.push({ product, expected: estimateProduct(product) });
}
writeFileSync('conformance/estimate_vectors.json', JSON.stringify(vectors, null, 1));
console.log('data and', vectors.length, 'golden vectors written');
