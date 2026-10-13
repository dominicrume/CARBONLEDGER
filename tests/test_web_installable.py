"""The app installs as a phone app (Solana dApp Store via a Trusted Web Activity, docs/SEEKER-DAPP-STORE.md):
a valid manifest, a service worker that never serves the ledger from a cache, and pages whose policy allows both."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"


def test_manifest_has_what_an_installable_app_needs():
    m = json.loads((WEB / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert m["name"] == "CarbonLedger" and m["display"] == "standalone" and m["start_url"].startswith("/app")
    assert "not yet verified credits" in m["description"]
    sizes = {(i["sizes"], i.get("purpose", "any")) for i in m["icons"]}
    assert ("192x192", "any") in sizes and ("512x512", "any") in sizes and ("512x512", "maskable") in sizes
    for i in m["icons"]:
        assert (WEB / i["src"].lstrip("/")).is_file(), i["src"]


def test_service_worker_never_caches_the_ledger():
    sw = (WEB / "sw.js").read_text(encoding="utf-8")
    assert "url.pathname.startsWith('/v1/') || url.pathname === '/health') return;" in sw
    assert "e.request.method !== 'GET'" in sw                      # writes always go to the network
    assert "fetch(e.request).then(" in sw                          # network first: a deploy shows at once


def test_both_pages_link_the_manifest_and_allow_it():
    for page in ["index.html", "landing.html"]:
        html = (WEB / page).read_text(encoding="utf-8")
        assert '<link rel="manifest" href="/manifest.webmanifest">' in html, page
        csp = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', html).group(1)
        assert "manifest-src 'self'" in csp and "worker-src 'self'" in csp, page


def test_the_api_serves_the_manifest_with_its_type(monkeypatch):
    from test_api import make
    monkeypatch.setenv("WEB_DIR", str(WEB))
    c = make()
    r = c.get("/manifest.webmanifest")
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/manifest+json")
    assert c.get("/sw.js").status_code == 200
