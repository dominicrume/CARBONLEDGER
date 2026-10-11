"""The server activity functions must reproduce every golden vector recorded from the app's own code (D1)."""
import json
from pathlib import Path
import pytest
from carbonledger import activities as A

VECTORS = json.loads((Path(__file__).resolve().parents[1] / "conformance" / "activity_vectors.json").read_text(encoding="utf-8"))
CALL = {
    "flight": lambda i: A.flight_grams(i["from"], i["to"], i["cabin"], i["ret"], i["people"]),
    "ground": lambda i: A.ground_grams(i["mode"], i["km"], i["people"]),
    "energy": lambda i: A.energy_grams(i["electricityKwh"], i["gasKwh"]),
    "meal": lambda i: A.meal_grams(i["meal"], i["n"]),
    "fleet": lambda i: A.business_fleet_grams(i["fuel"], i["km"]),
    "business_flights": lambda i: A.business_flight_grams(i["band"], i["n"]),
    "commute": lambda i: A.commute_grams(i["mode"], i["km"], i["days"], i["employees"]),
    "products_sold": lambda i: A.products_sold_grams(i["gPerUnit"], i["n"]),
    "measured": lambda i: A.measured_grams(i["kg"]),
}


@pytest.mark.parametrize("v", VECTORS, ids=[f"{v['fn']}-{n}" for n, v in enumerate(VECTORS)])
def test_matches_the_app(v):
    assert CALL[v["fn"]](v["in"]) == v["out"]


def test_every_function_is_covered():
    assert {v["fn"] for v in VECTORS} == set(CALL)


def test_partner_rewards_come_from_the_table():
    assert A.partner_grams("search") == 120 and A.partner_grams("nope") is None
