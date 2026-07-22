from unittest.mock import patch

from app.intelligence.models import BrowserIntelligenceResult, PageMetrics
from app.services.intelligence_service import IntelligenceService


def test_intelligence_service_delegates_to_extractor() -> None:
    expected_result = BrowserIntelligenceResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Example Domain",
        status_code=200,
        success=True,
        metrics=PageMetrics(load_time_ms=100),
    )

    service = IntelligenceService()

    with patch(
        "app.services.intelligence_service.analyze_page",
        return_value=expected_result,
    ) as mocked_analyze_page:
        result = service.analyze("https://example.com")

    mocked_analyze_page.assert_called_once_with("https://example.com")
    assert result == expected_result