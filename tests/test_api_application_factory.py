from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.analysis import PageAnalysisService
from app.api.main import app, create_app, get_page_analysis_service
from app.core.settings import Settings


@pytest.fixture(autouse=True)
def clear_service_cache() -> None:
    get_page_analysis_service.cache_clear()
    yield
    get_page_analysis_service.cache_clear()


def test_create_app_and_module_app_are_fastapi_instances() -> None:
    assert isinstance(create_app(Settings(environment="test")), FastAPI)
    assert isinstance(app, FastAPI)


def test_explicit_settings_control_metadata_and_runtime_responses() -> None:
    settings = Settings(
        app_name="Factory Test API",
        app_version="11.2.0",
        environment="test",
    )
    application = create_app(settings)

    with TestClient(application) as client:
        root_response = client.get("/")
        health_response = client.get("/health")
        schema = client.get("/openapi.json").json()

    assert application.title == "Factory Test API"
    assert application.version == "11.2.0"
    assert root_response.status_code == 200
    assert root_response.json()["environment"] == "test"
    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "healthy",
        "service": "zypharion-api",
        "version": "11.2.0",
        "environment": "test",
    }
    assert schema["info"]["title"] == "Factory Test API"
    assert schema["info"]["version"] == "11.2.0"
    assert schema["info"]["description"] == (
        "Backend API for Zypharion, an AI-powered Quality Engineering "
        "intelligence platform."
    )
    assert "/api/v1/analyze" in schema["paths"]


def test_omitted_settings_use_get_settings() -> None:
    settings = Settings(
        app_name="Cached Settings API",
        app_version="11.2.1",
        environment="test",
    )

    with patch("app.api.main.get_settings", return_value=settings) as getter:
        application = create_app()

    getter.assert_called_once_with()
    assert application.state.settings is settings
    assert application.title == "Cached Settings API"


def test_versioned_analysis_dependency_override_works_on_new_app() -> None:
    application = create_app(Settings(environment="test"))
    service = Mock(spec=PageAnalysisService)
    service.analyze.return_value = {
        "url": "https://example.com/",
        "status": "success",
        "errors": [],
        "duration_ms": 1,
    }
    application.dependency_overrides[get_page_analysis_service] = (
        lambda: service
    )

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/analyze",
            json={"url": "https://example.com", "use_ai": False},
        )

    assert response.status_code == 200
    service.analyze.assert_called_once()


def test_dependency_overrides_are_isolated_between_app_instances() -> None:
    first_app = create_app(Settings(environment="test"))
    second_app = create_app(Settings(environment="test"))
    override = Mock(spec=PageAnalysisService)

    first_app.dependency_overrides[get_page_analysis_service] = (
        lambda: override
    )

    assert get_page_analysis_service in first_app.dependency_overrides
    assert get_page_analysis_service not in second_app.dependency_overrides


def test_creating_apps_performs_no_analysis_or_network_work() -> None:
    with (
        patch.object(
            httpx.Client,
            "request",
            side_effect=AssertionError("network request attempted"),
        ) as network_request,
        patch(
            "app.api.main.intelligence_service.analyze_browser"
        ) as browser_analysis,
        patch(
            "app.api.main.intelligence_service.analyze_page"
        ) as legacy_analysis,
        patch(
            "app.api.main.create_page_analysis_service"
        ) as workflow_composition,
    ):
        first_app = create_app(Settings(environment="test"))
        second_app = create_app(Settings(environment="test"))

    assert first_app is not second_app
    network_request.assert_not_called()
    browser_analysis.assert_not_called()
    legacy_analysis.assert_not_called()
    workflow_composition.assert_not_called()


def test_page_analysis_service_dependency_is_cached_and_clearable() -> None:
    first_service = Mock(spec=PageAnalysisService)
    second_service = Mock(spec=PageAnalysisService)

    with patch(
        "app.api.main.create_page_analysis_service",
        side_effect=[first_service, second_service],
    ) as compose:
        first = get_page_analysis_service()
        repeated = get_page_analysis_service()
        get_page_analysis_service.cache_clear()
        after_clear = get_page_analysis_service()

    assert repeated is first
    assert after_clear is second_service
    assert after_clear is not first
    assert compose.call_count == 2


def test_module_level_app_preserves_existing_endpoint_behavior() -> None:
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/health").json()["status"] == "healthy"
        schema = client.get("/openapi.json").json()

    assert "/automation/smoke" in schema["paths"]
    assert "/intelligence/analyze" in schema["paths"]
    assert "/ai/analyze" in schema["paths"]
    assert "/api/v1/analyze" in schema["paths"]
