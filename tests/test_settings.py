from app.core.settings import Settings, get_settings


def test_default_settings_are_valid() -> None:
    settings = Settings()

    assert settings.app_name == "Zypharion API"
    assert settings.environment == "local"
    assert settings.api_port == 8000
    assert settings.playwright_headless is True
    assert settings.llm_provider == "mock"
    assert settings.ai_provider == "mock"


def test_ai_provider_settings_load_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AI_PROVIDER", "azure_openai")
    monkeypatch.setenv(
        "AZURE_OPENAI_ENDPOINT",
        "https://example.openai.azure.com/",
    )
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "test-deployment")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

    settings = Settings()

    assert settings.ai_provider == "azure_openai"
    assert (
        settings.azure_openai_endpoint
        == "https://example.openai.azure.com/"
    )
    assert settings.azure_openai_api_key == "test-key"
    assert settings.azure_openai_deployment == "test-deployment"
    assert settings.azure_openai_api_version == "2024-10-21"


def test_get_settings_returns_cached_instance() -> None:
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
