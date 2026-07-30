import json

import pytest
from pydantic import ValidationError

from app.ai import (
    AIIntelligenceResult,
    AIPageClassification,
)
from app.analysis import (
    AnalysisError,
    AnalysisStage,
    AnalysisStatus,
    PageAnalysisRequest,
    PageAnalysisResult,
)
from app.intelligence import (
    BrowserIntelligenceResult,
    PageClassification,
    PageMetrics,
    PageType,
)
from app.intelligence import (
    PageAnalysisResult as DeterministicPageAnalysisResult,
)


@pytest.mark.parametrize(
    ("url", "normalized_url"),
    [
        ("http://example.com", "http://example.com/"),
        ("https://example.com/path", "https://example.com/path"),
    ],
)
def test_request_accepts_http_urls(
    url: str,
    normalized_url: str,
) -> None:
    request = PageAnalysisRequest(url=url)

    assert str(request.url) == normalized_url


def test_request_rejects_invalid_url() -> None:
    with pytest.raises(ValidationError):
        PageAnalysisRequest(url="not-a-url")


def test_request_defaults_to_deterministic_mode() -> None:
    request = PageAnalysisRequest(url="https://example.com")

    assert request.use_ai is False


def test_request_accepts_explicit_ai_mode() -> None:
    request = PageAnalysisRequest(
        url="https://example.com",
        use_ai=True,
    )

    assert request.use_ai is True


def test_success_result_serializes_existing_nested_models() -> None:
    browser_result = _browser_result()
    intelligence = _deterministic_result()
    ai_intelligence = AIIntelligenceResult(
        classification=AIPageClassification(
            category="marketing",
            confidence=0.9,
            reasoning="Informational page structure detected",
        ),
        summary="An example marketing page.",
    )
    result = PageAnalysisResult(
        url="https://example.com/",
        status=AnalysisStatus.SUCCESS,
        browser_result=browser_result,
        intelligence=intelligence,
        ai_intelligence=ai_intelligence,
        duration_ms=125,
    )

    payload = result.model_dump(mode="json")

    assert payload["status"] == "success"
    assert payload["browser_result"]["title"] == "Example Domain"
    assert payload["intelligence"]["classification"]["page_type"] == "marketing"
    assert payload["ai_intelligence"]["summary"] == "An example marketing page."
    assert payload["errors"] == []
    json.dumps(payload)


def test_partial_success_result_preserves_available_data() -> None:
    error = AnalysisError(
        stage=AnalysisStage.INTELLIGENCE,
        code="ai_unavailable",
        message="AI intelligence could not be completed.",
    )
    result = PageAnalysisResult(
        url="https://example.com/",
        status=AnalysisStatus.PARTIAL_SUCCESS,
        browser_result=_browser_result(),
        errors=[error],
    )

    assert result.browser_result is not None
    assert result.intelligence is None
    assert result.errors == [error]


def test_failed_result_contains_safe_structured_error() -> None:
    result = PageAnalysisResult(
        url="https://example.com/",
        status=AnalysisStatus.FAILED,
        errors=[
            AnalysisError(
                stage=AnalysisStage.BROWSER,
                code="navigation_failed",
                message="The page could not be loaded.",
            )
        ],
    )

    assert result.browser_result is None
    assert result.errors[0].stage is AnalysisStage.BROWSER
    assert result.errors[0].code == "navigation_failed"


def test_error_list_defaults_to_empty_without_sharing() -> None:
    first = PageAnalysisResult(
        url="https://example.com/",
        status=AnalysisStatus.SUCCESS,
    )
    second = PageAnalysisResult(
        url="https://example.org/",
        status=AnalysisStatus.SUCCESS,
    )

    first.errors.append(
        AnalysisError(
            stage=AnalysisStage.EXTRACTION,
            code="content_unreadable",
            message="Some page content could not be read.",
        )
    )

    assert second.errors == []


def _browser_result() -> BrowserIntelligenceResult:
    return BrowserIntelligenceResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Example Domain",
        status_code=200,
        success=True,
        metrics=PageMetrics(load_time_ms=100),
    )


def _deterministic_result() -> DeterministicPageAnalysisResult:
    return DeterministicPageAnalysisResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Example Domain",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.9,
            evidence=["Informational page structure detected"],
        ),
    )
