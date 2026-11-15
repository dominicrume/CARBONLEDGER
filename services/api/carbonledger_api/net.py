"""The client's address for per-address limits. X-Forwarded-For is a list: each proxy appends the address it saw.
Only the entries our own proxies appended can be trusted; anything to their left was sent by the client and can be
forged. With TRUSTED_PROXY_HOPS=1 (one proxy, the host's edge) the client is the rightmost entry."""
from fastapi import Request


def client_address(request: Request, trusted_hops: int) -> str:
    direct = request.client.host if request.client else "unknown"
    if trusted_hops <= 0:
        return direct
    hops = [h.strip() for h in request.headers.get("x-forwarded-for", "").split(",") if h.strip()]
    return hops[-trusted_hops] if len(hops) >= trusted_hops else (hops[0] if hops else direct)
