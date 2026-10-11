"""Request models. Strict: unknown fields refused, every number bounded, every string capped (ENGINEERING rule 3)."""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from carbonledger.agentsig import is_pubkey

UNITS_STATUS = "Simulated pilot units. Not verified credits."
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


class RetireIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    account: Literal["personal", "business"]
    grams: int = Field(gt=0, le=MAX_RETIRE_G)
    kind: Literal[KINDS]
    label: Literal[LABELS]
    note: Optional[str] = Field(default=None, max_length=120)     # hashed into the receipt, never stored or logged
    lines: List[Line] = Field(default_factory=list, max_length=200)
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
