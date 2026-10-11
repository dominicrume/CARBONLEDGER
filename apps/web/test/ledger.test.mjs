// Node's own test runner. No dependencies. Run: node --test apps/web/test/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SolanaLedger, ref } from '../js/core/ledger.js';

function fakeFetch(calls, { hang = false, status = 200 } = {}) {
  return async (url, opts) => {
    calls.push(JSON.parse(opts.body));
    if (hang) await new Promise((_, rej) => opts.signal.addEventListener('abort', () => { const e = new Error('aborted'); e.name = 'AbortError'; rej(e); }));
    return { ok: status === 200, status, json: async () => ({ receipt_id: 'CL-1', ts: 't', explorer_url: null, receipt_hash: 'h', serial_start: 0, serial_end: 1, signature: 's' }) };
  };
}

test('two calls for the same intent send the same idempotency key', async () => {
  const calls = [];
  globalThis.fetch = fakeFetch(calls);
  const l = new SolanaLedger();
  const intent = { grams: 1, kind: 'shop', label: 'Shopping basket', lines: [], idempotencyKey: ref() };
  await l.retire(intent); await l.retire(intent);
  assert.equal(calls.length, 2);
  assert.equal(calls[0].idempotency_key, calls[1].idempotency_key);
  assert.match(calls[0].idempotency_key, /^CL-[0-9A-F]{16}$/);
});

test('without a caller key, each call gets its own key (local demo only)', async () => {
  const calls = [];
  globalThis.fetch = fakeFetch(calls);
  const l = new SolanaLedger();
  await l.retire({ grams: 1, kind: 'shop', label: 'x', lines: [] }); await l.retire({ grams: 1, kind: 'shop', label: 'x', lines: [] });
  assert.notEqual(calls[0].idempotency_key, calls[1].idempotency_key);
});

test('a timeout never claims that nothing was recorded', async () => {
  const calls = [];
  globalThis.fetch = fakeFetch(calls, { hang: true });
  const { CONFIG } = await import('../js/config.js');
  const saved = CONFIG.api.timeoutMs; CONFIG.api.timeoutMs = 20;
  try {
    await assert.rejects(new SolanaLedger().retire({ grams: 1, kind: 'shop', label: 'x', lines: [] }), /could not confirm whether this was recorded/);
  } finally { CONFIG.api.timeoutMs = saved; }
});

test('a server refusal is passed through word for word', async () => {
  globalThis.fetch = async () => ({ ok: false, status: 409, json: async () => ({ detail: 'Not enough pilot units left.' }) });
  await assert.rejects(new SolanaLedger().retire({ grams: 1, kind: 'shop', label: 'x', lines: [] }), /Not enough pilot units left\./);
});
