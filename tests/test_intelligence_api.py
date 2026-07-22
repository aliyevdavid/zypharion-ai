from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.main import app
from app.intelligence.models import BrowserIntelligenceResult, PageMetrics


client = TestClient(app)


def test_intelligence_analyze_endpoint_returns_structured_result() -> None:
    mocked_result = BrowserIntelligenceResult(
        requested_url="https://example.com/",
        final_url="https://example.com/",
        title="Example Domain",
        meta_description=None,
        canonical_url=None,
        status_code=200,
        success=True,
        metrics=PageMetrics(load_time_ms=125),
    )

    with patch(
        "app.api.main.intelligence_service.analyze_browser",
        return_value=mocked_result,
    ) as mocked_analyze:
        response = client.post(
            "/intelligence/analyze",
            json={"url": "https://example.com"},
        )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body["title"] == "Example Domain"
    assert response_body["status_code"] == 200
    assert response_body["success"] is True
    assert response_body["headings"] == []
    assert response_body["links"] == []
    assert response_body["metrics"]["load_time_ms"] == 125

    mocked_analyze.assert_called_once_with("https://example.com/")


def test_intelligence_analyze_endpoint_rejects_invalid_url() -> None:
    response = client.post(
        "/intelligence/analyze",
        json={"url": "not-a-valid-url"},
    )

    assert response.status_code == 422