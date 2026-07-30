import json
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.ai import (
    AIEngine,
    AIIntelligenceResult,
    AIResponse,
    LLMIntelligenceEngine,
    RecommendationPriority,
)
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


def _valid_content() -> str:
    return json.dumps(
        {
            "classification": {
                "category": "dashboard",
                "confidence": 0.9,
                "reasoning": "Dashboard controls were detected.",
            },
            "summary": "An interactive application dashboard.",
            "recommendations": [
                {
                    "title": "Resolve console errors",
                    "description": "Investigate the detected error.",
                    "priority": "medium",
                }
            ],
        }
    )


def _build_engine(content: str) -> tuple[LLMIntelligenceEngine, Mock]:
    provider = Mock(spec=AIEngine)
    provider.generate.return_value = AIResponse(
        content=content,
        provider="test",
        model="test-model",
    )
    return LLMIntelligenceEngine(provider), provider


def test_llm_engine_sends_relevant_analysis_data_to_provider() -> None:
    engine, provider = _build_engine(_valid_content())

    engine.analyze(_build_analysis())

    provider.generate.assert_called_once()
    request = provider.generate.call_args.args[0]
    context = json.loads(request.context)

    assert request.temperature == 0.0
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


def test_llm_engine_parses_valid_structured_response() -> None:
    engine, _ = _build_engine(_valid_content())

    result = engine.analyze(_build_analysis())

    assert isinstance(result, AIIntelligenceResult)
    assert result.classification.category == "dashboard"
    assert result.summary == "An interactive application dashboard."
    assert (
        result.recommendations[0].priority
        is RecommendationPriority.MEDIUM
    )


def test_llm_engine_rejects_malformed_json() -> None:
    engine, _ = _build_engine("{not valid JSON")

    with pytest.raises(json.JSONDecodeError):
        engine.analyze(_build_analysis())


def test_llm_engine_rejects_missing_required_fields() -> None:
    engine, _ = _build_engine(json.dumps({"summary": "Incomplete"}))

    with pytest.raises(ValidationError):
        engine.analyze(_build_analysis())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("confidence", 1.1),
        ("priority", "urgent"),
    ],
)
def test_llm_engine_rejects_invalid_values(
    field: str,
    value: float | str,
) -> None:
    response_data = json.loads(_valid_content())
    if field == "confidence":
        response_data["classification"]["confidence"] = value
    else:
        response_data["recommendations"][0]["priority"] = value
    engine, _ = _build_engine(json.dumps(response_data))

    with pytest.raises(ValidationError):
        engine.analyze(_build_analysis())


def test_llm_engine_is_stable_for_identical_input_and_response() -> None:
    engine, provider = _build_engine(_valid_content())
    analysis = _build_analysis()

    first_result = engine.analyze(analysis)
    second_result = engine.analyze(analysis)

    assert first_result == second_result
    first_request = provider.generate.call_args_list[0].args[0]
    second_request = provider.generate.call_args_list[1].args[0]
    assert first_request == second_request
    assert provider.generate.call_count == 2
