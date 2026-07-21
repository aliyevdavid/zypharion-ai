from app.core.settings import Settings, get_settings


def test_default_settings_are_valid() -> None:
    settings = Settings()

    assert settings.app_name == "Zypharion API"
    assert settings.environment == "local"
    assert settings.api_port == 8000
    assert settings.playwright_headless is True
    assert settings.llm_provider == "mock"


def test_get_settings_returns_cached_instance() -> None:
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second