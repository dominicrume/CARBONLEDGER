"""People and metrics storage (db/migrations/0004_people_metrics.sql). Not ledger history: these rows may change and be
deleted. MemoryPeople keeps them in the process (tests, dry runs); PostgresPeople writes them to the database.
Personal data is only accounts.email and profiles.display_name. Event counts hold a day, a name and a number."""
import secrets
import threading
from contextlib import contextmanager
from typing import Dict, Optional, Set


class MemoryPeople:
    kind = "memory"

    def __init__(self):
        self._lock = threading.Lock()
        self.events: Dict[tuple, int] = {}
        self.accounts: Dict[str, str] = {}          # account id -> email
        self.owners: Dict[str, str] = {}            # owner -> account id
        self.links: Dict[str, tuple] = {}           # token hash -> (email, expires_at, used)
        self.profiles: Dict[str, dict] = {}

    # ---- A: event counts ----
    def count_event(self, day: str, name: str) -> None:
        with self._lock:
            self.events[(day, name)] = self.events.get((day, name), 0) + 1

    def event_counts(self, since_day: str) -> Dict[str, Dict[str, int]]:
        out: Dict[str, Dict[str, int]] = {}
        for (day, name), n in self.events.items():
            if day >= since_day:
                out.setdefault(day, {})[name] = n
        return out

    # ---- B: sign-in links and accounts ----
    def put_link(self, token_hash: str, email: str, expires_at: float) -> None:
        self.links[token_hash] = (email, expires_at, False)

    def take_link(self, token_hash: str, now: float) -> Optional[str]:
        """The email for a valid, unused, unexpired link, and the link is used up. None otherwise."""
        with self._lock:
            row = self.links.get(token_hash)
            if not row or row[2] or row[1] < now:
                return None
            self.links[token_hash] = (row[0], row[1], True)
            return row[0]

    def account_for_email(self, email: str) -> str:
        with self._lock:
            for aid, e in self.accounts.items():
                if e == email:
                    return aid
            aid = f"acct-{secrets.token_hex(6)}"
            self.accounts[aid] = email
            self.owners[aid] = aid                  # the account's own main owner id
            return aid

    def link_owner(self, owner: str, account_id: str) -> None:
        with self._lock:
            self.owners.setdefault(owner, account_id)   # an owner already linked elsewhere stays where it is

    def account_of(self, owner: str) -> Optional[str]:
        return self.owners.get(owner)

    def owners_of(self, account_id: str) -> Set[str]:
        return {o for o, a in self.owners.items() if a == account_id}

    def email_of(self, account_id: str) -> Optional[str]:
        return self.accounts.get(account_id)

    # ---- profiles ----
    def get_profile(self, owner: str) -> dict:
        return dict(self.profiles.get(owner, {}))

    def put_profile(self, owner: str, fields: dict) -> dict:
        with self._lock:
            p = self.profiles.setdefault(owner, {})
            p.update(fields)
            return dict(p)

    def all_display_names(self) -> Dict[str, str]:
        return {o: p["display_name"] for o, p in self.profiles.items() if p.get("display_name")}

    # ---- delete my data ----
    def delete(self, owners: Set[str], account_id: Optional[str]) -> None:
        with self._lock:
            for o in owners:
                self.profiles.pop(o, None)
                self.owners.pop(o, None)
            if account_id:
                email = self.accounts.pop(account_id, None)
                self.links = {h: v for h, v in self.links.items() if v[0] != email}


class PostgresPeople:
    kind = "postgres"

    def __init__(self, url: str):
        import psycopg
        self._psycopg, self.url = psycopg, url
        with self._conn() as c:
            c.execute("SELECT 1 FROM schema_migrations WHERE name = '0004_people_metrics.sql'")
            if c.fetchone() is None:
                raise RuntimeError("database is not migrated: run python scripts/migrate.py")

    @contextmanager
    def _conn(self):
        with self._psycopg.connect(self.url) as conn:
            with conn.cursor() as cur:
                yield cur
            conn.commit()

    def count_event(self, day: str, name: str) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO event_counts (day, name, n) VALUES (%s,%s,1) ON CONFLICT (day, name) DO UPDATE SET n = event_counts.n + 1", (day, name))

    def event_counts(self, since_day: str) -> Dict[str, Dict[str, int]]:
        with self._conn() as c:
            c.execute("SELECT day::text, name, n FROM event_counts WHERE day >= %s", (since_day,))
            out: Dict[str, Dict[str, int]] = {}
            for day, name, n in c.fetchall():
                out.setdefault(day, {})[name] = n
            return out

    def put_link(self, token_hash: str, email: str, expires_at: float) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO login_links (token_hash, email, expires_at) VALUES (%s,%s,to_timestamp(%s))", (token_hash, email, expires_at))

    def take_link(self, token_hash: str, now: float) -> Optional[str]:
        with self._conn() as c:
            c.execute("UPDATE login_links SET used = true WHERE token_hash = %s AND NOT used AND expires_at >= to_timestamp(%s) RETURNING email",
                      (token_hash, now))
            row = c.fetchone()
            return row[0] if row else None

    def account_for_email(self, email: str) -> str:
        with self._conn() as c:
            c.execute("SELECT id FROM accounts WHERE email = %s", (email,))
            row = c.fetchone()
            if row:
                return row[0]
            aid = f"acct-{secrets.token_hex(6)}"
            c.execute("INSERT INTO accounts (id, email) VALUES (%s,%s)", (aid, email))
            c.execute("INSERT INTO account_owners (owner, account_id) VALUES (%s,%s) ON CONFLICT (owner) DO NOTHING", (aid, aid))
            return aid

    def link_owner(self, owner: str, account_id: str) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO account_owners (owner, account_id) VALUES (%s,%s) ON CONFLICT (owner) DO NOTHING", (owner, account_id))

    def account_of(self, owner: str) -> Optional[str]:
        with self._conn() as c:
            c.execute("SELECT account_id FROM account_owners WHERE owner = %s", (owner,))
            row = c.fetchone()
            return row[0] if row else None

    def owners_of(self, account_id: str) -> Set[str]:
        with self._conn() as c:
            c.execute("SELECT owner FROM account_owners WHERE account_id = %s", (account_id,))
            return {r[0] for r in c.fetchall()}

    def email_of(self, account_id: str) -> Optional[str]:
        with self._conn() as c:
            c.execute("SELECT email FROM accounts WHERE id = %s", (account_id,))
            row = c.fetchone()
            return row[0] if row else None

    def get_profile(self, owner: str) -> dict:
        with self._conn() as c:
            c.execute("SELECT display_name, business_name, employees FROM profiles WHERE owner = %s", (owner,))
            row = c.fetchone()
            return {k: v for k, v in zip(("display_name", "business_name", "employees"), row) if v is not None} if row else {}

    def put_profile(self, owner: str, fields: dict) -> dict:
        cur = self.get_profile(owner)
        cur.update(fields)
        with self._conn() as c:
            c.execute("""INSERT INTO profiles (owner, display_name, business_name, employees) VALUES (%s,%s,%s,%s)
                         ON CONFLICT (owner) DO UPDATE SET display_name = EXCLUDED.display_name, business_name = EXCLUDED.business_name,
                         employees = EXCLUDED.employees, updated_at = now()""",
                      (owner, cur.get("display_name"), cur.get("business_name"), cur.get("employees")))
        return cur

    def all_display_names(self) -> Dict[str, str]:
        with self._conn() as c:
            c.execute("SELECT owner, display_name FROM profiles WHERE display_name IS NOT NULL")
            return dict(c.fetchall())

    def delete(self, owners: Set[str], account_id: Optional[str]) -> None:
        with self._conn() as c:
            for o in owners:
                c.execute("DELETE FROM profiles WHERE owner = %s", (o,))
            if account_id:
                c.execute("DELETE FROM login_links WHERE email = (SELECT email FROM accounts WHERE id = %s)", (account_id,))
                c.execute("DELETE FROM accounts WHERE id = %s", (account_id,))     # account_owners go with it (ON DELETE CASCADE)


def people_from_env(url: Optional[str]):
    return PostgresPeople(url) if url else MemoryPeople()
