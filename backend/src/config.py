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

    # Zalo Bot: polling is suitable for local demos; production should use a webhook.
    zalo_bot_token: str = ""
    zalo_bot_api_base_url: str = "https://bot-api.zaloplatforms.com"
    zalo_bot_enabled: bool = False
    zalo_bot_polling_enabled: bool = False
    zalo_bot_poll_timeout_seconds: int = Field(default=25, ge=1, le=50)
    zalo_bot_processed_message_retention_days: int = Field(default=30, ge=1, le=365)
    booking_access_otp_ttl_seconds: int = Field(default=60, ge=60, le=900)
    booking_access_otp_resend_cooldown_seconds: int = Field(default=60, ge=1, le=900)
    booking_access_otp_max_attempts: int = Field(default=2, ge=1, le=10)

    # Deterministic AI guardrails. These checks run before the agent, before
    # tool execution, and before a chat response crosses the public API.
    guardrails_enabled: bool = True
    guardrails_max_payload_bytes: int = Field(default=16_384, ge=1_024, le=1_048_576)
    guardrails_max_payload_depth: int = Field(default=6, ge=1, le=20)
    guardrails_max_payload_nodes: int = Field(default=256, ge=16, le=10_000)
    guardrails_max_payload_string_chars: int = Field(default=5_000, ge=128, le=100_000)
    guardrails_max_tool_calls_per_message: int = Field(default=3, ge=1, le=8)
    guardrails_max_output_chars: int = Field(default=8_000, ge=256, le=100_000)


@lru_cache
def get_settings() -> Settings:
    return Settings()
