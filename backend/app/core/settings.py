from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "NovaPrint API"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/novaprint"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/novaprint"

    # JWT Authentication
    secret_key: str = "your-secret-key-change-in-production-at-least-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # File Upload
    max_upload_size_mb: int = 200
    upload_dir: str = "./uploads"
    allowed_extensions: list[str] = [".stl", ".3mf"]

    # S3 Compatible Storage (optional)
    s3_enabled: bool = False
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "novaprint-uploads"

    # Redis (for background tasks)
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
