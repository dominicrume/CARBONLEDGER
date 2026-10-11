// Safe wrapper around browser storage. Falls back to memory when storage is blocked.
const mem = {};
const PREFIX = 'carbonledger.';
export const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem(PREFIX + key); if (v !== null) return JSON.parse(v); } catch {}
    return key in mem ? mem[key] : fallback;
  },
  set(key, value) {
    mem[key] = value;
    try { localStorage.setItem(PREFIX + key, JSON.stringify(value)); } catch {}
  },
};
