from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    public_base_url: str = ""
    dashboard_origin: str = "http://localhost:3000"

    telegram_bot_token: str
    telegram_webhook_secret: str = Field(min_length=16, pattern=r"^[A-Za-z0-9_-]+$")
    admin_telegram_ids: Annotated[list[int], NoDecode] = []

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = "claude"
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-5-5"   # confirm the exact model id in your Anthropic console
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    embedding_provider: str = "voyage"
    embedding_model: str = ""
    embedding_dim: int = 1024
    voyage_api_key: str = ""

    jwt_secret: str = Field(min_length=32)
    jwt_ttl_minutes: int = 480
    max_request_bytes: int = 1_048_576
    rate_limit_per_minute: int = 20
    retention_days: int = 365

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def _split_ids(cls, v):
        if isinstance(v, str):
            return [int(x) for x in v.split(",") if x.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # fails fast at startup when a required secret is missing
