"""KYA mandate: what an agent may retire on an owner's behalf. Cap, allow-list, expiry, revoke.
Same shape as the mandate in cantor8_kya_rails, so the controls read the same across chains."""
from dataclasses import dataclass
from typing import Optional, Tuple


class MandateError(ValueError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code


@dataclass
class Mandate:
    id: str
    owner: str
    agent: str
    cap_g: int
    expires_at: int                      # unix seconds
    allow_projects: Optional[Tuple[str, ...]] = None   # None means any project
    used_g: int = 0
    revoked: bool = False


def authorize(m: Mandate, agent: str, grams: int, project_id: str, now: int) -> None:
    """Raise MandateError unless the agent may retire this much from this project now. Changes nothing."""
    if not isinstance(grams, int) or isinstance(grams, bool) or grams <= 0:
        raise MandateError("BAD_AMOUNT")
    if m.revoked:
        raise MandateError("REVOKED")
    if now >= m.expires_at:
        raise MandateError("EXPIRED")
    if agent != m.agent:
        raise MandateError("WRONG_AGENT")
    if m.allow_projects is not None and project_id not in m.allow_projects:
        raise MandateError("PROJECT_NOT_ALLOWED")
    if m.used_g + grams > m.cap_g:
        raise MandateError("OVER_CAP")


def consume(m: Mandate, grams: int) -> None:
    m.used_g += grams


def revoke(m: Mandate, signer: str) -> None:
    if signer != m.owner:
        raise MandateError("UNAUTHORISED", "only the owner can revoke")
    m.revoked = True
