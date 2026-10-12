"""Claims discipline on screen (rules/HARDENING-PRODUCT.md, DEBT D10). Pilot units are retired, never offset.
Scans the app's user-facing source with comments stripped. Data files and the map are excluded."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
BANNED = [r"\boffsets?\b", r"\boffsetting\b", r"carbon[ -]neutral", r"net[ -]zero", r"climate[ -]positive", r"verified credits?",
          r"permanently on", r"your exact footprint"]
ALLOWED = [r"not yet verified credits", r"not an offset", r"never \"offset\"", r"not verified credits", r"verified credits?\b.*\bnot\b", r"never offset", r"a verified credit until"]


def _user_facing_lines():
    files = [WEB / "index.html"] + [p for p in (WEB / "js").rglob("*.js") if "data" not in p.parts]
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            code = re.sub(r"(^|\s)//.*$", "", line)         # strip line comments
            if code.strip():
                yield f.relative_to(ROOT), n, code


def test_no_banned_claim_words_on_screen():
    bad = []
    for path, n, code in _user_facing_lines():
        for rx in BANNED:
            if re.search(rx, code, re.I) and not any(re.search(a, code, re.I) for a in ALLOWED):
                bad.append(f"{path}:{n}: {code.strip()[:100]}")
    assert not bad, "\n".join(bad)


def test_pilot_unit_tag_appears_beside_unit_counts():
    retire = (WEB / "js" / "ui" / "retire.js").read_text(encoding="utf-8")
    assert retire.count("SIM_TAG") >= 3
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "Pilot units" in retire and "not yet verified credits" in retire and "not yet verified credits" in html


def test_footer_credits_every_data_source():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    for src in ["Poore and Nemecek", "Agribalyse", "Open Food Facts", "Global Carbon Project", "Natural Earth", "DESNZ", "Verify a receipt"]:
        assert src in html, src
