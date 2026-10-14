import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sizeXP, xpOf, previewXP, DAILY_COUNTED } from '../js/core/xp.js';

const r = (id, ts, grams, kind = 'shop', mode = 'chosen') => ({ id, ts, grams, kind, mode });

test('size grows with the logarithm of grams and is capped both ways', () => {
  assert.deepEqual([1, 10, 1000, 10_000, 100_000, 1_000_000, 50_000_000].map(sizeXP), [5, 25, 75, 100, 125, 150, 150]);
  assert.equal(sizeXP(0), 0);
});

test('a long-haul flight cannot out-score a careful month of habits', () => {
  const flight = xpOf([r('f', '2026-10-05T10:00:00Z', 2_500_000, 'travel')]).total;
  const month = xpOf([0, 7, 14, 21].flatMap((d, i) => [
    r(`s${i}`, new Date(Date.UTC(2026, 9, 4 + d, 9)).toISOString(), 2_500, 'shop', 'frontline'),
    r(`d${i}`, new Date(Date.UTC(2026, 9, 5 + d, 19)).toISOString(), 4_000, 'daily')])).total;
  assert.ok(flight < 400, `flight ${flight}`);
  assert.ok(month > 4 * flight, `month ${month} vs flight ${flight}`);
});

test('splitting one basket into many retirements in a day earns nothing extra after the daily limit', () => {
  const h = Array.from({ length: 20 }, (_, i) => r(`x${i}`, `2026-10-06T10:${String(i).padStart(2, '0')}:00Z`, 1));
  const { each } = xpOf(h);
  assert.equal([...each.values()].filter(v => v > 0).length, DAILY_COUNTED);
});

test('a week and a new kind of action each add a bonus once', () => {
  const h = [r('a', '2026-10-06T10:00:00Z', 1000, 'shop')];
  assert.equal(xpOf(h).total, 75 + 100 + 40);
  assert.equal(previewXP(h, { grams: 1000, kind: 'shop', ts: '2026-10-06T11:00:00Z' }), 75);
  assert.equal(previewXP(h, { grams: 1000, kind: 'travel', ts: '2026-10-06T11:00:00Z' }), 75 + 40);
});

test('the same history always gives the same XP, whatever order it arrives in', () => {
  const h = [r('a', '2026-10-06T10:00:00Z', 900), r('b', '2026-10-01T10:00:00Z', 50_000, 'travel'), r('c', '2026-10-06T12:00:00Z', 3)];
  assert.equal(xpOf(h).total, xpOf([...h].reverse()).total);
});
