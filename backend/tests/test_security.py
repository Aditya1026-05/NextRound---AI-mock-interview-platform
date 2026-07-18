import uuid
from datetime import timedelta

import pytest

from app.core.exceptions import ExpiredTokenException, InvalidTokenException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)


def test_password_hashing():
    password = "SuperSecretPassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert hashed.startswith("$argon2")
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_valid_access_token():
    user_id = uuid.uuid4()
    access_token = create_access_token(subject=user_id)
    verified_sub = verify_access_token(access_token)
    assert verified_sub == str(user_id)


def test_valid_refresh_token():
    user_id = uuid.uuid4()
    refresh_token = create_refresh_token(subject=user_id)
    verified_refresh_sub = verify_refresh_token(refresh_token)
    assert verified_refresh_sub == str(user_id)


def test_token_type_cross_usage():
    user_id = uuid.uuid4()
    access_token = create_access_token(subject=user_id)
    refresh_token = create_refresh_token(subject=user_id)

    with pytest.raises(InvalidTokenException):
        verify_refresh_token(access_token)

    with pytest.raises(InvalidTokenException):
        verify_access_token(refresh_token)


def test_malformed_token():
    with pytest.raises(InvalidTokenException):
        verify_access_token("this.is.malformed")


def test_expired_token():
    user_id = uuid.uuid4()
    expired_token = create_access_token(
        subject=user_id, expires_delta=timedelta(seconds=-10)
    )
    with pytest.raises(ExpiredTokenException):
        verify_access_token(expired_token)
