"""Request models. Strict: unknown fields refused, every number bounded, every string capped (ENGINEERING rule 3)."""
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from carbonledger.agentsig import is_pubkey

UNITS_STATUS = "Pilot units. Not yet verified credits."
# Receipt labels are a closed vocabulary (D8, T18). Free text goes in `note`, which is hashed and never stored.
LABELS = ("Shopping basket", "Journey", "Everyday activities", "Business period", "Partner reward")
KINDS = ("shop", "travel", "daily", "business", "partner", "other")
MAX_RETIRE_G = 10**12                  # ASSUMPTION: a request above 1,000,000 tonnes is a mistake or an attack
STATUS_FOR = {"UNAUTHORISED": 403, "OVER_RETIREMENT": 409, "OVER_ISSUANCE": 409, "SUSPENDED": 409,
              "UNKNOWN_BATCH": 404, "UNKNOWN_PROJECT": 404, "BAD_AMOUNT": 422, "DUPLICATE_LINK": 409, "EXISTS": 409, "NOT_ATTESTED": 409}


class Line(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(max_length=80)
    grams: int = Field(ge=0, le=MAX_RETIRE_G)


# ---- Typed items: what the retirement is for, in a form the server can price itself (D1). ----
_B = ConfigDict(extra="forbid", strict=True)
_NUM = Annotated[Union[int, float], Field(ge=0, le=MAX_RETIRE_G)]


class ProductItem(BaseModel):
    model_config = _B
    type: Literal["product"]
    code: Optional[str] = Field(default=None, min_length=4, max_length=20, pattern=r"^[0-9]+$")
    groupId: Optional[str] = Field(default=None, max_length=24, pattern=r"^[a-z]+$")
    packGrams: Optional[_NUM] = None
    qty: int = Field(ge=1, le=1000)


class FlightItem(BaseModel):
    model_config = _B
    type: Literal["flight"]
    from_: str = Field(alias="from", min_length=3, max_length=3)
    to: str = Field(min_length=3, max_length=3)
    cabin: Literal["economy", "business"]
    ret: bool
    people: int = Field(ge=1, le=1000)


class GroundItem(BaseModel):
    model_config = _B
    type: Literal["ground"]
    mode: str = Field(max_length=16)
    km: _NUM
    people: int = Field(ge=1, le=100)


class EnergyItem(BaseModel):
    model_config = _B
    type: Literal["energy"]
    electricityKwh: _NUM
    gasKwh: _NUM


class MealItem(BaseModel):
    model_config = _B
    type: Literal["meal"]
    meal: str = Field(max_length=16)
    n: int = Field(ge=1, le=10000)


class FleetItem(BaseModel):
    model_config = _B
    type: Literal["fleet"]
    fuel: str = Field(max_length=16)
    km: _NUM


class BusinessFlightsItem(BaseModel):
    model_config = _B
    type: Literal["business_flights"]
    band: Literal["domestic", "short", "long"]
    n: int = Field(ge=0, le=100000)


class CommuteItem(BaseModel):
    model_config = _B
    type: Literal["commute"]
    mode: str = Field(max_length=16)
    km: _NUM
    days: int = Field(ge=0, le=366)
    employees: int = Field(ge=1, le=10**6)


class ProductsSoldItem(BaseModel):
    model_config = _B
    type: Literal["products_sold"]
    gPerUnit: _NUM
    n: int = Field(ge=0, le=MAX_RETIRE_G)


class MeasuredItem(BaseModel):
    model_config = _B
    type: Literal["measured"]
    kg: _NUM


class PartnerItem(BaseModel):
    model_config = _B
    type: Literal["partner"]
    id: str = Field(max_length=24)


Item = Annotated[Union[ProductItem, FlightItem, GroundItem, EnergyItem, MealItem, FleetItem, BusinessFlightsItem, CommuteItem,
                       ProductsSoldItem, MeasuredItem, PartnerItem], Field(discriminator="type")]


class RetireIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    account: Literal["personal", "business"]
    grams: int = Field(gt=0, le=MAX_RETIRE_G)
    kind: Literal[KINDS]
    label: Literal[LABELS]
    note: Optional[str] = Field(default=None, max_length=120)     # hashed into the receipt, never stored or logged
    lines: List[Line] = Field(default_factory=list, max_length=200)
    items: List[Item] = Field(min_length=1, max_length=200)       # what this retirement is for; the server prices these
    target_iso3: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    idempotency_key: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    mandate_id: Optional[str] = Field(default=None, max_length=64)
    agent: Optional[str] = Field(default=None, max_length=64)        # the agent's base58 ed25519 public key
    agent_ts: Optional[int] = Field(default=None, ge=0, le=10**11)     # unix seconds when the agent signed
    agent_sig: Optional[str] = Field(default=None, max_length=128)    # base58 ed25519 signature, see agentsig.py

    @model_validator(mode="after")
    def lines_add_up(self):
        # A client cannot retire less than its own lines say (first step of D1).
        if self.lines and sum(l.grams for l in self.lines) != self.grams:
            raise ValueError("the line grams do not add up to the total; nothing was recorded")
        return self


class MandateIn(BaseModel):
    """The owner is the caller's key, never a field: a stranger cannot write a mandate in someone else's name.
    The agent is a public key, never a name (KYA)."""
    model_config = ConfigDict(extra="forbid", strict=True)
    agent: str = Field(min_length=32, max_length=44)

    @field_validator("agent")
    @classmethod
    def agent_is_a_key(cls, v):
        if not is_pubkey(v):
            raise ValueError("agent must be a base58 ed25519 public key, not a name")
        return v
    cap_g: int = Field(gt=0, le=MAX_RETIRE_G)
    ttl_seconds: int = Field(gt=0, le=31_536_000)
    allow_projects: Optional[List[str]] = Field(default=None, max_length=50)
