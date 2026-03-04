"""
Centralized configuration module for the multi-tenant data platform.

This module uses environment-driven settings so the same codebase works in local
development, CI, and cloud deployment targets. The settings object is imported in
other modules to avoid duplicated configuration logic.
"""

# ===============================
# STANDARD LIBRARY IMPORTS
# ===============================
from functools import lru_cache

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ===============================
# APPLICATION SETTINGS MODEL
# ===============================
class Settings(BaseSettings):
    """
    Defines all runtime configuration values.

    Why this design:
    - BaseSettings loads from environment variables automatically.
    - Strong typing prevents invalid settings values from being used silently.
    - A single source of truth reduces deployment mistakes.
    """

    # Database DSN used by SQLAlchemy engine/session setup.
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/backend_patterns"
    )

    # Secret key used to validate JWT signatures.
    JWT_SECRET_KEY: str = Field(default="change-me-in-real-env")
    JWT_ALGORITHM: str = Field(default="HS256")

    # Local development only toggles.
    ENABLE_LOCAL_JWT_BYPASS: bool = Field(default=True)
    LOCAL_TEST_TENANT_ID: str = Field(default="00000000-0000-0000-0000-000000000001")
    LOCAL_TEST_USER_ID: str = Field(default="00000000-0000-0000-0000-000000000002")
    LOCAL_TEST_ROLE: str = Field(default="ADMIN")

    # Ingestion protections.
    MAX_INGEST_BATCH_SIZE: int = Field(default=1000)
    ALLOWED_VIEW_NAMES: list[str] = Field(default=["team_view"])
    ALLOWED_DATABASE_NAMES: list[str] = Field(default=["core"])
    ALLOWED_READ_TABLE_NAMES: list[str] = Field(default=["teams"])

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache

def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    Why caching matters:
    - Avoids repeatedly parsing environment values.
    - Produces deterministic behavior across request handlers.
    """

    return Settings()
