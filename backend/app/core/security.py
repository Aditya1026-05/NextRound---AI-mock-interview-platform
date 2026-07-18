import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import ExpiredTokenException, InvalidTokenException
from app.shared.enums import TokenType

# Recommended password hash will auto-detect and use argon2 since we installed it.
password_hash_helper = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2."""
    return password_hash_helper.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its Argon2 hash."""
    return password_hash_helper.verify(password, hashed_password)


def _create_token(
    subject: str | uuid.UUID,
    token_type: TokenType,
    expires_delta: timedelta | None = None,
) -> str:
    """Internal helper to create a signed JWT token with standard claims."""
    now = datetime.now(UTC)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        if token_type == TokenType.ACCESS:
            expire = now + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        else:
            expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }

    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def create_access_token(
    subject: str | uuid.UUID, expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token."""
    return _create_token(
        subject=subject,
        token_type=TokenType.ACCESS,
        expires_delta=expires_delta,
    )


def create_refresh_token(
    subject: str | uuid.UUID, expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT refresh token."""
    return _create_token(
        subject=subject,
        token_type=TokenType.REFRESH,
        expires_delta=expires_delta,
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token, verifying standard claims."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenException() from None
    except JWTError:
        raise InvalidTokenException() from None


def verify_access_token(token: str) -> str:
    """Verify an access token and return its subject (user ID)."""
    payload = decode_token(token)
    if payload.get("type") != TokenType.ACCESS.value:
        raise InvalidTokenException("Invalid token type")
    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenException("Token has no subject")
    return subject


def verify_refresh_token(token: str) -> str:
    """Verify a refresh token and return its subject (user ID)."""
    payload = decode_token(token)
    if payload.get("type") != TokenType.REFRESH.value:
        raise InvalidTokenException("Invalid token type")
    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenException("Token has no subject")
    return subject
