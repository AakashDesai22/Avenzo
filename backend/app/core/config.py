"""
AVENZO Backend — Application Configuration
Loads all environment variables using Pydantic Settings.
Enforces production security rules when APP_ENV == "production".
"""

from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    See .env.example for all available variables.
    """

    # Application
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://avenzo_user:password@localhost:5432/avenzo_db"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "avenzo_db"
    DATABASE_USER: str = "avenzo_user"
    DATABASE_PASSWORD: str = "password"

    # JWT Authentication
    JWT_SECRET: str = "CHANGE_THIS_SECRET_IN_PRODUCTION_MINIMUM_32_CHARS"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS — comma-separated list of allowed origins
    ALLOWED_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000"

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_STR.split(",") if origin.strip()]

    # Inventory & Expiry Threshold Defaults (Centralized App-Level Config)
    EXPIRING_SOON_THRESHOLD_DAYS: int = 30
    CRITICAL_THRESHOLD_DAYS: int = 7

    # AI Service
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_API_KEY: str = ""

    # Firebase FCM
    FCM_PROJECT_ID: str = ""
    FCM_PRIVATE_KEY_ID: str = ""
    FCM_PRIVATE_KEY: str = ""
    FCM_CLIENT_EMAIL: str = ""
    FCM_CLIENT_ID: str = ""

    # Expiry Monitoring Internal Trigger Secret
    EXPIRY_MONITOR_SECRET: str = "dev-only-change-me"

    # Logging
    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Enforces strict security constraints and normalizes DATABASE_URL."""
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.DATABASE_URL.startswith("postgresql://") and not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

        if self.APP_ENV.lower() == "production":
            if self.APP_DEBUG:
                raise ValueError("APP_DEBUG must be set to False in production mode.")
            if "CHANGE_THIS_SECRET" in self.JWT_SECRET or len(self.JWT_SECRET) < 32:
                raise ValueError(
                    "JWT_SECRET must be configured with a strong secret (at least 32 characters) in production."
                )
            if (
                not self.EXPIRY_MONITOR_SECRET
                or "change-me" in self.EXPIRY_MONITOR_SECRET.lower()
                or len(self.EXPIRY_MONITOR_SECRET) < 16
            ):
                raise ValueError(
                    "EXPIRY_MONITOR_SECRET must be configured with a strong secret (at least 16 characters) in production."
                )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Singleton settings instance
settings = Settings()
