
from datetime import timedelta

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hashing():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_access_token_creation():
    token = create_access_token(agent_id=10)

    assert isinstance(token, str)
    assert decode_access_token(token) == 10


def test_invalid_access_token():
    result = decode_access_token("invalid.jwt.token")

    assert result is None


def test_expired_access_token():
    token = create_access_token(
        agent_id=10,
        expires_delta=timedelta(seconds=-1)
    )

    assert decode_access_token(token) is None
