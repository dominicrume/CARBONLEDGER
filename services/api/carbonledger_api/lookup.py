"""Product facts for server-side recomputation (D1). Order: the exported catalogue, then Open Food Facts over the
network when allowed. Outside numbers are untrusted: the estimator bounds them. Results are cached per process."""
import json
import os
import threading
from pathlib import Path
from typing import Callable, Dict, Optional

CATALOGUE_PATH = Path(__file__).resolve().parents[3] / "packages" / "core" / "carbonledger" / "data_products.json"
_CATALOGUE: Dict[str, dict] = {p["code"]: p for p in json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))}
OFF_URL = "https://world.openfoodfacts.org/api/v2/product/{code}.json?fields=code,product_name,quantity,product_quantity,product_quantity_unit,categories_tags,ecoscore_data"

ProductLookup = Callable[[str], Optional[dict]]


def _variants(code: str):
    return [code, code.lstrip("0"), code.zfill(13)]


def catalogue_lookup(code: str) -> Optional[dict]:
    for c in _variants(code):
        p = _CATALOGUE.get(c)
        if p:
            return {"name": p["name"], "grams": p.get("grams"), "cats": p.get("cats") or [], "hint": p.get("hint") or "",
                    "agribalyseKgPerKg": p.get("agribalyseKgPerKg"), "origin": "catalogue"}
    return None


class OpenFoodFactsLookup:
    """Live lookup, used only when OPEN_FOOD_FACTS_ENABLED is not "0". The same fields the app reads."""
    def __init__(self, user_agent: str, timeout: float = 4.0):
        self.user_agent, self.timeout, self._cache, self._lock = user_agent, timeout, {}, threading.Lock()

    def __call__(self, code: str) -> Optional[dict]:
        with self._lock:
            if code in self._cache:
                return self._cache[code]
        facts = None
        try:
            import httpx
            r = httpx.get(OFF_URL.format(code=code), headers={"User-Agent": self.user_agent}, timeout=self.timeout)
            j = r.json() if r.status_code == 200 else {}
            p = j.get("product") if j.get("status") == 1 else None
            if p:
                unit = str(p.get("product_quantity_unit") or "g").lower()
                q = p.get("product_quantity")
                grams = float(q) * (1000 if unit in ("kg", "l") else 1) if isinstance(q, (int, float, str)) and str(q).replace(".", "", 1).isdigit() else None
                agri = ((p.get("ecoscore_data") or {}).get("agribalyse") or {}).get("co2_total")
                facts = {"name": p.get("product_name") or "Unnamed product", "grams": grams, "cats": [c for c in (p.get("categories_tags") or []) if str(c).startswith("en:")],
                         "hint": "", "agribalyseKgPerKg": agri, "origin": "openfoodfacts"}
        except Exception:  # noqa: BLE001  offline, blocked, timed out: the caller falls back
            facts = None
        with self._lock:
            self._cache[code] = facts
        return facts


def lookup_from_env() -> ProductLookup:
    off = None
    if os.environ.get("OPEN_FOOD_FACTS_ENABLED", "1") != "0":
        off = OpenFoodFactsLookup(os.environ.get("OPEN_FOOD_FACTS_USER_AGENT", "CarbonLedger/0.2 (dev)"))

    def lookup(code: str) -> Optional[dict]:
        return catalogue_lookup(code) or (off(code) if off else None)
    return lookup
