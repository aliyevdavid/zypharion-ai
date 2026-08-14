from unittest.mock import Mock, patch

import pytest

from app.ai import (
    AIIntelligenceEngine,
    AIIntelligenceResult,
    AIPageClassification,
    AIRecommendation,
    RecommendationPriority,
)
from app.intelligence.analysis_models import (
    PageAnalysisResult,
    PageClassification,
    PageType,
)
from app.intelligence.models import (
    BrowserIntelligenceResult,
    PageMetrics,
)
from app.services import IntelligenceService, PageIntelligenceResult


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


def test_enhanced_pipeline_runs_ai_after_deterministic_analysis() -> None:
    analysis_result = _build_analysis_result()
    ai_result = _build_ai_result()
    call_order: list[str] = []
    engine = Mock(spec=AIIntelligenceEngine)

    def analyze_deterministically(
        url: str,
    ) -> PageAnalysisResult:
        call_order.append("deterministic")
        return analysis_result

    def analyze_with_ai(
        analysis: PageAnalysisResult,
    ) -> AIIntelligenceResult:
        call_order.append("ai")
        assert analysis is analysis_result
        return ai_result

    engine.analyze.side_effect = analyze_with_ai
    service = IntelligenceService(ai_engine=engine)

    with patch.object(
        service,
        "analyze_page",
        side_effect=analyze_deterministically,
    ):
        result = service.analyze_page_with_ai("https://example.com")

    assert call_order == ["deterministic", "ai"]
    engine.analyze.assert_called_once_with(analysis_result)
    assert result == PageIntelligenceResult(
        page_analysis=analysis_result,
        ai_intelligence=ai_result,
    )


def test_enhanced_pipeline_default_engine_is_deterministic() -> None:
    analysis_result = _build_analysis_result()
    service = IntelligenceService()

    with patch.object(
        service,
        "analyze_page",
        return_value=analysis_result,
    ):
        first_result = service.analyze_page_with_ai(
            "https://example.com"
        )
        second_result = service.analyze_page_with_ai(
            "https://example.com"
        )

    assert first_result.ai_intelligence == second_result.ai_intelligence
    assert first_result.page_analysis is analysis_result


def test_enhanced_pipeline_propagates_ai_engine_failure() -> None:
    analysis_result = _build_analysis_result()
    engine = Mock(spec=AIIntelligenceEngine)
    engine.analyze.side_effect = RuntimeError("AI engine failed")
    service = IntelligenceService(ai_engine=engine)

    with (
        patch.object(
            service,
            "analyze_page",
            return_value=analysis_result,
        ),
        pytest.raises(RuntimeError, match="AI engine failed"),
    ):
        service.analyze_page_with_ai("https://example.com")


def _build_analysis_result() -> PageAnalysisResult:
    return PageAnalysisResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Example Domain",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.90,
            evidence=["Example evidence"],
        ),
        recommendations=["Add smoke-test coverage"],
    )


def _build_ai_result() -> AIIntelligenceResult:
    return AIIntelligenceResult(
        classification=AIPageClassification(
            category="marketing",
            confidence=0.90,
            reasoning="Example evidence",
        ),
        summary="Example summary",
        recommendations=[
            AIRecommendation(
                title="Recommendation 1",
                description="Add smoke-test coverage",
                priority=RecommendationPriority.MEDIUM,
            )
        ],
    )
