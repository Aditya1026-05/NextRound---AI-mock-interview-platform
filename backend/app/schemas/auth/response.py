import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl


class UserResponse(BaseModel):
    """Schema for candidate profile details response (never exposes password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: EmailStr
    avatar_url: HttpUrl | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """Schema for authentication token details response."""

    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"


class AuthResponse(BaseModel):
    """Schema for complete authentication login/register response."""

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
