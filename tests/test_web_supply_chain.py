"""Supply chain for the browser (D7, T17): no remote script, every vendored script pinned with a matching
integrity hash, and a Content-Security-Policy that allows scripts only from the app's own origin."""
import base64
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
HTML = (WEB / "index.html").read_text(encoding="utf-8")


def _scripts():
    return re.findall(r'<script\b([^>]*)>', HTML)


def test_no_script_loads_from_a_remote_host():
    for attrs in _scripts():
        src = re.search(r'src="([^"]+)"', attrs)
        assert src and not src.group(1).startswith(("http:", "https:", "//")), attrs


def test_every_vendored_script_has_the_right_integrity_hash():
    seen = 0
    for attrs in _scripts():
        src = re.search(r'src="([^"]+)"', attrs).group(1)
        if not src.startswith("vendor/"):
            continue
        seen += 1
        integrity = re.search(r'integrity="sha384-([^"]+)"', attrs)
        assert integrity, f"{src} has no integrity attribute"
        digest = base64.b64encode(hashlib.sha384((WEB / src).read_bytes()).digest()).decode()
        assert integrity.group(1) == digest, f"{src}: integrity does not match the file"
        assert 'crossorigin="anonymous"' in attrs
    assert seen == 3


def test_vendored_versions_are_pinned_in_the_file_names():
    names = sorted(p.name for p in (WEB / "vendor").glob("*.js"))
    assert names == ["d3-7.9.0.min.js", "topojson-client-3.1.0.min.js", "zxing-library-0.21.3.umd.min.js"]


def test_content_security_policy_allows_scripts_from_self_only():
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"', HTML)
    assert m, "no CSP meta tag"
    csp = {d.split()[0]: d.split()[1:] for d in m.group(1).split(";") if d.strip()}
    assert csp["default-src"] == ["'none'"] and csp["script-src"] == ["'self'"] and csp["object-src"] == ["'none'"]
    assert "'unsafe-inline'" not in csp["script-src"] and "'unsafe-eval'" not in csp["script-src"]
    assert "https://world.openfoodfacts.org" in csp["connect-src"] and csp["base-uri"] == ["'none'"]


def test_landing_page_loads_no_remote_script_and_keeps_its_policy():
    html = (WEB / "landing.html").read_text(encoding="utf-8")
    for attrs in re.findall(r'<script\b([^>]*)>', html):
        src = re.search(r'src="([^"]+)"', attrs)
        assert src and not src.group(1).startswith(("http:", "https:", "//")), attrs
    csp = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', html).group(1)
    assert "script-src 'self'" in csp and "connect-src 'self'" in csp and "unsafe-eval" not in csp
