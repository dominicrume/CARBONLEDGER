// Settings a demo operator can change in the app. Defaults come from config.js.
import { CONFIG } from '../config.js';
import { store } from './store.js';

export const settings = {
  pricePerTonne: () => store.get('pricePerTonne', CONFIG.pricePerTonneGBP),
  setPricePerTonne(v) { if (Number.isFinite(v) && v > 0) store.set('pricePerTonne', Math.round(v * 100) / 100); },
  communityTonnes: () => store.get('communityTonnes', CONFIG.demoCommunityTonnes),
  setCommunityTonnes(v) { if (Number.isFinite(v) && v >= 0) store.set('communityTonnes', Math.round(v)); },
};
