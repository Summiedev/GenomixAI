from functools import lru_cache

from fastapi import Request
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    project_name: str = "GenomixAI Backend"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://localhost:5432/genomixai"
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1)
    cors_origins: list[str] = Field(default_factory=list)
    log_level: str = "INFO"

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        environment = self.app_env.strip().lower()
        if environment in {"production", "prod"} and len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters in production")
        if "*" in self.cors_origins:
            raise ValueError("Wildcard CORS origins are not permitted")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_request_settings(request: Request) -> Settings:
    """Use the settings bound to the current app instance in request handlers."""

    return getattr(request.app.state, "settings", None) or get_settings()
