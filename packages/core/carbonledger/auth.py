"""API keys and rate limits (D2, T12). A key is a login, like a password: it signs nothing and decides nothing.
The server stores only a salted hash (sha256 of pepper plus key). The plaintext is shown once, at creation.
Roles: personal, business, agent, verifier, authority. Every write endpoint needs a key. Reads stay public, because
anyone must be able to verify a receipt."""
import hashlib
import hmac
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional

ROLES = ("personal", "business", "agent", "verifier", "authority")


class AuthError(ValueError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code


@dataclass
class KeyRecord:
    key_id: str
    role: str
    owner: str
    key_hash: str
    revoked: bool = False


def hash_key(pepper: str, key: str) -> str:
    return hashlib.sha256((pepper + key).encode("utf-8")).hexdigest()


class ApiKeyStore:
    def __init__(self, pepper: str):
        if not pepper or len(pepper) < 16:
            raise AuthError("BAD_PEPPER", "API_KEY_PEPPER must be at least 16 characters")
        self.pepper = pepper
        self._by_hash: Dict[str, KeyRecord] = {}
        self._lock = threading.Lock()

    def issue(self, role: str, owner: str) -> tuple[str, KeyRecord]:
        """Make a new key. Returns the plaintext ONCE and the record. The plaintext is never stored."""
        if role not in ROLES:
            raise AuthError("BAD_ROLE", role)
        if not owner or len(owner) > 64:
            raise AuthError("BAD_OWNER")
        key = f"clk_{role}_{secrets.token_hex(24)}"
        rec = KeyRecord("key-" + secrets.token_hex(6), role, owner, hash_key(self.pepper, key))
        with self._lock:
            self._by_hash[rec.key_hash] = rec
        return key, rec

    def add_hashed(self, role: str, owner: str, key_hash: str, key_id: Optional[str] = None) -> KeyRecord:
        """Load a key whose hash was made elsewhere (scripts/make_api_key.py, the database, the environment)."""
        if role not in ROLES:
            raise AuthError("BAD_ROLE", role)
        rec = KeyRecord(key_id or ("key-" + key_hash[:12]), role, owner, key_hash)
        with self._lock:
            self._by_hash[key_hash] = rec
        return rec

    def check(self, key: Optional[str]) -> KeyRecord:
        if not key:
            raise AuthError("NO_KEY", "send Authorization: Bearer <api key>")
        h = hash_key(self.pepper, key)
        with self._lock:
            rec = self._by_hash.get(h)
        # constant-time compare on the hash, so timing tells an attacker nothing about near misses
        if rec is None or not hmac.compare_digest(rec.key_hash, h):
            raise AuthError("BAD_KEY", "this key is not known")
        if rec.revoked:
            raise AuthError("REVOKED_KEY", "this key was revoked")
        return rec

    def revoke(self, key_id: str) -> bool:
        with self._lock:
            for rec in self._by_hash.values():
                if rec.key_id == key_id:
                    rec.revoked = True
                    return True
        return False

    def count(self) -> int:
        with self._lock:
            return len(self._by_hash)


class TokenBucket:
    """Per-key token bucket. `per_minute` tokens refill a minute, up to `burst` held at once."""
    def __init__(self, per_minute: int, burst: int, now: Callable[[], float] = time.monotonic):
        if per_minute <= 0 or burst <= 0:
            raise AuthError("BAD_LIMIT")
        self.rate, self.burst, self.now = per_minute / 60.0, float(burst), now
        self._state: Dict[str, tuple[float, float]] = {}       # key id -> (tokens, last)
        self._lock = threading.Lock()

    def take(self, key_id: str) -> bool:
        t = self.now()
        with self._lock:
            tokens, last = self._state.get(key_id, (self.burst, t))
            tokens = min(self.burst, tokens + (t - last) * self.rate)
            if tokens < 1.0:
                self._state[key_id] = (tokens, t)
                return False
            self._state[key_id] = (tokens - 1.0, t)
            return True
