import pytest
from pydantic import ValidationError

from app.intelligence.analysis_models import (
    AnalysisFinding,
    PageAnalysisRequest,
    PageAnalysisResult,
    PageClassification,
    PageType,
)


def test_page_analysis_request_accepts_valid_url() -> None:
    request = PageAnalysisRequest(url="https://example.com")

    assert str(request.url).startswith("https://example.com")


def test_page_analysis_request_rejects_invalid_url() -> None:
    with pytest.raises(ValidationError):
        PageAnalysisRequest(url="not-a-valid-url")


def test_page_classification_accepts_valid_confidence() -> None:
    classification = PageClassification(
        page_type=PageType.AUTHENTICATION,
        confidence=0.95,
        evidence=[
            "Password input detected",
            "Login form detected",
        ],
    )

    assert classification.page_type == PageType.AUTHENTICATION
    assert classification.confidence == 0.95
    assert len(classification.evidence) == 2


def test_page_classification_rejects_confidence_above_one() -> None:
    with pytest.raises(ValidationError):
        PageClassification(
            page_type=PageType.UNKNOWN,
            confidence=1.1,
        )


def test_page_classification_rejects_negative_confidence() -> None:
    with pytest.raises(ValidationError):
        PageClassification(
            page_type=PageType.UNKNOWN,
            confidence=-0.1,
        )


def test_page_analysis_result_uses_empty_collection_defaults() -> None:
    result = PageAnalysisResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title="Example Domain",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.75,
            evidence=["Informational page structure detected"],
        ),
    )

    assert result.detected_features == []
    assert result.findings == []
    assert result.recommendations == []


def test_analysis_finding_uses_default_info_severity() -> None:
    finding = AnalysisFinding(
        category="accessibility",
        message="Image without alternative text detected",
    )

    assert finding.severity == "info"