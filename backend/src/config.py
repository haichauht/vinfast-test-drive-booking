from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Shared root defaults load first; backend-local values are more specific
        # and must win (notably the SQLite URL supported by this MVP).
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "AI20K Agent"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000"

    # LLM
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    model_name: str = "gpt-4o-mini"
    classifier_model_name: str = ""
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # Database
    database_url: str = "postgresql://vinfast:vinfast@localhost:5432/vinfast_booking"
    auto_load_eval_data: bool = True
    eval_data_dir: str = "eval/data"

    # Media: local development serves MEDIA_ROOT at /media. Production can set
    # MEDIA_BASE_URL to an absolute CDN origin without changing API DTOs.
    media_root: str = "./data/media"
    media_base_url: str = "/media"

    # Vector Store
    chroma_persist_dir: str = "./data/chroma"


@lru_cache
def get_settings() -> Settings:
    return Settings()
