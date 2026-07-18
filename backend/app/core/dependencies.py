import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationRequiredException,
    InactiveUserException,
    InvalidTokenException,
)
from app.core.security import verify_access_token
from app.dependencies.providers import get_db
from app.models.identity.user import User

# Configure scheme with auto_error=False to allow custom error handling
# and support optional authentication dependencies.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", auto_error=False
)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract Bearer token, validate it, and return the current user."""
    if not token:
        raise AuthenticationRequiredException()

    user_id_str = verify_access_token(token)
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise InvalidTokenException() from None

    user = await db.scalar(select(User).filter(User.id == user_uuid))
    if not user:
        raise InvalidTokenException()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user is active."""
    if not current_user.is_active:
        raise InactiveUserException()
    return current_user


async def optional_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Optionally extract Bearer token and return the current user if authenticated."""
    if not token:
        return None

    try:
        user_id_str = verify_access_token(token)
        user_uuid = uuid.UUID(user_id_str)
        user = await db.scalar(select(User).filter(User.id == user_uuid))
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None
