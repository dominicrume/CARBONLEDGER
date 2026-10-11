"""Server-side estimator. A faithful port of the app's tiered estimator (apps/web/js/core/estimate.js).
Rule: numbers come only from the factor tables. A model may suggest a category, never a figure.
Tests replay 133 golden vectors recorded from the app's own code."""
import json
import math
import re
from pathlib import Path

_D = json.loads((Path(__file__).parent / "data_factors.json").read_text(encoding="utf-8"))
_RULES = [(re.compile(r["src"]), r["key"], r["x"]) for r in _D["FOOD_RULES"]]
_GROUP_RULES = [(re.compile(r["src"]), r["id"]) for r in _D["GROUP_RULES"]]
_SKIP = re.compile(_D["AGRIBALYSE_SKIP"]["src"])
_UNKNOWN_G = _D["CONFIG"]["unknownWeightGrams"]
_UPLIFT = _D["CONFIG"]["estimateUplift"]
_MAX_AGRI = _D["CONFIG"]["maxAgribalyseKgPerKg"]
TIERS = {1: "International study", 2: "National database", 3: "Recognised organisation", 4: "Estimate, rounded up"}


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _num(x) -> str:
    """Print a number the way JavaScript does (2.0 prints as 2)."""
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def _match_food(text: str):
    for rx, key, x in _RULES:
        if rx.search(text):
            mult = x or 1
            return {"key": key, "kg_per_kg": _D["FOOD_FACTORS"][key] * mult, "x": mult}
    return None


def guess_group(product: dict) -> str:
    text = " ".join([product.get("hint") or "", *(product.get("cats") or [])])
    for rx, gid in _GROUP_RULES:
        if rx.search(text):
            return gid
    return "food"


def estimate_product(product: dict) -> dict:
    # Numbers from outside are untrusted. Anything that is not a sane positive number is ignored.
    g = product.get("grams")
    grams_in = g if _is_num(g) and g > 0 else None
    a = product.get("agribalyseKgPerKg")
    agri_ok = _is_num(a) and 0 < a <= _MAX_AGRI
    weight_kg = (grams_in or _UNKNOWN_G) / 1000
    weight_note = "" if grams_in else f" (pack weight unknown, {_UNKNOWN_G} g assumed)"
    candidates = []
    if not product.get("groupId"):
        m = _match_food(product.get("hint") or "") or _match_food(" ".join(product.get("cats") or []))
        if m:
            extra = f" (×{_num(m['x'])} for concentrate)" if m["x"] > 1 else ""
            candidates.append({"tier": 1, "kg": m["kg_per_kg"] * weight_kg, "source": _D["PN_SOURCE"],
                               "detail": f"{m['key']} {m['kg_per_kg']:.2f} kg CO₂e per kg{extra}{weight_note}"})
        prepared = bool(_SKIP.search(" ".join([product.get("hint") or "", *(product.get("cats") or [])])))
        agri = a
        if agri_ok and not prepared:
            candidates.append({"tier": 2, "kg": agri * weight_kg,
                               "source": "Agribalyse (French government environmental database)",
                               "detail": f"{agri:.2f} kg CO₂e per kg{weight_note}"})
    best = sorted(candidates, key=lambda c: c["kg"], reverse=True)[0] if candidates else None
    if best is None:
        gid = product.get("groupId") or guess_group(product)
        groups = _D["ESTIMATE_GROUPS"]
        g = next((x for x in groups if x["id"] == gid), groups[-1])
        base = g["perItem"] if g.get("perItem") else g["perKg"] * weight_kg
        margin = math.floor((_UPLIFT - 1) * 100 + 0.5)
        basis = f"{_num(g['perItem'])} kg per item" if g.get("perItem") else f"{_num(g['perKg'])} kg per kg{weight_note}"
        best = {"tier": 4, "kg": base * _UPLIFT, "source": "CarbonLedger category estimate",
                "detail": f"{g['label']}: {basis}, plus {margin}% margin"}
    return {"grams": math.ceil(best["kg"] * 1000), "tier": best["tier"], "source": best["source"],
            "detail": best["detail"], "alternatives": len(candidates)}
