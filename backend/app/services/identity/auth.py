import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EmailAlreadyRegisteredException,
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from app.models.identity.user import User
from app.schemas.auth.request import (
    RefreshTokenRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.auth.response import AuthResponse, TokenResponse, UserResponse


class AuthService:
    """Service handling business logic for identity authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        """Query user details by email."""
        return await self.db.scalar(select(User).filter(User.email == email))

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Query user details by ID."""
        return await self.db.scalar(select(User).filter(User.id == user_id))

    async def register_user(self, schema: UserRegisterRequest) -> AuthResponse:
        """Verify email uniqueness, hash password, and return auth details."""
        existing_user = await self.get_user_by_email(schema.email)
        if existing_user:
            raise EmailAlreadyRegisteredException()

        hashed_pass = hash_password(schema.password)

        new_user = User(
            email=schema.email,
            full_name=schema.full_name,
            password_hash=hashed_pass,
            is_active=True,
            is_verified=False,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        # Automatically log in the user after registration
        access_token = create_access_token(subject=new_user.id)
        refresh_token = create_refresh_token(subject=new_user.id)

        return AuthResponse(
            user=UserResponse.model_validate(new_user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def login_user(self, schema: UserLoginRequest) -> AuthResponse:
        """Verify user credentials and generate token credentials."""
        user = await self.authenticate_user(schema.email, schema.password)

        # Update last login time
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(user)

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        return AuthResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(
        self, schema: RefreshTokenRequest
    ) -> TokenResponse:
        """Verify refresh token integrity and return a new token pair."""
        user_id_str = verify_refresh_token(schema.refresh_token)
        try:
            user_uuid = uuid.UUID(user_id_str)
        except ValueError:
            raise InvalidTokenException() from None

        user = await self.get_user_by_id(user_uuid)
        if not user:
            raise InvalidTokenException()

        if not user.is_active:
            raise InactiveUserException()

        new_access_token = create_access_token(subject=user.id)
        new_refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    async def authenticate_user(self, email: str, password: str) -> User:
        """Check credentials authenticity and user status."""
        user = await self.get_user_by_email(email)
        if not user:
            raise InvalidCredentialsException()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InactiveUserException()

        return user
