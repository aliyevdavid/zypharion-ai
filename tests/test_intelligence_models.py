import pytest
from pydantic import ValidationError

from app.intelligence.models import (
    BrowserIntelligenceRequest,
    BrowserIntelligenceResult,
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


def test_heading_level_must_be_between_one_and_six() -> None:
    with pytest.raises(ValidationError):
        HeadingInfo(level=7, text="Invalid heading")