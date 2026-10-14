"""Sign-in email. Off unless RESEND_API_KEY and EMAIL_FROM are set: then sign-in says it is not set up and stores
nothing. The key comes from the secret store, never from the repo. The email holds a one-time link and nothing else."""
import os
import sys
from typing import Callable, Optional

import httpx

Mailer = Callable[[str, str], None]


def resend_mailer(api_key: str, sender: str) -> Mailer:
    def send(to: str, link: str) -> None:
        body = {"from": sender, "to": [to], "subject": "Your CarbonLedger sign-in link",
                "text": f"Sign in to CarbonLedger with this link. It works once, for 15 minutes:\n\n{link}\n\n"
                        "If you did not ask for it, ignore this email. Nothing happens unless the link is opened.\n"
                        "CarbonLedger: pilot units, not yet verified credits."}
        r = httpx.post("https://api.resend.com/emails", json=body, headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
        r.raise_for_status()
    return send


def mailer_from_env() -> Optional[Mailer]:
    key, sender = os.environ.get("RESEND_API_KEY", "").strip(), os.environ.get("EMAIL_FROM", "").strip()
    if not key or key.startswith("<") or not sender:
        if os.environ.get("APP_ENV") == "dev":      # on a laptop only: the link goes to this terminal, never to anyone
            return lambda to, link: print(f"[dev] sign-in link for {to}: {link}", file=sys.stderr, flush=True)
        return None
    return resend_mailer(key, sender)
