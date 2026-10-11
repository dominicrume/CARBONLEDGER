"""Registry rules, as a reference model. The Anchor program (programs/carbon_registry) must pass the same
conformance vectors (conformance/registry_vectors.json). Integer grams only.

What this enforces, and why it is the heart of a single register:
  1. Nothing is issued unless a verifier attested the project (no issuance on a promise).
  2. Issued grams never exceed attested grams.
  3. Every retirement takes a fresh serial range, so a gram can never be retired twice.
  4. An external credit (registry name plus serial) can be linked once, ever: no double counting.
  5. A suspended project can issue and retire nothing."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


class InvariantError(AssertionError):
    """A registry rule is broken in stored state. Raised explicitly, never by `assert`, so the check survives
    python -O (bandit B101) and the nightly recheck can never be blinded by a flag."""


class RegistryError(ValueError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code


@dataclass
class Project:
    id: str
    country_iso3: str
    methodology: str
    status: str = "proposed"          # proposed | attested | suspended
    attested_g: int = 0
    issued_g: int = 0


@dataclass
class Batch:
    id: str
    project_id: str
    vintage: int
    issued_g: int
    retired_g: int = 0
    next_serial: int = 0


@dataclass(frozen=True)
class Retirement:
    receipt_no: int
    batch_id: str
    retiree: str
    grams: int
    serial_start: int
    serial_end: int
    target_iso3: Optional[str]
    memo_hash: str


@dataclass
class Registry:
    authority: str
    verifiers: Set[str]
    projects: Dict[str, Project] = field(default_factory=dict)
    batches: Dict[str, Batch] = field(default_factory=dict)
    links: Set[Tuple[str, str]] = field(default_factory=set)
    retirements: List[Retirement] = field(default_factory=list)

    # -- helpers
    def _need_authority(self, signer: str) -> None:
        if signer != self.authority:
            raise RegistryError("UNAUTHORISED", "only the registry authority can do this")

    @staticmethod
    def _positive(n: int, what: str) -> None:
        if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
            raise RegistryError("BAD_AMOUNT", f"{what} must be a whole number above zero")

    def _project(self, pid: str) -> Project:
        p = self.projects.get(pid)
        if p is None:
            raise RegistryError("UNKNOWN_PROJECT", pid)
        return p

    # -- instructions
    def register_project(self, signer: str, pid: str, country_iso3: str, methodology: str) -> None:
        self._need_authority(signer)
        if pid in self.projects:
            raise RegistryError("EXISTS", pid)
        self.projects[pid] = Project(pid, country_iso3, methodology)

    def attest_project(self, signer: str, pid: str, attested_g: int) -> None:
        if signer not in self.verifiers:
            raise RegistryError("UNAUTHORISED", "only a verifier can attest")
        self._positive(attested_g, "attested grams")
        p = self._project(pid)
        if p.status == "suspended":
            raise RegistryError("SUSPENDED", pid)
        if attested_g < p.issued_g:
            raise RegistryError("OVER_ISSUANCE", "attestation cannot fall below what is already issued")
        p.attested_g, p.status = attested_g, "attested"

    def issue_batch(self, signer: str, pid: str, batch_id: str, vintage: int, grams: int) -> None:
        self._need_authority(signer)
        self._positive(grams, "grams")
        p = self._project(pid)
        if p.status == "suspended":
            raise RegistryError("SUSPENDED", pid)
        if p.status != "attested":
            raise RegistryError("NOT_ATTESTED", pid)
        if batch_id in self.batches:
            raise RegistryError("EXISTS", batch_id)
        if p.issued_g + grams > p.attested_g:
            raise RegistryError("OVER_ISSUANCE", "issuing would exceed the attested amount")
        p.issued_g += grams
        self.batches[batch_id] = Batch(batch_id, pid, vintage, grams)

    def link_external(self, signer: str, registry_name: str, serial: str, batch_id: str) -> None:
        self._need_authority(signer)
        if batch_id not in self.batches:
            raise RegistryError("UNKNOWN_BATCH", batch_id)
        key = (registry_name, serial)
        if key in self.links:
            raise RegistryError("DUPLICATE_LINK", f"{registry_name}:{serial} is already linked")
        self.links.add(key)

    def suspend_project(self, signer: str, pid: str) -> None:
        self._need_authority(signer)
        self._project(pid).status = "suspended"

    def retire(self, retiree: str, batch_id: str, grams: int, target_iso3: Optional[str], memo_hash: str) -> Retirement:
        self._positive(grams, "grams")
        b = self.batches.get(batch_id)
        if b is None:
            raise RegistryError("UNKNOWN_BATCH", batch_id)
        if self.projects[b.project_id].status == "suspended":
            raise RegistryError("SUSPENDED", b.project_id)
        if grams > b.issued_g - b.retired_g:
            raise RegistryError("OVER_RETIREMENT", "not enough unretired units in this batch")
        start = b.next_serial
        b.next_serial += grams
        b.retired_g += grams
        r = Retirement(len(self.retirements) + 1, batch_id, retiree, grams, start, start + grams, target_iso3, memo_hash)
        self.retirements.append(r)
        return r

    def check_invariants(self) -> None:
        """Raise InvariantError if any rule above is broken. Called by tests after every random step, at startup
        when state is rebuilt from the database, and by scripts/recheck.py."""
        def need(cond: bool, what: str) -> None:
            if not cond:
                raise InvariantError(what)
        per_project: Dict[str, int] = {}
        for b in self.batches.values():
            need(0 <= b.retired_g <= b.issued_g, f"batch {b.id}: retired more than issued")
            per_project[b.project_id] = per_project.get(b.project_id, 0) + b.issued_g
            ranges = sorted((r.serial_start, r.serial_end) for r in self.retirements if r.batch_id == b.id)
            for (s1, e1), (s2, e2) in zip(ranges, ranges[1:]):
                need(e1 <= s2, f"batch {b.id}: serial ranges overlap at {s2}")
            need((ranges[-1][1] if ranges else 0) <= b.issued_g, f"batch {b.id}: serial beyond issued")
        for pid, total in per_project.items():
            need(total == self.projects[pid].issued_g, f"project {pid}: issued total drifted")
            need(total <= self.projects[pid].attested_g, f"project {pid}: issued beyond attested")
