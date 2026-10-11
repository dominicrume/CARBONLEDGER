// CO2 estimate for a product, following the agreed source order:
//   1 International study (Poore & Nemecek)  2 National database (Agribalyse, France)
//   3 Widely accepted organisation (reserved)  4 Educated guess, rounded up.
// Where tiers 1 and 2 both give a figure, the higher is used, so the result errs high.
import { CONFIG } from '../config.js';
import { FOOD_FACTORS, FOOD_RULES, PN_SOURCE, ESTIMATE_GROUPS, GROUP_RULES, AGRIBALYSE_SKIP } from '../data/factors.js';

export const TIERS = {
  1: 'International study',
  2: 'National database',
  3: 'Recognised organisation',
  4: 'Estimate, rounded up',
};

function matchFood(text) {
  for (const r of FOOD_RULES) if (r.re.test(text)) return { key: r.key, kgPerKg: FOOD_FACTORS[r.key] * (r.x || 1), x: r.x || 1 };
  return null;
}

export function guessGroup(product) {
  const text = [product.hint, ...(product.cats || [])].join(' ');
  return (GROUP_RULES.find(r => r.re.test(text)) || { id: 'food' }).id;
}

// product: { name, grams, hint, cats, agribalyseKgPerKg, groupId? }
// returns: { grams (CO2e, whole grams rounded up), tier, source, detail }
export function estimateProduct(product) {
  // Numbers from outside (product lookups) are untrusted. Anything that is not a sane positive number is ignored.
  const okGrams = typeof product.grams === 'number' && Number.isFinite(product.grams) && product.grams > 0 ? product.grams : null;
  const agri = product.agribalyseKgPerKg;
  const okAgri = typeof agri === 'number' && Number.isFinite(agri) && agri > 0 && agri <= CONFIG.maxAgribalyseKgPerKg;
  const weightKg = (okGrams || CONFIG.unknownWeightGrams) / 1000;
  const weightNote = okGrams ? '' : ` (pack weight unknown, ${CONFIG.unknownWeightGrams} g assumed)`;
  const candidates = [];

  if (!product.groupId) {
    const m = matchFood(product.hint || '') || matchFood((product.cats || []).join(' '));
    if (m) candidates.push({ tier: 1, kg: m.kgPerKg * weightKg, source: PN_SOURCE,
      detail: `${m.key} ${m.kgPerKg.toFixed(2)} kg CO₂e per kg${m.x > 1 ? ` (×${m.x} for concentrate)` : ''}${weightNote}` });
    const prepared = AGRIBALYSE_SKIP.test([product.hint, ...(product.cats || [])].join(' '));
    if (okAgri && !prepared) candidates.push({ tier: 2, kg: agri * weightKg,
      source: 'Agribalyse (French government environmental database)', detail: `${agri.toFixed(2)} kg CO₂e per kg${weightNote}` });
  }

  let best = candidates.sort((a, b) => b.kg - a.kg)[0];
  if (!best) {
    const g = ESTIMATE_GROUPS.find(x => x.id === (product.groupId || guessGroup(product))) || ESTIMATE_GROUPS.at(-1);
    const base = g.perItem ?? g.perKg * weightKg;
    best = { tier: 4, kg: base * CONFIG.estimateUplift, source: 'CarbonLedger category estimate',
      detail: `${g.label}: ${g.perItem ? `${g.perItem} kg per item` : `${g.perKg} kg per kg${weightNote}`}, plus ${Math.round((CONFIG.estimateUplift - 1) * 100)}% margin` };
  }
  return { grams: Math.ceil(best.kg * 1000), tier: best.tier, source: best.source, detail: best.detail, alternatives: candidates.length };
}
