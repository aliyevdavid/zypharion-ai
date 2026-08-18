from unittest.mock import Mock, patch

import pytest

from app.ai import (
    AIIntelligenceEngine,
    AIIntelligenceResult,
    AIPageClassification,
)
from app.analysis import (
    PageAnalysisRequest,
    PageAnalysisService,
    create_page_analysis_service,
)
from app.api.main import app, get_page_analysis_service
from app.core.settings import Settings
from app.intelligence import (
    BrowserIntelligenceResult,
    PageAnalysisResult as DeterministicPageAnalysisResult,
    PageClassification,
    PageMetrics,
    PageType,
)


@pytest.fixture(autouse=True)
def clear_api_service_cache() -> None:
    get_page_analysis_service.cache_clear()
    yield
    get_page_analysis_service.cache_clear()
    app.dependency_overrides.clear()


def test_composition_preserves_and_uses_supplied_dependencies() -> None:
    browser_result = BrowserIntelligenceResult(
        requested_url="https://example.com/",
        final_url="https://example.com/",
        title="Example",
        success=True,
        metrics=PageMetrics(load_time_ms=1),
    )
    deterministic_result = DeterministicPageAnalysisResult(
        requested_url="https://example.com/",
        final_url="https://example.com/",
        title="Example",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.8,
            evidence=["Informational page structure detected"],
        ),
    )
    ai_result = AIIntelligenceResult(
        classification=AIPageClassification(
            category="marketing",
            confidence=0.9,
            reasoning="Page structure",
        ),
        summary="A marketing page.",
    )
    browser_analyzer = Mock(return_value=browser_result)
    deterministic_analyzer = Mock(return_value=deterministic_result)
    ai_engine = Mock(spec=AIIntelligenceEngine)
    ai_engine.analyze.return_value = ai_result

    service = create_page_analysis_service(
        Settings(),
        browser_analyzer=browser_analyzer,
        deterministic_analyzer=deterministic_analyzer,
        ai_engine=ai_engine,
    )

    assert isinstance(service, PageAnalysisService)
    assert service._browser_analyzer is browser_analyzer
    assert service._deterministic_analyzer is deterministic_analyzer
    assert service._ai_engine is ai_engine

    result = service.analyze(
        PageAnalysisRequest(url="https://example.com", use_ai=True)
    )

    browser_analyzer.assert_called_once_with("https://example.com/")
    deterministic_analyzer.assert_called_once_with(browser_result)
    ai_engine.analyze.assert_called_once_with(deterministic_result)
    assert result.ai_intelligence is ai_result


def test_explicit_ai_engine_bypasses_automatic_composition() -> None:
    ai_engine = Mock(spec=AIIntelligenceEngine)

    with patch(
        "app.analysis.composition.create_intelligence_engine"
    ) as create_engine:
        service = create_page_analysis_service(
            Settings(),
            browser_analyzer=Mock(),
            deterministic_analyzer=Mock(),
            ai_engine=ai_engine,
        )

    create_engine.assert_not_called()
    assert service._ai_engine is ai_engine


def test_explicit_settings_are_passed_to_ai_composition() -> None:
    settings = Settings(environment="test")
    composed_engine = Mock(spec=AIIntelligenceEngine)

    with patch(
        "app.analysis.composition.create_intelligence_engine",
        return_value=composed_engine,
    ) as create_engine:
        service = create_page_analysis_service(
            settings,
            browser_analyzer=Mock(),
            deterministic_analyzer=Mock(),
        )

        assert service._ai_engine_factory is not None
        assert service._ai_engine_factory() is composed_engine

    create_engine.assert_called_once_with(settings)


def test_omitted_settings_use_cached_settings() -> None:
    settings = Settings(environment="test")
    composed_engine = Mock(spec=AIIntelligenceEngine)

    with (
        patch(
            "app.analysis.composition.get_settings",
            return_value=settings,
        ) as get_settings,
        patch(
            "app.analysis.composition.create_intelligence_engine",
            return_value=composed_engine,
        ) as create_engine,
    ):
        service = create_page_analysis_service(
            browser_analyzer=Mock(),
            deterministic_analyzer=Mock(),
        )

        assert service._ai_engine_factory is not None
        assert service._ai_engine_factory() is composed_engine

    get_settings.assert_called_once_with()
    create_engine.assert_called_once_with(settings)


def test_deterministic_request_does_not_compose_ai_engine() -> None:
    browser_result = BrowserIntelligenceResult(
        requested_url="https://example.test/",
        final_url="https://example.test/",
        title="Example",
        success=True,
        metrics=PageMetrics(load_time_ms=1),
    )
    deterministic_result = DeterministicPageAnalysisResult(
        requested_url="https://example.test/",
        final_url="https://example.test/",
        title="Example",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.8,
        ),
    )

    with patch(
        "app.analysis.composition.create_intelligence_engine",
        side_effect=ValueError("invalid provider configuration"),
    ) as create_engine:
        service = create_page_analysis_service(
            Settings(ai_provider="unsupported"),
            browser_analyzer=Mock(return_value=browser_result),
            deterministic_analyzer=Mock(return_value=deterministic_result),
        )
        result = service.analyze(
            PageAnalysisRequest(url="https://example.test", use_ai=False)
        )

    create_engine.assert_not_called()
    assert result.status.value == "success"
    assert result.intelligence is deterministic_result


def test_ai_request_reports_invalid_provider_configuration() -> None:
    browser_result = BrowserIntelligenceResult(
        requested_url="https://example.test/",
        final_url="https://example.test/",
        title="Example",
        success=True,
        metrics=PageMetrics(load_time_ms=1),
    )
    deterministic_result = DeterministicPageAnalysisResult(
        requested_url="https://example.test/",
        final_url="https://example.test/",
        title="Example",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.8,
        ),
    )
    service = create_page_analysis_service(
        Settings(ai_provider="unsupported"),
        browser_analyzer=Mock(return_value=browser_result),
        deterministic_analyzer=Mock(return_value=deterministic_result),
    )

    result = service.analyze(
        PageAnalysisRequest(url="https://example.test", use_ai=True)
    )

    assert result.status.value == "partial_success"
    assert result.errors[0].code == "ai_intelligence_unavailable"


def test_composition_performs_no_analysis_work() -> None:
    browser_analyzer = Mock()
    deterministic_analyzer = Mock()
    ai_engine = Mock(spec=AIIntelligenceEngine)

    create_page_analysis_service(
        Settings(),
        browser_analyzer=browser_analyzer,
        deterministic_analyzer=deterministic_analyzer,
        ai_engine=ai_engine,
    )

    browser_analyzer.assert_not_called()
    deterministic_analyzer.assert_not_called()
    ai_engine.analyze.assert_not_called()


def test_api_dependency_returns_composed_cached_service() -> None:
    composed_service = Mock(spec=PageAnalysisService)

    with patch(
        "app.api.main.create_page_analysis_service",
        return_value=composed_service,
    ) as create_service:
        first = get_page_analysis_service()
        second = get_page_analysis_service()

    assert first is composed_service
    assert second is first
    create_service.assert_called_once_with()


def test_api_dependency_remains_overrideable() -> None:
    overridden_service = Mock(spec=PageAnalysisService)
    app.dependency_overrides[get_page_analysis_service] = (
        lambda: overridden_service
    )

    assert app.dependency_overrides[get_page_analysis_service]() is (
        overridden_service
    )
