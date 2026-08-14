import pytest
from pydantic import ValidationError

from app.intelligence.models import (
    BrowserIntelligenceRequest,
    BrowserIntelligenceResult,
    ExtractionCategory,
    ExtractionWarning,
    ExtractionWarningCode,
    HeadingInfo,
    PageMetrics,
)


def test_browser_intelligence_request_accepts_valid_url() -> None:
    request = BrowserIntelligenceRequest(url="https://example.com")

    assert str(request.url).startswith("https://example.com")


def test_browser_intelligence_request_rejects_invalid_url() -> None:
    with pytest.raises(ValidationError):
        BrowserIntelligenceRequest(url="not-a-valid-url")


def test_browser_intelligence_result_uses_empty_collection_defaults() -> None:
    result = BrowserIntelligenceResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Example Domain",
        status_code=200,
        success=True,
        metrics=PageMetrics(load_time_ms=100),
    )

    assert result.headings == []
    assert result.links == []
    assert result.images == []
    assert result.forms == []
    assert result.buttons == []
    assert result.inputs == []
    assert result.console_errors == []
    assert result.warnings == []


def test_extraction_warning_has_typed_category_and_stable_safe_content() -> None:
    warning = ExtractionWarning(
        category=ExtractionCategory.HEADINGS,
        code=ExtractionWarningCode.HEADINGS_EXTRACTION_FAILED,
        message="Heading content could not be extracted.",
    )

    assert warning.category is ExtractionCategory.HEADINGS
    assert warning.code is ExtractionWarningCode.HEADINGS_EXTRACTION_FAILED
    assert warning.model_dump(mode="json") == {
        "category": "headings",
        "code": "headings_extraction_failed",
        "message": "Heading content could not be extracted.",
    }


def test_browser_intelligence_warning_lists_are_not_shared() -> None:
    first = BrowserIntelligenceResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="First",
        success=True,
        metrics=PageMetrics(load_time_ms=1),
    )
    second = BrowserIntelligenceResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Second",
        success=True,
        metrics=PageMetrics(load_time_ms=2),
    )

    first.warnings.append(
        ExtractionWarning(
            category="links",
            code="links_extraction_failed",
            message="Link content could not be extracted.",
        )
    )

    assert len(first.warnings) == 1
    assert second.warnings == []


def test_browser_result_serializes_multiple_warnings_with_success() -> None:
    result = BrowserIntelligenceResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Example",
        success=True,
        metrics=PageMetrics(load_time_ms=3),
        warnings=[
            ExtractionWarning(
                category="images",
                code="images_extraction_failed",
                message="Image content could not be extracted.",
            ),
            ExtractionWarning(
                category="forms",
                code="forms_extraction_failed",
                message="Form content could not be extracted.",
            ),
        ],
    )

    serialized = result.model_dump(mode="json")

    assert result.success is True
    assert serialized["warnings"] == [
        {
            "category": "images",
            "code": "images_extraction_failed",
            "message": "Image content could not be extracted.",
        },
        {
            "category": "forms",
            "code": "forms_extraction_failed",
            "message": "Form content could not be extracted.",
        },
    ]


def test_heading_level_must_be_between_one_and_six() -> None:
    with pytest.raises(ValidationError):
        HeadingInfo(level=7, text="Invalid heading")
