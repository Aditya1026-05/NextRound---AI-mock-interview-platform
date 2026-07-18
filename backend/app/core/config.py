
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "NextRound"
    ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nextround"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI & Integrations
    LITELLM_GEMINI_API_KEY: str | None = None
    LITELLM_GROQ_API_KEY: str | None = None
    CLOUDINARY_URL: str | None = None
    JUDGE0_URL: str = "http://localhost:2358"
    JUDGE0_API_KEY: str | None = None

    # JWT Security Configurations
    SECRET_KEY: str = "supersecretkey_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "nextround-api"
    JWT_AUDIENCE: str = "nextround-app"

settings = Settings()
