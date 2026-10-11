from decimal import Decimal
import pytest
from carbonledger.units import UnitError, grams_to_clt, price_gbp


def test_clt_is_six_decimals_of_a_tonne():
    assert grams_to_clt(1) == "0.000001"
    assert grams_to_clt(1_000_000) == "1.000000"
    assert grams_to_clt(2_500_001) == "2.500001"


def test_price_matches_the_app_rule():
    assert price_gbp(1_000_000, "250") == Decimal("250.00")
    assert price_gbp(1, "250") == Decimal("0.01")          # at least a penny
    assert price_gbp(120, "250") == Decimal("0.03")


def test_bad_values_fail_loud():
    for bad in (-1, 1.5, True, "5"):
        with pytest.raises(UnitError):
            grams_to_clt(bad)
    with pytest.raises(UnitError):
        price_gbp(0, "250")
    with pytest.raises(UnitError):
        price_gbp(10, "0")
