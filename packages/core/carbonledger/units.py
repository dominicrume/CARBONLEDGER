"""Units. 1 CLT = 1 tonne CO2e. Six decimals = whole grams. Integers for grams, Decimal for money. Never float for money."""
from decimal import Decimal, ROUND_HALF_UP

GRAMS_PER_TONNE = 1_000_000


class UnitError(ValueError):
    pass


def grams_to_clt(grams: int) -> str:
    if not isinstance(grams, int) or isinstance(grams, bool) or grams < 0:
        raise UnitError("grams must be a whole number, zero or more")
    whole, frac = divmod(grams, GRAMS_PER_TONNE)
    return f"{whole}.{frac:06d}"


def price_gbp(grams: int, price_per_tonne: str) -> Decimal:
    """Same rule as the app: at least one penny, rounded to the penny."""
    if not isinstance(grams, int) or grams <= 0:
        raise UnitError("grams must be a whole number above zero")
    rate = Decimal(price_per_tonne)
    if rate <= 0:
        raise UnitError("price per tonne must be above zero")
    raw = (Decimal(grams) / Decimal(GRAMS_PER_TONNE)) * rate
    return max(Decimal("0.01"), raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
