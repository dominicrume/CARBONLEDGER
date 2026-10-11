// The shopping basket: scanned items with their estimated footprint.
import { store } from './store.js';
import { estimateProduct } from './estimate.js';

let items = store.get('basket', []);
const listeners = new Set();
const save = () => { store.set('basket', items); listeners.forEach(f => f(items)); };

export const basket = {
  items: () => items,
  onChange(f) { listeners.add(f); return () => listeners.delete(f); },
  add(product) {
    const est = estimateProduct(product);
    const existing = items.find(i => i.code === (product.code || null) && i.groupId === (product.groupId || null));
    if (existing && product.code) existing.qty += 1;
    else items.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2, 7), code: product.code || null, name: product.name, brand: product.brand || '',
      quantity: product.quantity || '', groupId: product.groupId || null, packGrams: typeof product.grams === 'number' && product.grams > 0 ? product.grams : null, qty: 1, est });
    save();
    return est;
  },
  setQty(id, qty) { const i = items.find(x => x.id === id); if (!i) return; if (qty <= 0) items = items.filter(x => x.id !== id); else i.qty = qty; save(); },
  clear() { items = []; save(); },
  totalGrams: () => items.reduce((s, i) => s + i.est.grams * i.qty, 0),
};
