
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BrightCore Recruitment API"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"

    database_url: str
    redis_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    cv_storage_path: str = "./private_uploads/cvs"
    cv_max_bytes: int = 5 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
