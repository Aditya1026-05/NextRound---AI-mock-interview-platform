from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.dependencies.providers import get_db
from app.models.identity.user import User
from app.schemas.auth.request import (
    RefreshTokenRequest,
    UserRegisterRequest,
)
from app.schemas.auth.response import AuthResponse, TokenResponse, UserResponse
from app.services.identity.auth import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a candidate account and return JWT credentials.",
)
async def register(
    schema: UserRegisterRequest, db: AsyncSession = Depends(get_db)
):
    """Handle candidate registration."""
    service = AuthService(db)
    return await service.register_user(schema)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User credentials login",
    description="Authenticate a user and return a JWT access and refresh token pair.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Handle user login credentials verification."""
    service = AuthService(db)
    return await service.login_user(
        email=form_data.username, password=form_data.password
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Generate a new set of JWT credentials using a valid refresh token.",
)
async def refresh(
    schema: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    """Handle access token renewal."""
    service = AuthService(db)
    return await service.refresh_access_token(schema)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the current active authenticated user's profile details.",
)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Return the profile of the current active authenticated user."""
    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out current session",
    description="Invalidate the user session on the client side.",
)
async def logout(current_user: User = Depends(get_current_active_user)):
    """Log out the current user session."""
    return None
