from typing import Any

from openai import AzureOpenAI

from app.ai.engine import AIEngine
from app.ai.mock_engine import MockAIEngine
from app.ai.providers.azure_openai_engine import AzureOpenAIEngine
from app.core.settings import Settings


def create_ai_provider(
    settings: Settings,
    *,
    azure_client: Any | None = None,
) -> AIEngine:
    """Construct the configured AI provider without making an API request."""
    provider_name = settings.ai_provider.strip().lower()

    if provider_name == "mock":
        return MockAIEngine()

    if provider_name != "azure_openai":
        raise ValueError(f"Unsupported AI provider: {settings.ai_provider!r}")

    endpoint = _require_setting(
        settings.azure_openai_endpoint,
        "AZURE_OPENAI_ENDPOINT",
    )
    api_key = _require_setting(
        settings.azure_openai_api_key,
        "AZURE_OPENAI_API_KEY",
    )
    deployment = _require_setting(
        settings.azure_openai_deployment,
        "AZURE_OPENAI_DEPLOYMENT",
    )
    api_version = _require_setting(
        settings.azure_openai_api_version,
        "AZURE_OPENAI_API_VERSION",
    )

    client = azure_client
    if client is None:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

    return AzureOpenAIEngine(client, deployment)


def _require_setting(value: str | None, environment_name: str) -> str:
    if value is None or not value.strip():
        raise ValueError(
            f"{environment_name} is required when "
            "AI_PROVIDER=azure_openai"
        )

    return value.strip()
