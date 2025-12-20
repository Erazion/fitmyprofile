from __future__ import annotations

try:
    from pydantic_settings import BaseSettings  # type: ignore
except ImportError:
    from pydantic import BaseSettings  # type: ignore


class Settings(BaseSettings):
    ENV: str = "dev"

    OPENAI_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str | None = None
    OPENROUTER_APP_NAME: str | None = None

    PRICE_EUR: float = 4.90
    USE_FAKE_CHECKOUT: bool = True
    MAX_UPLOAD_MB: int = 5
    RATE_LIMIT_PER_MIN: int = 120
    RATE_LIMIT_BURST: int = 40
    LOG_LEVEL: str = "INFO"

    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PRICE_ID: str | None = None

    ANALYTICS_DOMAIN: str | None = None

    PUBLIC_BASE_URL: str | None = None

    SESSION_SECRET_KEY: str = "dev_secret"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
