from carbonledger.auth import ApiKeyStore, AuthError, TokenBucket, hash_key
import pytest

PEPPER = "x" * 32


def test_a_key_is_shown_once_and_only_its_hash_is_kept():
    s = ApiKeyStore(PEPPER)
    key, rec = s.issue("business", "acme")
    assert key.startswith("clk_business_") and rec.key_hash == hash_key(PEPPER, key)
    assert key not in repr(vars(rec))
    assert s.check(key).owner == "acme"


def test_missing_wrong_and_revoked_keys_fail_with_their_own_codes():
    s = ApiKeyStore(PEPPER)
    key, rec = s.issue("personal", "p1")
    flipped = key[:-1] + ("1" if key[-1] == "0" else "0")        # always a different key, whatever the last character was
    for bad, code in [(None, "NO_KEY"), ("", "NO_KEY"), ("clk_personal_nope", "BAD_KEY"), (flipped, "BAD_KEY")]:
        with pytest.raises(AuthError) as e:
            s.check(bad)
        assert e.value.code == code
    assert s.revoke(rec.key_id)
    with pytest.raises(AuthError) as e:
        s.check(key)
    assert e.value.code == "REVOKED_KEY"


def test_a_different_pepper_turns_every_key_into_a_stranger():
    s1, s2 = ApiKeyStore(PEPPER), ApiKeyStore("y" * 32)
    key, rec = s1.issue("agent", "bot")
    s2.add_hashed(rec.role, rec.owner, rec.key_hash)
    with pytest.raises(AuthError):
        s2.check(key)


def test_bad_role_and_short_pepper_are_refused():
    with pytest.raises(AuthError):
        ApiKeyStore("short")
    with pytest.raises(AuthError):
        ApiKeyStore(PEPPER).issue("admin", "x")


def test_token_bucket_refills_at_the_set_rate():
    clock = {"t": 0.0}
    b = TokenBucket(per_minute=60, burst=3, now=lambda: clock["t"])
    assert [b.take("k") for _ in range(4)] == [True, True, True, False]
    clock["t"] += 1.0                      # one token a second at 60 a minute
    assert b.take("k") and not b.take("k")
    assert b.take("other")                 # buckets are per key
