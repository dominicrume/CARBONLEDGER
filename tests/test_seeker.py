"""Sign in with Seeker (carbonledger_api/seeker.py): a SIWS signature proves the wallet, the nonce works once, the
domain must be ours, and a Seeker Genesis Token is checked read-only on mainnet. One phone earns the Seeker mark once."""
import base64

from solders.keypair import Keypair

from carbonledger_api.seeker import SGT_GROUP, TOKEN_2022, sgt_lookup_rpc, sgt_mint_ok
from test_api import CLOCK, make

MINT_A, MINT_B = "5mXbkqKz883aufhAsx3p5Z1NcvD2ppZbdTTznM6oUKLj", "So11111111111111111111111111111111111111112"


def siws_text(ch: dict, address: str) -> str:
    """The SIWS message a wallet builds from the challenge (the Sign In With Solana standard layout)."""
    return (f"{ch['domain']} wants you to sign in with your Solana account:\n{address}\n\n{ch['statement']}\n\n"
            f"URI: {ch['uri']}\nVersion: {ch['version']}\nChain ID: mainnet\nNonce: {ch['nonce']}\n"
            f"Issued At: {ch['issuedAt']}\nExpiration Time: {ch['expirationTime']}")


def signed(kp: Keypair, ch: dict, text: str = None) -> dict:
    msg = (text or siws_text(ch, str(kp.pubkey()))).encode()
    return {"address": str(kp.pubkey()), "signed_message": base64.b64encode(msg).decode(),
            "signature": base64.b64encode(bytes(kp.sign_message(msg))).decode()}


def test_a_seeker_signs_in_once_per_nonce_and_earns_the_mark():
    holders = {}
    c = make(sgt_lookup=lambda w: holders.get(w))
    kp = Keypair(); holders[str(kp.pubkey())] = MINT_A
    ch = c.anon().post("/v1/auth/seeker/challenge").json()
    assert ch["domain"] == "carbonledger.world" and "no transaction" in ch["statement"]
    body = signed(kp, ch)
    r = c.post("/v1/auth/seeker/verify", json=body)
    assert r.status_code == 200 and r.json()["seeker"] is True and "verified" in r.json()["note"]
    assert c.post("/v1/auth/seeker/verify", json=body).status_code == 401                 # the nonce is used up
    me = c.anon(); me.headers["authorization"] = f"Bearer {r.json()['api_key']}"
    assert me.get("/v1/accounts/me/profile").json()["seeker"] is True


def test_refused_when_the_signature_domain_or_nonce_is_wrong():
    c = make(sgt_lookup=lambda w: None)
    kp, other = Keypair(), Keypair()
    ch = c.anon().post("/v1/auth/seeker/challenge").json()
    forged = signed(other, ch, siws_text(ch, str(kp.pubkey()))); forged["address"] = str(kp.pubkey())
    assert c.anon().post("/v1/auth/seeker/verify", json=forged).status_code == 401           # someone else's signature
    phish = dict(ch, domain="carbon-ledger.example")
    assert c.anon().post("/v1/auth/seeker/verify", json=signed(kp, phish)).status_code == 401  # a sign-in meant for another site
    made_up = dict(ch, nonce="0" * 32)
    assert c.anon().post("/v1/auth/seeker/verify", json=signed(kp, made_up)).status_code == 401
    CLOCK["t"] += 11 * 60
    assert c.anon().post("/v1/auth/seeker/verify", json=signed(kp, ch)).status_code == 401     # expired after 10 minutes


def test_one_phone_one_seeker_mark_and_honest_when_solana_is_unreachable():
    holders = {}
    c = make(sgt_lookup=lambda w: holders.get(w))
    a, b = Keypair(), Keypair()
    holders[str(a.pubkey())] = holders[str(b.pubkey())] = MINT_A                   # the same token shown twice
    assert c.anon().post("/v1/auth/seeker/verify", json=signed(a, c.anon().post("/v1/auth/seeker/challenge").json())).json()["seeker"] is True
    second = c.anon().post("/v1/auth/seeker/verify", json=signed(b, c.anon().post("/v1/auth/seeker/challenge").json())).json()
    assert second["seeker"] is False and "already belongs" in second["note"]

    def down(w):
        raise TimeoutError("rpc down")
    d = make(sgt_lookup=down)
    r = d.anon().post("/v1/auth/seeker/verify", json=signed(Keypair(), d.anon().post("/v1/auth/seeker/challenge").json())).json()
    assert r["seeker"] is False and "could not reach Solana" in r["note"]


def test_the_league_marks_seekers_and_delete_removes_the_wallet():
    holders = {}
    c = make(sgt_lookup=lambda w: holders.get(w))
    kp = Keypair(); holders[str(kp.pubkey())] = MINT_A
    r = c.post("/v1/auth/seeker/verify", json=signed(kp, c.anon().post("/v1/auth/seeker/challenge").json())).json()
    me = c.anon(); me.headers["authorization"] = f"Bearer {r['api_key']}"
    from test_api import body
    assert me.post("/v1/retire", json=body(idempotency_key="key-5000001")).status_code == 200
    assert me.get("/v1/league").json()["entries"][0]["seeker"] is True
    me.delete("/v1/accounts/me")
    people = c.app.state.st.people
    assert people.wallets == {} and people.sgt == {}


def test_the_mainnet_check_reads_token_2022_group_membership_and_skips_empty_accounts(monkeypatch):
    def mint(group, owner=TOKEN_2022):
        return {"owner": owner, "data": {"parsed": {"info": {"extensions": [{"extension": "tokenGroupMember", "state": {"group": group, "mint": MINT_A}}]}}}}
    assert sgt_mint_ok(mint(SGT_GROUP)) and not sgt_mint_ok(mint("x" * 44)) and not sgt_mint_ok(mint(SGT_GROUP, owner="Tokenkeg")) and not sgt_mint_ok(None)

    calls = []

    class R:
        def __init__(self, result): self._r = result
        def raise_for_status(self): pass
        def json(self): return {"result": self._r}

    def fake_post(url, json, timeout):
        calls.append(json["method"])
        if json["method"] == "getTokenAccountsByOwner":
            acct = lambda m, amt: {"account": {"data": {"parsed": {"info": {"mint": m, "tokenAmount": {"amount": amt}}}}}}
            return R({"value": [acct(MINT_B, "0"), acct(MINT_A, "1")]})          # an empty account first: not ownership
        assert json["params"][0] == [MINT_A]
        return R({"value": [mint(SGT_GROUP)]})
    monkeypatch.setattr("carbonledger_api.seeker.httpx.post", fake_post)
    assert sgt_lookup_rpc("https://rpc.example")("Wallet111") == MINT_A
    assert calls == ["getTokenAccountsByOwner", "getMultipleAccounts"]
