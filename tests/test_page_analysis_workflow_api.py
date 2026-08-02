from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.ai import (
    AIIntelligenceResult,
    AIPageClassification,
    LLMIntelligenceEngine,
    MockAIEngine,
)
from app.analysis import (
    AnalysisError,
    AnalysisStage,
    AnalysisStatus,
    PageAnalysisRequest,
    PageAnalysisResult,
    PageAnalysisService,
)
from app.api.main import app, get_page_analysis_service
from app.intelligence import (
    BrowserIntelligenceResult,
    ExtractionWarning,
    PageAnalysisResult as DeterministicPageAnalysisResult,
    PageClassification,
    PageMetrics,
    PageType,
)


@pytest.fixture
def browser_result() -> BrowserIntelligenceResult:
    return BrowserIntelligenceResult(
        requested_url="https://example.com/",
        final_url="https://example.com/",
        title="Example",
        success=True,
        metrics=PageMetrics(load_time_ms=10),
    )


@pytest.fixture
def deterministic_result() -> DeterministicPageAnalysisResult:
    return DeterministicPageAnalysisResult(
        requested_url="https://example.com/",
        final_url="https://example.com/",
        title="Example",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.8,
            evidence=["Informational page structure detected"],
        ),
    )


@pytest.fixture
def client_and_service() -> tuple[TestClient, Mock]:
    service = Mock(spec=PageAnalysisService)
    app.dependency_overrides[get_page_analysis_service] = lambda: service
    with TestClient(app) as client:
        yield client, service
    app.dependency_overrides.clear()


def test_valid_request_uses_overridden_service_once(
    client_and_service: tuple[TestClient, Mock],
    browser_result: BrowserIntelligenceResult,
    deterministic_result: DeterministicPageAnalysisResult,
) -> None:
    client, service = client_and_service
    result = PageAnalysisResult(
        url="https://example.com/",
        status=AnalysisStatus.SUCCESS,
        browser_result=browser_result,
        intelligence=deterministic_result,
        duration_ms=12,
    )
    service.analyze.return_value = result

    response = client.post(
        "/api/v1/analyze",
        json={"url": "https://example.com", "use_ai": False},
    )

    assert response.status_code == 200
    assert response.json() == result.model_dump(mode="json")
    service.analyze.assert_called_once()
    request = service.analyze.call_args.args[0]
    assert isinstance(request, PageAnalysisRequest)
    assert str(request.url) == "https://example.com/"
    assert request.use_ai is False


def test_application_api_serializes_browser_warnings_without_errors(
    client_and_service: tuple[TestClient, Mock],
    browser_result: BrowserIntelligenceResult,
    deterministic_result: DeterministicPageAnalysisResult,
) -> None:
    client, service = client_and_service
    browser_result.warnings.append(
        ExtractionWarning(
            category="buttons",
            code="buttons_extraction_failed",
            message="Button content could not be extracted.",
        )
    )
    service.analyze.return_value = PageAnalysisResult(
        url="https://example.com/",
        status=AnalysisStatus.SUCCESS,
        browser_result=browser_result,
        intelligence=deterministic_result,
    )

    response = client.post(
        "/api/v1/analyze",
        json={"url": "https://example.com"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["browser_result"]["warnings"][0]["code"] == (
        "buttons_extraction_failed"
    )
    assert response.json()["errors"] == []


def test_successful_ai_response_is_serialized(
    client_and_service: tuple[TestClient, Mock],
    browser_result: BrowserIntelligenceResult,
    deterministic_result: DeterministicPageAnalysisResult,
) -> None:
    client, service = client_and_service
    result = PageAnalysisResult(
        url="https://example.com/",
        status=AnalysisStatus.SUCCESS,
        browser_result=browser_result,
        intelligence=deterministic_result,
        ai_intelligence=AIIntelligenceResult(
            classification=AIPageClassification(
                category="marketing",
                confidence=0.9,
                reasoning="Clear product positioning.",
            ),
            summary="A marketing page.",
        ),
        duration_ms=15,
    )
    service.analyze.return_value = result

    response = client.post(
        "/api/v1/analyze",
        json={"url": "https://example.com", "use_ai": True},
    )

    assert response.status_code == 200
    assert response.json() == result.model_dump(mode="json")
    assert response.json()["ai_intelligence"]["summary"] == "A marketing page."


def test_use_ai_with_mock_provider_runs_complete_endpoint_workflow(
    browser_result: BrowserIntelligenceResult,
    deterministic_result: DeterministicPageAnalysisResult,
) -> None:
    service = PageAnalysisService(
        Mock(return_value=browser_result),
        Mock(return_value=deterministic_result),
        LLMIntelligenceEngine(MockAIEngine()),
    )
    app.dependency_overrides[get_page_analysis_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/analyze",
                json={"url": "https://example.com", "use_ai": True},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["intelligence"]["title"] == "Example"
    assert response.json()["ai_intelligence"]["classification"][
        "category"
    ] == "unknown"
    assert response.json()["errors"] == []


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (
            AnalysisStatus.PARTIAL_SUCCESS,
            AnalysisError(
                stage=AnalysisStage.INTELLIGENCE,
                code="ai_intelligence_failed",
                message="AI intelligence could not be completed.",
            ),
        ),
        (
            AnalysisStatus.FAILED,
            AnalysisError(
                stage=AnalysisStage.BROWSER,
                code="browser_analysis_failed",
                message="Browser analysis could not be completed.",
            ),
        ),
    ],
)
def test_controlled_workflow_outcomes_return_http_200_without_raw_details(
    client_and_service: tuple[TestClient, Mock],
    status: AnalysisStatus,
    error: AnalysisError,
) -> None:
    client, service = client_and_service
    result = PageAnalysisResult(
        url="https://example.com/",
        status=status,
        errors=[error],
        duration_ms=4,
    )
    service.analyze.return_value = result

    response = client.post(
        "/api/v1/analyze",
        json={"url": "https://example.com"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == status.value
    assert response.json()["errors"] == [error.model_dump(mode="json")]
    assert "provider secret" not in response.text
    assert "Traceback" not in response.text


@pytest.mark.parametrize(
    "body",
    [
        {"url": "not-a-valid-url"},
        None,
    ],
)
def test_invalid_request_returns_422_without_calling_service(
    client_and_service: tuple[TestClient, Mock],
    body: dict[str, str] | None,
) -> None:
    client, service = client_and_service

    response = client.post("/api/v1/analyze", json=body)

    assert response.status_code == 422
    service.analyze.assert_not_called()


def test_unexpected_route_exception_does_not_expose_details() -> None:
    service = Mock(spec=PageAnalysisService)
    service.analyze.side_effect = RuntimeError("provider secret")
    app.dependency_overrides[get_page_analysis_service] = lambda: service

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/analyze",
                json={"url": "https://example.com"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert "provider secret" not in response.text


def test_existing_root_and_health_endpoints_remain_functional(
    client_and_service: tuple[TestClient, Mock],
) -> None:
    client, _ = client_and_service

    assert client.get("/").status_code == 200
    assert client.get("/health").json()["status"] == "healthy"
