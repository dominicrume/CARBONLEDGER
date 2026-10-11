"""Server recomputation of a retire request's footprint from its typed items (D1, T7). The browser total is a
preview. The server computes its own total with the same tables and refuses a request that claims less."""
from typing import List, Optional, Tuple

from carbonledger import activities as A
from carbonledger.estimate import estimate_product

from .lookup import ProductLookup


class RecomputeError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def _product(item, lookup: ProductLookup) -> int:
    facts: Optional[dict] = None
    if item.code:
        facts = lookup(item.code)
    if facts is None:
        if not item.groupId:
            raise RecomputeError("UNKNOWN_PRODUCT", f"barcode {item.code or '(none)'} is not known to the server and no category was chosen")
        facts = {"name": "category estimate", "groupId": item.groupId, "grams": item.packGrams, "hint": "", "cats": []}
    est = estimate_product(facts)
    return est["grams"] * item.qty


def compute(items, lookup: ProductLookup) -> Tuple[int, List[dict]]:
    """Returns (total grams, breakdown). Raises RecomputeError for an item the server cannot price."""
    total, breakdown = 0, []
    for it in items:
        t = it.type
        if t == "product":
            g = _product(it, lookup)
        elif t == "flight":
            r = A.flight_grams(it.from_, it.to, it.cabin, it.ret, it.people)
            if r is None:
                raise RecomputeError("BAD_FLIGHT", "unknown airport pair or cabin")
            g = r["grams"]
        elif t == "ground":
            r = A.ground_grams(it.mode, it.km, it.people)
            if r is None:
                raise RecomputeError("BAD_GROUND", "unknown mode or zero distance")
            g = r["grams"]
        elif t == "energy":
            g = A.business_energy_grams(it.electricityKwh, it.gasKwh)
        elif t == "meal":
            r = A.meal_grams(it.meal, it.n)
            if r is None:
                raise RecomputeError("BAD_MEAL", "unknown meal or zero count")
            g = r["grams"]
        elif t == "fleet":
            g = A.business_fleet_grams(it.fuel, it.km)
        elif t == "business_flights":
            g = A.business_flight_grams(it.band, it.n)
        elif t == "commute":
            g = A.commute_grams(it.mode, it.km, it.days, it.employees)
        elif t == "products_sold":
            g = A.products_sold_grams(it.gPerUnit, it.n)
        elif t == "measured":
            g = A.measured_grams(it.kg)
        elif t == "partner":
            p = A.partner_grams(it.id)
            if p is None:
                raise RecomputeError("UNKNOWN_PARTNER", it.id)
            g = p
        else:  # pragma: no cover  the model forbids other types
            raise RecomputeError("BAD_ITEM", t)
        total += g
        breakdown.append({"type": t, "grams": g})
    return total, breakdown
