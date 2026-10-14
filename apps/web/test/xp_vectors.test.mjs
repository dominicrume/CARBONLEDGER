// The browser's XP rules and the server's (services/api/carbonledger_api/xp.py) pass the same vectors.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { sizeXP, xpOf } from '../js/core/xp.js';

const V = JSON.parse(readFileSync(new URL('../../../conformance/xp_vectors.json', import.meta.url)));
test('size XP matches the shared vectors', () => { for (const [g, want] of V.size) assert.equal(sizeXP(g), want, `${g} g`); });
test('history XP matches the shared vectors', () => { for (const h of V.histories) assert.equal(xpOf(h.records).total, h.total, h.name); });
