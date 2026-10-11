"""The server estimator must reproduce every golden vector recorded from the web app's own code."""
import json
from pathlib import Path
import pytest
from carbonledger.estimate import estimate_product

VECTORS = json.loads((Path(__file__).resolve().parents[1] / "conformance" / "estimate_vectors.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("v", VECTORS, ids=[v["product"]["name"] for v in VECTORS])
def test_matches_the_app(v):
    assert estimate_product(v["product"]) == v["expected"]


def test_all_three_tiers_are_covered():
    assert {v["expected"]["tier"] for v in VECTORS} == {1, 2, 4}


def test_estimates_err_high_when_unsure():
    # an unknown pack weight assumes 1000 g, on purpose
    assert estimate_product({"name": "x", "hint": "beef"})["grams"] > estimate_product({"name": "x", "grams": 100, "hint": "beef"})["grams"]
