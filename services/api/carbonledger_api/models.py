"""Request models. Strict: unknown fields refused, every number bounded, every string capped (ENGINEERING rule 3)."""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

UNITS_STATUS = "Simulated pilot units. Not verified credits."
MAX_RETIRE_G = 10**12                  # ASSUMPTION: a request above 1,000,000 tonnes is a mistake or an attack
STATUS_FOR = {"UNAUTHORISED": 403, "OVER_RETIREMENT": 409, "OVER_ISSUANCE": 409, "SUSPENDED": 409,
              "UNKNOWN_BATCH": 404, "UNKNOWN_PROJECT": 404, "BAD_AMOUNT": 422, "DUPLICATE_LINK": 409, "EXISTS": 409, "NOT_ATTESTED": 409}


class Line(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(max_length=80)
    grams: int = Field(ge=0, le=MAX_RETIRE_G)


class RetireIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    account: Literal["personal", "business"]
    grams: int = Field(gt=0, le=MAX_RETIRE_G)
    kind: str = Field(max_length=24)
    label: str = Field(max_length=120)
    lines: List[Line] = Field(default_factory=list, max_length=200)
    target_iso3: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    idempotency_key: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    mandate_id: Optional[str] = Field(default=None, max_length=64)
    agent: Optional[str] = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def lines_add_up(self):
        # A client cannot retire less than its own lines say (first step of D1).
        if self.lines and sum(l.grams for l in self.lines) != self.grams:
            raise ValueError("the line grams do not add up to the total; nothing was recorded")
        return self


class MandateIn(BaseModel):
    """The owner is the caller's key, never a field: a stranger cannot write a mandate in someone else's name."""
    model_config = ConfigDict(extra="forbid", strict=True)
    agent: str = Field(min_length=1, max_length=64)
    cap_g: int = Field(gt=0, le=MAX_RETIRE_G)
    ttl_seconds: int = Field(gt=0, le=31_536_000)
    allow_projects: Optional[List[str]] = Field(default=None, max_length=50)
