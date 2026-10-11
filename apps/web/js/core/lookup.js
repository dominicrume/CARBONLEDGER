// Barcode -> product. Order: built-in catalogue, then Open Food Facts live (when the browser allows it).
import { CONFIG } from '../config.js';
import { PRODUCTS } from '../data/products.js';

const byCode = new Map(PRODUCTS.map(p => [p.code, p]));
const variants = code => [code, code.replace(/^0+/, ''), code.padStart(13, '0')];

export function catalogue() { return PRODUCTS; }

export async function lookupBarcode(code) {
  for (const c of variants(code)) if (byCode.has(c)) return { ...byCode.get(c), origin: 'catalogue' };
  if (!CONFIG.openFoodFacts.enabled) return null;
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), CONFIG.openFoodFacts.timeoutMs);
    const url = `https://world.openfoodfacts.org/api/v2/product/${encodeURIComponent(code)}.json?fields=code,product_name,brands,quantity,product_quantity,product_quantity_unit,categories_tags,ecoscore_data`;
    const res = await fetch(url, { signal: ctrl.signal });
    clearTimeout(t);
    const j = await res.json();
    if (j.status !== 1 || !j.product) return null;
    const p = j.product, unit = (p.product_quantity_unit || 'g').toLowerCase();
    const grams = p.product_quantity ? Number(p.product_quantity) * (unit === 'kg' || unit === 'l' ? 1000 : 1) : null;
    return {
      code, name: p.product_name || 'Unnamed product', brand: (p.brands || '').split(',')[0], quantity: p.quantity || '',
      grams: Number.isFinite(grams) ? grams : null, cats: (p.categories_tags || []).filter(t => t.startsWith('en:')),
      agribalyseKgPerKg: p.ecoscore_data?.agribalyse?.co2_total ?? null, origin: 'openfoodfacts',
    };
  } catch { return null; } // offline, blocked, or timed out
}
