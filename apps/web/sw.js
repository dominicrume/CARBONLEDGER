// Service worker: the app opens offline and installs as a phone app (Solana dApp Store via a Trusted Web Activity).
// Rules: the ledger is never cached. /v1/ and /health always go to the network, so nothing is ever shown as recorded
// from a stale copy (CLAUDE.md: a chain that cannot be reached records nothing). Pages and assets are network-first,
// so a deploy shows at once; the cached copy is used only when the network is down.
const CACHE = 'carbonledger-shell-v1';
const SHELL = ['/app', '/', '/css/app.css', '/css/landing.css', '/js/main.js', '/js/landing.js', '/manifest.webmanifest', '/brand/mark-192.png', '/brand/mark-dark-128.png'];

self.addEventListener('install', (e) => {          // one missing file never blocks the install
  e.waitUntil(caches.open(CACHE).then(c => Promise.allSettled(SHELL.map(u => c.add(u)))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;            // writes and other sites: untouched
  if (url.pathname.startsWith('/v1/') || url.pathname === '/health') return;            // the ledger: never from a cache
  e.respondWith(fetch(e.request).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
    return res;
  }).catch(() => caches.match(e.request).then(hit => hit || (e.request.mode === 'navigate' ? caches.match('/app') : Response.error()))));
});
