// Serials are grams, numbered from 0 within a batch; a retirement holds the range [start, end).
// Evidence (video, satellite, the verifier's visit) happens per tonne, never per gram, so a retirement is shown as a
// share of the pilot tonne it came from. Tonnes are counted from 1 for people: grams 0 to 999,999 are pilot tonne 1.
// Integers only: grams are never floats (CLAUDE.md), and the share is computed in hundredths of a percent.
export const G_PER_TONNE = 1_000_000;

export function tonneShares(start, end) {
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 || end <= start) return [];
  const out = [];
  for (let t = Math.floor(start / G_PER_TONNE); t * G_PER_TONNE < end; t++) {
    const lo = Math.max(start, t * G_PER_TONNE), hi = Math.min(end, (t + 1) * G_PER_TONNE);
    out.push({ tonne: t + 1, first: lo - t * G_PER_TONNE, last: hi - 1 - t * G_PER_TONNE, grams: hi - lo });
  }
  return out;
}

// grams of one tonne as a percentage with two decimals, from integers: 4,519 g -> "0.45%", a whole tonne -> "100%"
export function shareOfTonne(grams) {
  const h = Math.floor(grams / 100);            // hundredths of a percent, since 1 t = 1,000,000 g
  if (h === 0) return 'under 0.01%';
  if (h === 10000) return '100%';
  return `${Math.floor(h / 100)}.${String(h % 100).padStart(2, '0')}%`;
}

const n = v => v.toLocaleString('en-GB');
// "pilot tonne 12 (grams 712,279 to 716,797 of it, 0.45%)"; a range across tonnes names each, up to three
export function tonneText(start, end) {
  const s = tonneShares(start, end);
  if (!s.length) return '';
  const one = x => `pilot tonne ${n(x.tonne)} (grams ${n(x.first)} to ${n(x.last)} of it, ${shareOfTonne(x.grams)})`;
  if (s.length <= 3) return s.map(one).join(', and ');
  return `pilot tonnes ${n(s[0].tonne)} to ${n(s.at(-1).tonne)} (${s.length} tonnes)`;
}

// The short form for a receipt line: "pilot tonne 12, 0.45% of it", or "pilot tonnes 12 and 13" across a boundary
export function tonneShort(start, end) {
  const s = tonneShares(start, end);
  if (!s.length) return '';
  if (s.length === 1) return `pilot tonne ${n(s[0].tonne)}, ${shareOfTonne(s[0].grams)} of it`;
  return `pilot tonnes ${n(s[0].tonne)} ${s.length === 2 ? 'and' : 'to'} ${n(s.at(-1).tonne)}`;
}
