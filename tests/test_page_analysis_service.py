from unittest.mock import Mock

import pytest

from app.ai import (
    AIEngine,
    AIIntelligenceEngine,
    AIIntelligenceResult,
    AIPageClassification,
    AIResponse,
    LLMIntelligenceEngine,
    MockAIEngine,
)
from app.analysis import (
    AnalysisStage,
    AnalysisStatus,
    PageAnalysisRequest,
    PageAnalysisService,
)
from app.intelligence import (
    BrowserIntelligenceResult,
    PageAnalysisResult as DeterministicPageAnalysisResult,
    PageClassification,
    PageMetrics,
    PageType,
)


@pytest.fixture
def browser_result() -> BrowserIntelligenceResult:
    return BrowserIntelligenceResult(
        requested_url="https://example.com/",
        final_url="https://example.com/final",
        title="Example",
        success=True,
        headings=[],
        metrics=PageMetrics(load_time_ms=12),
    )


@pytest.fixture
def intelligence() -> DeterministicPageAnalysisResult:
    return DeterministicPageAnalysisResult(
        requested_url="https://example.com/",
        final_url="https://example.com/final",
        title="Example",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.8,
            evidence=["Prominent heading content detected"],
        ),
        detected_features=["navigation_links"],
    )


@pytest.fixture
def ai_result() -> AIIntelligenceResult:
    return AIIntelligenceResult(
        classification=AIPageClassification(
            category="marketing",
            confidence=0.9,
            reasoning="Page structure",
        ),
        summary="A marketing page.",
    )


def test_successful_deterministic_only_analysis(
    browser_result: BrowserIntelligenceResult,
    intelligence: DeterministicPageAnalysisResult,
) -> None:
    browser = Mock(return_value=browser_result)
    deterministic = Mock(return_value=intelligence)
    ai_engine = Mock(spec=AIIntelligenceEngine)
    service = PageAnalysisService(browser, deterministic, ai_engine)

    result = service.analyze(
        PageAnalysisRequest(url="https://example.com", use_ai=False)
    )

    assert result.status is AnalysisStatus.SUCCESS
    assert result.url == "https://example.com/"
    assert result.browser_result is browser_result
    assert result.intelligence is intelligence
    assert result.ai_intelligence is None
    assert result.errors == []
    assert result.duration_ms is not None and result.duration_ms >= 0
    browser.assert_called_once_with("https://example.com/")
    deterministic.assert_called_once_with(browser_result)
    ai_engine.analyze.assert_not_called()


def test_successful_ai_analysis(
    browser_result: BrowserIntelligenceResult,
    intelligence: DeterministicPageAnalysisResult,
    ai_result: AIIntelligenceResult,
) -> None:
    browser = Mock(return_value=browser_result)
    deterministic = Mock(return_value=intelligence)
    ai_engine = Mock(spec=AIIntelligenceEngine)
    ai_engine.analyze.return_value = ai_result

    result = PageAnalysisService(
        browser, deterministic, ai_engine
    ).analyze(PageAnalysisRequest(url="https://example.com", use_ai=True))

    assert result.status is AnalysisStatus.SUCCESS
    assert result.ai_intelligence is ai_result
    browser.assert_called_once()
    deterministic.assert_called_once()
    ai_engine.analyze.assert_called_once_with(intelligence)


def test_mock_ai_analysis_returns_validated_intelligence(
    browser_result: BrowserIntelligenceResult,
    intelligence: DeterministicPageAnalysisResult,
) -> None:
    result = PageAnalysisService(
        Mock(return_value=browser_result),
        Mock(return_value=intelligence),
        LLMIntelligenceEngine(MockAIEngine()),
    ).analyze(PageAnalysisRequest(url="https://example.com", use_ai=True))

    assert result.status is AnalysisStatus.SUCCESS
    assert result.ai_intelligence is not None
    assert result.ai_intelligence.classification.category == "unknown"
    assert result.errors == []


def test_browser_exception_returns_safe_failure() -> None:
    browser = Mock(side_effect=RuntimeError("secret browser path"))
    deterministic = Mock()

    result = PageAnalysisService(browser, deterministic).analyze(
        PageAnalysisRequest(url="https://example.com")
    )

    assert result.status is AnalysisStatus.FAILED
    assert result.browser_result is None
    assert result.errors[0].stage is AnalysisStage.BROWSER
    assert result.errors[0].code == "browser_analysis_failed"
    assert "secret browser path" not in result.model_dump_json()
    browser.assert_called_once()
    deterministic.assert_not_called()


def test_unsuccessful_browser_result_is_preserved() -> None:
    browser_result = BrowserIntelligenceResult(
        requested_url="https://example.com/",
        final_url="https://example.com/",
        title="",
        success=False,
        metrics=PageMetrics(load_time_ms=3),
    )
    deterministic = Mock()

    result = PageAnalysisService(
        Mock(return_value=browser_result), deterministic
    ).analyze(PageAnalysisRequest(url="https://example.com"))

    assert result.status is AnalysisStatus.FAILED
    assert result.browser_result is browser_result
    assert result.errors[0].stage is AnalysisStage.BROWSER
    assert result.errors[0].code == "browser_analysis_failed"
    deterministic.assert_not_called()


def test_deterministic_failure_preserves_browser_data(
    browser_result: BrowserIntelligenceResult,
) -> None:
    deterministic = Mock(
        side_effect=ValueError("raw deterministic exception")
    )

    result = PageAnalysisService(
        Mock(return_value=browser_result), deterministic
    ).analyze(PageAnalysisRequest(url="https://example.com"))

    assert result.status is AnalysisStatus.PARTIAL_SUCCESS
    assert result.browser_result is browser_result
    assert result.intelligence is None
    assert result.errors[0].stage is AnalysisStage.INTELLIGENCE
    assert result.errors[0].code == "deterministic_intelligence_failed"
    assert "raw deterministic exception" not in result.model_dump_json()


def test_ai_failure_preserves_prior_results(
    browser_result: BrowserIntelligenceResult,
    intelligence: DeterministicPageAnalysisResult,
) -> None:
    ai_engine = Mock(spec=AIIntelligenceEngine)
    ai_engine.analyze.side_effect = RuntimeError("provider secret")

    result = PageAnalysisService(
        Mock(return_value=browser_result),
        Mock(return_value=intelligence),
        ai_engine,
    ).analyze(PageAnalysisRequest(url="https://example.com", use_ai=True))

    assert result.status is AnalysisStatus.PARTIAL_SUCCESS
    assert result.browser_result is browser_result
    assert result.intelligence is intelligence
    assert result.ai_intelligence is None
    assert result.errors[0].stage is AnalysisStage.INTELLIGENCE
    assert result.errors[0].code == "ai_intelligence_failed"
    assert "provider secret" not in result.model_dump_json()
    ai_engine.analyze.assert_called_once_with(intelligence)


@pytest.mark.parametrize(
    "provider_content",
    [
        "{malformed JSON",
        '{"summary":"Incomplete response"}',
        '```json\n{"summary":"Incomplete response"} trailing\n```',
    ],
)
def test_invalid_ai_response_preserves_prior_results(
    browser_result: BrowserIntelligenceResult,
    intelligence: DeterministicPageAnalysisResult,
    provider_content: str,
) -> None:
    provider = Mock(spec=AIEngine)
    provider.generate.return_value = AIResponse(
        content=provider_content,
        provider="test",
        model="test-model",
    )

    result = PageAnalysisService(
        Mock(return_value=browser_result),
        Mock(return_value=intelligence),
        LLMIntelligenceEngine(provider),
    ).analyze(PageAnalysisRequest(url="https://example.com", use_ai=True))

    assert result.status is AnalysisStatus.PARTIAL_SUCCESS
    assert result.browser_result is browser_result
    assert result.intelligence is intelligence
    assert result.ai_intelligence is None
    assert result.errors[0].code == "ai_response_invalid"
    assert result.errors[0].message == (
        "AI provider response could not be parsed or validated."
    )
    assert provider_content not in result.model_dump_json()


def test_missing_ai_dependency_is_safe(
    browser_result: BrowserIntelligenceResult,
    intelligence: DeterministicPageAnalysisResult,
) -> None:
    result = PageAnalysisService(
        Mock(return_value=browser_result),
        Mock(return_value=intelligence),
    ).analyze(PageAnalysisRequest(url="https://example.com", use_ai=True))

    assert result.status is AnalysisStatus.PARTIAL_SUCCESS
    assert result.browser_result is browser_result
    assert result.intelligence is intelligence
    assert result.errors[0].code == "ai_intelligence_unavailable"
    assert result.errors[0].stage is AnalysisStage.INTELLIGENCE


def test_clock_is_clamped_and_calls_do_not_share_errors(
    browser_result: BrowserIntelligenceResult,
    intelligence: DeterministicPageAnalysisResult,
) -> None:
    clock = Mock(side_effect=[2.0, 1.0, 3.0, 3.004])
    service = PageAnalysisService(
        Mock(return_value=browser_result),
        Mock(side_effect=[RuntimeError("failure"), intelligence]),
        clock=clock,
    )

    failed = service.analyze(PageAnalysisRequest(url="https://example.com"))
    succeeded = service.analyze(PageAnalysisRequest(url="https://example.com"))

    assert failed.duration_ms == 0
    assert failed.errors
    assert succeeded.duration_ms == 4
    assert succeeded.errors == []
    assert failed.errors is not succeeded.errors
    assert succeeded.intelligence is intelligence
