import pytest
from pydantic import ValidationError

from app.ai import (
    AIIntelligenceResult,
    AIPageClassification,
    AIRecommendation,
    DeterministicIntelligenceEngine,
    RecommendationPriority,
)
from app.intelligence.analysis_models import (
    AnalysisFinding,
    PageAnalysisResult,
    PageClassification,
    PageType,
)


def _build_analysis(
    *,
    title: str = "Sign In",
    page_type: PageType = PageType.AUTHENTICATION,
    evidence: list[str] | None = None,
    detected_features: list[str] | None = None,
    findings: list[AnalysisFinding] | None = None,
    recommendations: list[str] | None = None,
) -> PageAnalysisResult:
    return PageAnalysisResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title=title,
        classification=PageClassification(
            page_type=page_type,
            confidence=0.8,
            evidence=(
                evidence
                if evidence is not None
                else ["Password input detected"]
            ),
        ),
        detected_features=detected_features or [],
        findings=findings or [],
        recommendations=recommendations or [],
    )


def test_engine_returns_typed_intelligence_result() -> None:
    result = DeterministicIntelligenceEngine().analyze(_build_analysis())

    assert isinstance(result, AIIntelligenceResult)
    assert result.classification.category == "authentication"
    assert result.classification.confidence == 0.8
    assert result.classification.reasoning == "Password input detected"
    assert "deterministically classified" in result.summary


def test_engine_returns_stable_output_for_same_analysis() -> None:
    engine = DeterministicIntelligenceEngine()
    analysis = _build_analysis(
        detected_features=["forms", "password_input"],
    )

    first_result = engine.analyze(analysis)
    second_result = engine.analyze(analysis)

    assert first_result == second_result


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_ai_classification_rejects_invalid_confidence(
    confidence: float,
) -> None:
    with pytest.raises(ValidationError):
        AIPageClassification(
            category="unknown",
            confidence=confidence,
            reasoning="Test reasoning",
        )


def test_engine_structures_existing_recommendations() -> None:
    analysis = _build_analysis(
        recommendations=[
            "Add this page to automated smoke-test coverage",
            "Create negative validation tests",
        ]
    )

    recommendations = (
        DeterministicIntelligenceEngine()
        .analyze(analysis)
        .recommendations
    )

    assert [item.title for item in recommendations] == [
        "Recommendation 1",
        "Recommendation 2",
    ]
    assert recommendations[0].description == (
        "Add this page to automated smoke-test coverage"
    )
    assert all(
        item.priority is RecommendationPriority.MEDIUM
        for item in recommendations
    )
    assert recommendations[0].model_dump(mode="json")["priority"] == "medium"


def test_ai_recommendation_rejects_invalid_priority() -> None:
    with pytest.raises(ValidationError):
        AIRecommendation(
            title="Invalid priority",
            description="This should not validate.",
            priority="urgent",
        )


def test_engine_handles_minimal_analysis() -> None:
    analysis = _build_analysis(
        title="",
        page_type=PageType.UNKNOWN,
        evidence=[],
    )

    result = DeterministicIntelligenceEngine().analyze(analysis)

    assert result.classification.category == "unknown"
    assert result.classification.reasoning == (
        "No classification evidence was available."
    )
    assert result.summary.startswith(
        "Untitled page was deterministically classified as unknown."
    )
    assert result.recommendations == []
