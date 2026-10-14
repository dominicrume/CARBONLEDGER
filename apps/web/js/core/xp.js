// XP pays for actions and habits, never for emitting more. Grams stay the shared total (the world clock, the
// country queue, the gram badges); personal XP is a separate score so a long-haul flight cannot out-level a careful
// month. Rules, all from the account's own history, oldest first:
//   - each retirement: a size score that grows with the logarithm of its grams, from 5 to 150 XP
//   - only the first DAILY_COUNTED retirements of a UTC day score, so splitting one basket into many earns nothing
//   - +100 for the first retirement of each week (the habit), +40 for each new kind of action that week (variety)
// Integers only. The same history always gives the same XP. Every input is on the server's receipt (kind, grams,
// time), so the server's leaderboard (carbonledger_api/xp.py) can check it: no bonus rests on a browser's word.
export const DAILY_COUNTED = 5, WEEK_XP = 100, KIND_XP = 40, LEVEL_BASE_XP = 80;

// 1 g -> 5, 10 g -> 25, 1 kg -> 75, 10 kg -> 100, 100 kg -> 125, 1 t and above -> 150
export function sizeXP(grams) {
  if (!(grams > 0)) return 0;
  return Math.max(5, Math.min(150, Math.round(25 * Math.log10(grams))));
}

const day = ts => String(ts).slice(0, 10);
function week(ts) { const d = new Date(ts); d.setUTCHours(0, 0, 0, 0); d.setUTCDate(d.getUTCDate() - d.getUTCDay()); return d.toISOString().slice(0, 10); }

// Total XP of a history, and what each record earned (by id), for receipts and the reward moment.
export function xpOf(history) {
  const rs = [...history].sort((a, b) => String(a.ts).localeCompare(String(b.ts)));
  const perDay = new Map(), weeks = new Map(), each = new Map();
  let total = 0;
  for (const r of rs) {
    const d = day(r.ts), w = week(r.ts), n = (perDay.get(d) || 0) + 1;
    perDay.set(d, n);
    let x = n <= DAILY_COUNTED ? sizeXP(r.grams) : 0;
    if (!weeks.has(w)) { weeks.set(w, new Set()); x += WEEK_XP; }
    const kinds = weeks.get(w);
    if (r.kind && !kinds.has(r.kind)) { kinds.add(r.kind); x += KIND_XP; }
    each.set(r.id, x); total += x;
  }
  return { total, each };
}

// What one more retirement would add right now, for the "+N XP" on a retire button.
export function previewXP(history, { grams, kind, ts = new Date().toISOString() }) {
  return xpOf([...history, { id: '__preview', ts, grams, kind }]).total - xpOf(history).total;
}
