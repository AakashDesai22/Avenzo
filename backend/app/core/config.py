"""
AVENZO Backend — Application Configuration
Loads all environment variables using Pydantic Settings.
Enforces production security rules when APP_ENV == "production".
"""


from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings


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

    # Initial Admin Bootstrap (One-time setup for development / academic project)
    INITIAL_ADMIN_EMAIL: str = "admin@avenzo.dev"
    INITIAL_ADMIN_PASSWORD: str = ""
    INITIAL_ADMIN_FIRST_NAME: str = "Admin"
    INITIAL_ADMIN_LAST_NAME: str = "User"

    # JWT Authentication
    JWT_SECRET: str = "CHANGE_THIS_SECRET_IN_PRODUCTION_MINIMUM_32_CHARS"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS — comma-separated list of allowed origins.
    # Canonical configuration name: ALLOWED_ORIGINS.
    # Backward-compatible legacy name: ALLOWED_ORIGINS_STR.
    # Deterministic precedence: ALLOWED_ORIGINS > ALLOWED_ORIGINS_STR.
    ALLOWED_ORIGINS_STR: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "ALLOWED_ORIGINS_STR"),
        description="Comma-separated allowed CORS origins. Precedence: ALLOWED_ORIGINS > ALLOWED_ORIGINS_STR.",
    )

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        origins: list[str] = []
        for raw in self.ALLOWED_ORIGINS_STR.split(","):
            cleaned = raw.strip()
            if not cleaned:
                continue
            # Strip trailing slash if present (CORS origins do not include path or trailing slash)
            if cleaned.endswith("/") and cleaned not in ("http://", "https://"):
                cleaned = cleaned.rstrip("/")
            if cleaned and cleaned not in origins:
                origins.append(cleaned)
        return origins

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

    # Cloudinary Image Storage
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "avenzo"

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
            if "*" in self.ALLOWED_ORIGINS:
                raise ValueError(
                    "Wildcard '*' origin is not permitted when allow_credentials=True in production."
                )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Singleton settings instance
settings = Settings()
