from app.core.security import create_access_token, decode_access_token, hash_secret, verify_secret


def test_hash_and_verify_secret_roundtrip():
    raw = "Admin@123456"
    hashed = hash_secret(raw)

    assert hashed != raw
    assert verify_secret(raw, hashed) is True
    assert verify_secret("wrong-password", hashed) is False


def test_access_token_roundtrip_contains_subject_and_role():
    token = create_access_token("user-id", "admin")
    payload = decode_access_token(token)

    assert payload["sub"] == "user-id"
    assert payload["role"] == "admin"
