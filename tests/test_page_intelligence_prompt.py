import json

from app.ai.models import AIRequest
from app.ai.prompts import PageIntelligencePromptBuilder
from app.intelligence.analysis_models import (
    AnalysisFinding,
    PageAnalysisResult,
    PageClassification,
    PageType,
)


def _build_analysis() -> PageAnalysisResult:
    return PageAnalysisResult(
        requested_url="https://example.com/requested",
        final_url="https://example.com/final",
        title="Example Dashboard",
        classification=PageClassification(
            page_type=PageType.DASHBOARD,
            confidence=0.85,
            evidence=["Dashboard-related text detected"],
        ),
        detected_features=["interactive_buttons"],
        findings=[
            AnalysisFinding(
                category="reliability",
                message="A console error was detected",
                severity="warning",
            )
        ],
        recommendations=["Investigate browser console errors"],
    )


def test_prompt_builder_returns_stable_provider_neutral_request() -> None:
    builder = PageIntelligencePromptBuilder()
    analysis = _build_analysis()

    first_request = builder.build(analysis)
    second_request = builder.build(analysis)

    assert isinstance(first_request, AIRequest)
    assert first_request.temperature == 0.0
    assert first_request == second_request


def test_prompt_builder_includes_only_relevant_analysis_data() -> None:
    request = PageIntelligencePromptBuilder().build(_build_analysis())
    context = json.loads(request.context)

    assert context == {
        "detected_features": ["interactive_buttons"],
        "deterministic_classification": {
            "confidence": 0.85,
            "evidence": ["Dashboard-related text detected"],
            "page_type": "dashboard",
        },
        "deterministic_recommendations": [
            "Investigate browser console errors"
        ],
        "final_url": "https://example.com/final",
        "findings": [
            {
                "category": "reliability",
                "message": "A console error was detected",
                "severity": "warning",
            }
        ],
        "title": "Example Dashboard",
    }
    assert "analysis_id" not in context
    assert "requested_url" not in context
