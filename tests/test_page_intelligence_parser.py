import json

import pytest

from app.ai import AIIntelligenceResult, RecommendationPriority
from app.ai.page_intelligence_parser import (
    AIResponseValidationError,
    PageIntelligenceResponseParser,
)


def _valid_response_data() -> dict:
    return {
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


def test_parser_returns_validated_intelligence_result() -> None:
    result = PageIntelligenceResponseParser().parse(
        json.dumps(_valid_response_data())
    )

    assert isinstance(result, AIIntelligenceResult)
    assert result.classification.category == "dashboard"
    assert (
        result.recommendations[0].priority
        is RecommendationPriority.MEDIUM
    )


def test_parser_rejects_malformed_json() -> None:
    with pytest.raises(AIResponseValidationError):
        PageIntelligenceResponseParser().parse("{not valid JSON")


def test_parser_rejects_missing_required_fields() -> None:
    with pytest.raises(AIResponseValidationError):
        PageIntelligenceResponseParser().parse(
            json.dumps({"summary": "Incomplete"})
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("confidence", 1.1),
        ("priority", "urgent"),
    ],
)
def test_parser_rejects_invalid_values(
    field: str,
    value: float | str,
) -> None:
    response_data = _valid_response_data()
    if field == "confidence":
        response_data["classification"]["confidence"] = value
    else:
        response_data["recommendations"][0]["priority"] = value

    with pytest.raises(AIResponseValidationError):
        PageIntelligenceResponseParser().parse(
            json.dumps(response_data)
        )
