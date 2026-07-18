from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Schema for candidate registration request."""

    full_name: str = Field(
        ..., min_length=1, max_length=100, description="User's full name"
    )
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., min_length=8, description="User's password (min 8 chars)"
    )


class UserLoginRequest(BaseModel):
    """Schema for user credentials login request."""

    email: EmailStr = Field(..., description="User's login email")
    password: str = Field(..., description="User's login password")


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="JWT Refresh Token")
