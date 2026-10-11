"""Server-side activity footprints: a faithful port of apps/web/js/core/activities.js over the same factor tables.
Golden vectors recorded from the app's own code must match exactly (tests/test_activity_parity.py).
Grams are whole numbers rounded up. Numbers come only from the tables. Nothing reads the clock or the network."""
import json
import math
from pathlib import Path
from typing import Optional

_D = json.loads((Path(__file__).parent / "data_activities.json").read_text(encoding="utf-8"))
FLIGHT, FLIGHT_UPLIFT, ENERGY, FLIGHT_KM = _D["FLIGHT"], _D["FLIGHT_UPLIFT"], _D["ENERGY"], _D["FLIGHT_KM"]
GROUND = {g["id"]: g for g in _D["GROUND"]}
MEALS = {m["id"]: m for m in _D["MEALS"]}
AIRPORTS = {a[0]: a for a in _D["AIRPORTS"]}
UK_AIRPORTS = set(_D["UK_AIRPORTS"])
PARTNERS = {p["id"]: p for p in _D["PARTNERS"]}
SHORT_HAUL_MAX_KM = _D["SHORT_HAUL_MAX_KM"]
TRAVEL_SOURCE = _D["TRAVEL_SOURCE"]


def _num(x) -> float:
    """JavaScript's `+x || 0` for the inputs we accept: numbers only, anything else is 0."""
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) else 0.0


def _js_num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else repr(float(v))


def km(a, b) -> float:
    R = 6371.0
    r = lambda d: d * math.pi / 180  # noqa: E731
    d_lat, d_lon = r(b[2] - a[2]), r(b[3] - a[3])
    h = math.sin(d_lat / 2) ** 2 + math.cos(r(a[2])) * math.cos(r(b[2])) * math.sin(d_lon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def flight_grams(from_: str, to: str, cabin: str, ret: bool, people) -> Optional[dict]:
    a, b = AIRPORTS.get(from_), AIRPORTS.get(to)
    if a is None or b is None or a is b or cabin not in FLIGHT["short"]:
        return None
    dist = km(a, b) * FLIGHT_UPLIFT
    band = "domestic" if (from_ in UK_AIRPORTS and to in UK_AIRPORTS) else ("short" if dist <= SHORT_HAUL_MAX_KM else "long")
    g = math.ceil(dist * FLIGHT[band][cabin] * 1000 * (2 if ret else 1) * _num(people))
    return {"grams": g, "dist": _js_round(dist), "band": band, "label": f"{a[1]} to {b[1]}{' and back' if ret else ''}"}


def _js_round(x: float) -> int:
    return math.floor(x + 0.5)


def ground_grams(mode: str, dist, people) -> Optional[dict]:
    g = GROUND.get(mode)
    d = _num(dist)
    if g is None or not d > 0:
        return None
    share = max(1.0, _num(people) or 1.0) if g.get("perVehicle") else 1.0
    return {"grams": math.ceil(d * g["perKm"] * 1000 / share), "label": f"{g['label']}, {_js_num(d)} km", "share": share}


def energy_grams(electricity_kwh, gas_kwh) -> list:
    lines = []
    e, g = max(0.0, _num(electricity_kwh)), max(0.0, _num(gas_kwh))
    if e:
        lines.append({"name": f"Electricity {_js_num(e)} kWh", "grams": math.ceil(e * ENERGY["electricity"] * 1000)})
    if g:
        lines.append({"name": f"Gas {_js_num(g)} kWh", "grams": math.ceil(g * ENERGY["gas"] * 1000)})
    return lines


def meal_grams(meal: str, n) -> Optional[dict]:
    m = MEALS.get(meal)
    k = _num(n)
    if m is None or not k > 0:
        return None
    return {"grams": math.ceil(k * m["kg"] * 1000), "label": f"{_js_num(k)} × {m['label']}"}


def business_fleet_grams(fuel: str, dist) -> int:
    f, d = GROUND.get(fuel), _num(dist)
    return math.ceil(d * f["perKm"] * 1000) if f and d > 0 else 0


def business_flight_grams(band: str, n) -> int:
    k = _num(n)
    return math.ceil(k * 2 * FLIGHT_KM[band] * FLIGHT_UPLIFT * FLIGHT[band]["economy"] * 1000) if band in FLIGHT_KM and k > 0 else 0


def commute_grams(mode: str, dist, days, employees) -> int:
    c, d, dy, emp = GROUND.get(mode), _num(dist), _num(days), _num(employees)
    return math.ceil(emp * d * dy * c["perKm"] * 1000) if c and d > 0 and dy > 0 and emp > 0 else 0


def products_sold_grams(g_per_unit, n) -> int:
    g, k = _num(g_per_unit), _num(n)
    return math.ceil(g * k) if g > 0 and k > 0 else 0


def measured_grams(kg) -> int:
    k = _num(kg)
    return math.ceil(k * 1000) if k > 0 else 0


def business_energy_grams(electricity_kwh, gas_kwh) -> int:
    return sum(l["grams"] for l in energy_grams(electricity_kwh, gas_kwh))


def partner_grams(partner_id: str) -> Optional[int]:
    p = PARTNERS.get(partner_id)
    return int(p["grams"]) if p else None
