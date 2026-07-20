from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "NextRound"
    ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/nextround"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI & Integrations
    LITELLM_GEMINI_API_KEY: str | None = None
    LITELLM_GROQ_API_KEY: str | None = None
    CLOUDINARY_URL: str | None = None
    JUDGE0_URL: str = "http://localhost:2358"
    JUDGE0_API_KEY: str | None = None

    # LLM settings
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini/gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 30
    LLM_PROFILES_PATH: str = "configs/llm_profiles.yaml"
    LLM_FALLBACK_ORDER: list[str] = ["gemini", "groq", "mistral", "ollama"]

    # LLM API keys
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    MISTRAL_API_KEY: str | None = None
    OLLAMA_BASE_URL: str | None = None

    # Storage
    UPLOAD_DIR: str = "uploads"

    # JWT Security Configurations
    SECRET_KEY: str = "supersecretkey_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "nextround-api"
    JWT_AUDIENCE: str = "nextround-app"

    # Logging Configurations
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False
    SQL_ECHO: bool = False


settings = Settings()
