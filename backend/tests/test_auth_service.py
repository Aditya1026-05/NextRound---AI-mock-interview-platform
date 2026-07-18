import uuid
from datetime import UTC, datetime

import pytest

from app.core.exceptions import (
    EmailAlreadyRegisteredException,
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
)
from app.core.security import create_refresh_token
from app.schemas.auth.request import (
    RefreshTokenRequest,
    UserRegisterRequest,
)
from app.services.identity.auth import AuthService


@pytest.mark.asyncio
async def test_register_user_success(db):
    service = AuthService(db)
    email = f"test_register_{uuid.uuid4().hex}@example.com"
    request_data = UserRegisterRequest(
        email=email,
        password="secure_password_123",
        full_name="John Doe",
    )

    response = await service.register_user(request_data)

    assert response.user.email == email
    assert response.user.full_name == "John Doe"
    assert response.access_token is not None
    assert response.refresh_token is not None

    # Check database persistence
    user_in_db = await service.get_user_by_email(email)
    assert user_in_db is not None
    assert user_in_db.full_name == "John Doe"


@pytest.mark.asyncio
async def test_register_user_duplicate_email(db):
    service = AuthService(db)
    email = f"duplicate_{uuid.uuid4().hex}@example.com"

    # Pre-register a user
    request_data = UserRegisterRequest(
        email=email,
        password="secure_password_123",
        full_name="First User",
    )
    await service.register_user(request_data)

    # Attempt duplicate register
    duplicate_request = UserRegisterRequest(
        email=email,
        password="different_password_123",
        full_name="Second User",
    )

    with pytest.raises(EmailAlreadyRegisteredException):
        await service.register_user(duplicate_request)


@pytest.mark.asyncio
async def test_login_user_success(db):
    service = AuthService(db)
    email = f"login_success_{uuid.uuid4().hex}@example.com"
    password = "correct_password"

    # Pre-register
    await service.register_user(
        UserRegisterRequest(
            email=email,
            password=password,
            full_name="Login Test User",
        )
    )

    # Fetch initial last_login_at
    user_db = await service.get_user_by_email(email)
    assert user_db.last_login_at is None

    # Log in
    response = await service.login_user(email=email, password=password)

    assert response.user.email == email
    assert response.access_token is not None

    # Verify last_login_at update
    await db.refresh(user_db)
    assert user_db.last_login_at is not None
    # Timestamp should be close to now
    delta = datetime.now(UTC) - user_db.last_login_at
    assert delta.total_seconds() < 5


@pytest.mark.asyncio
async def test_login_user_invalid_credentials(db):
    service = AuthService(db)
    email = f"login_fail_{uuid.uuid4().hex}@example.com"

    # Pre-register
    await service.register_user(
        UserRegisterRequest(
            email=email,
            password="correct_password",
            full_name="Login Fail User",
        )
    )

    # Login with wrong password
    with pytest.raises(InvalidCredentialsException):
        await service.login_user(email=email, password="wrong_password")

    # Login with non-existent email
    with pytest.raises(InvalidCredentialsException):
        await service.login_user(
            email="non_existent@example.com", password="some_password"
        )


@pytest.mark.asyncio
async def test_login_user_inactive(db):
    service = AuthService(db)
    email = f"inactive_{uuid.uuid4().hex}@example.com"
    password = "correct_password"

    # Pre-register
    auth_resp = await service.register_user(
        UserRegisterRequest(
            email=email,
            password=password,
            full_name="Inactive User",
        )
    )

    # Deactivate the user manually
    user_db = await service.get_user_by_id(auth_resp.user.id)
    user_db.is_active = False
    await db.commit()

    # Attempt login
    with pytest.raises(InactiveUserException):
        await service.login_user(email=email, password=password)


@pytest.mark.asyncio
async def test_refresh_access_token_success(db):
    service = AuthService(db)
    email = f"refresh_{uuid.uuid4().hex}@example.com"

    auth_resp = await service.register_user(
        UserRegisterRequest(
            email=email,
            password="password123",
            full_name="Refresh Test User",
        )
    )

    refresh_request = RefreshTokenRequest(refresh_token=auth_resp.refresh_token)
    response = await service.refresh_access_token(refresh_request)

    assert response.access_token is not None
    assert response.refresh_token is not None


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_user(db):
    service = AuthService(db)
    # Generate a refresh token for a non-existent user ID
    fake_user_id = uuid.uuid4()
    fake_refresh_token = create_refresh_token(subject=fake_user_id)

    refresh_request = RefreshTokenRequest(refresh_token=fake_refresh_token)

    with pytest.raises(InvalidTokenException):
        await service.refresh_access_token(refresh_request)


@pytest.mark.asyncio
async def test_refresh_access_token_inactive(db):
    service = AuthService(db)
    email = f"refresh_inactive_{uuid.uuid4().hex}@example.com"

    auth_resp = await service.register_user(
        UserRegisterRequest(
            email=email,
            password="password123",
            full_name="Refresh Inactive",
        )
    )

    # Deactivate user
    user_db = await service.get_user_by_id(auth_resp.user.id)
    user_db.is_active = False
    await db.commit()

    refresh_request = RefreshTokenRequest(refresh_token=auth_resp.refresh_token)

    with pytest.raises(InactiveUserException):
        await service.refresh_access_token(refresh_request)
