from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.main import app
from app.intelligence.analysis_models import (
    IntelligenceExplanation,
    PageAnalysisResult,
    PageClassification,
    PageType,
)
from app.intelligence.evidence_models import (
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
)


client = TestClient(app)

TEST_ANALYSIS_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)


def test_page_analysis_endpoint_returns_explainable_result() -> None:
    mocked_result = PageAnalysisResult(
        analysis_id=TEST_ANALYSIS_ID,
        requested_url="https://example.com/",
        final_url="https://example.com/",
        title="Example Domain",
        classification=PageClassification(
            page_type=PageType.MARKETING,
            confidence=0.75,
            evidence=[
                "Prominent heading content detected",
                "Informational page structure detected",
            ],
            structured_evidence=[
                EvidenceItem(
                    type=EvidenceType.STRUCTURE,
                    source=EvidenceSource.DETERMINISTIC,
                    description=description,
                )
                for description in (
                    "Prominent heading content detected",
                    "Informational page structure detected",
                )
            ],
            explanation=IntelligenceExplanation(
                conclusion="marketing",
                confidence=0.75,
                evidence=[
                    EvidenceItem(
                        type=EvidenceType.STRUCTURE,
                        source=EvidenceSource.DETERMINISTIC,
                        description=description,
                    )
                    for description in (
                        "Prominent heading content detected",
                        "Informational page structure detected",
                    )
                ],
            ),
        ),
        detected_features=[
            "navigation_links",
        ],
        findings=[],
        recommendations=[
            "Add this page to automated smoke-test coverage",
        ],
    )

    with patch(
        "app.api.main.intelligence_service.analyze_page",
        return_value=mocked_result,
    ) as mocked_analyze_page:
        response = client.post(
            "/ai/analyze",
            json={
                "url": "https://example.com",
            },
        )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body["analysis_id"] == str(TEST_ANALYSIS_ID)
    assert response_body["requested_url"] == "https://example.com/"
    assert response_body["final_url"] == "https://example.com/"
    assert response_body["title"] == "Example Domain"

    assert response_body["classification"] == {
        "page_type": "marketing",
        "confidence": 0.75,
        "evidence": [
            "Prominent heading content detected",
            "Informational page structure detected",
        ],
        "structured_evidence": [
            {
                "type": "structure",
                "source": "deterministic",
                "description": description,
                "confidence": None,
                "severity": None,
            }
            for description in (
                "Prominent heading content detected",
                "Informational page structure detected",
            )
        ],
        "explanation": {
            "conclusion": "marketing",
            "confidence": 0.75,
            "evidence": [
                {
                    "type": "structure",
                    "source": "deterministic",
                    "description": description,
                    "confidence": None,
                    "severity": None,
                }
                for description in (
                    "Prominent heading content detected",
                    "Informational page structure detected",
                )
            ],
            "uncertainty": None,
        },
    }

    assert response_body["detected_features"] == [
        "navigation_links",
    ]

    assert response_body["findings"] == []

    assert response_body["recommendations"] == [
        "Add this page to automated smoke-test coverage",
    ]

    mocked_analyze_page.assert_called_once_with(
        "https://example.com/"
    )


def test_page_analysis_endpoint_rejects_invalid_url() -> None:
    with patch(
        "app.api.main.intelligence_service.analyze_page",
    ) as mocked_analyze_page:
        response = client.post(
            "/ai/analyze",
            json={
                "url": "not-a-valid-url",
            },
        )

    assert response.status_code == 422
    mocked_analyze_page.assert_not_called()
