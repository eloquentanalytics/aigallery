from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Google Auth
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")

    # Stripe
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # External APIs
    replicate_api_token: str = os.getenv("REPLICATE_API_TOKEN", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # App secrets
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database - support both SQLite (local) and Postgres (Vercel/production)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/gallery.db")

    # Vercel-specific settings
    vercel_env: Optional[str] = os.getenv("VERCEL_ENV", None)  # development, preview, production
    is_vercel: bool = os.getenv("VERCEL", "0") == "1"

    class Config:
        env_file = ".env"

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings