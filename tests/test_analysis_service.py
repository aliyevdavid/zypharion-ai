from unittest.mock import patch

from app.intelligence.analysis_models import (
    PageAnalysisResult,
    PageClassification,
    PageType,
)
from app.intelligence.models import (
    BrowserIntelligenceResult,
    PageMetrics,
)
from app.services import IntelligenceService


def test_analysis_service_runs_complete_pipeline() -> None:
    browser_result = BrowserIntelligenceResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Example Domain",
        status_code=200,
        success=True,
        metrics=PageMetrics(load_time_ms=100),
    )

    analysis_result = PageAnalysisResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Example Domain",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.90,
            evidence=["Example evidence"],
        ),
    )

    service = IntelligenceService()

    with (
        patch.object(
            service,
            "analyze_browser",
            return_value=browser_result,
        ) as browser_mock,
        patch(
            "app.services.intelligence_service.analyze_browser_intelligence",
            return_value=analysis_result,
        ) as analyzer_mock,
    ):
        result = service.analyze_page("https://example.com")

    browser_mock.assert_called_once_with("https://example.com")
    analyzer_mock.assert_called_once_with(browser_result)

    assert result == analysis_result