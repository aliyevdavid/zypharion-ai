from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized, typed configuration for the Zypharion application.

    Values may come from defaults, operating-system environment variables,
    or a local .env file that is never committed to source control.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Zypharion API"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "development", "production"] = "local"
    debug: bool = False

    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)

    playwright_headless: bool = True
    playwright_timeout_ms: int = Field(default=30_000, ge=1_000)

    llm_provider: Literal["mock", "openai"] = "mock"
    llm_model: str = "not-configured"
    openai_api_key: str | None = None

    ai_provider: str = "mock"
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_api_version: str | None = None


@lru_cache
def get_settings() -> Settings:
    """
    Return one cached Settings instance for the running application.

    Tests can clear the cache with get_settings.cache_clear().
    """

    return Settings()
