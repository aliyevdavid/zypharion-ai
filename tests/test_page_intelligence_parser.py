import json
from collections.abc import Callable

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


@pytest.mark.parametrize(
    "content_builder",
    [
        lambda content: f"```json\n{content}\n```",
        lambda content: f"```\n{content}\n```",
        lambda content: f"Here is the result:\n{content}\nAnalysis complete.",
        lambda content: f" \n\t{content}\n ",
    ],
    ids=["json-fence", "generic-fence", "prose", "whitespace"],
)
def test_parser_normalizes_supported_provider_formats(
    content_builder: Callable[[str], str],
) -> None:
    content = content_builder(json.dumps(_valid_response_data()))

    result = PageIntelligenceResponseParser().parse(content)

    assert result.classification.category == "dashboard"


def test_parser_handles_nested_objects_and_json_string_syntax() -> None:
    response_data = _valid_response_data()
    response_data["classification"]["reasoning"] = (
        'A value with {braces}, an escaped quote: "yes", and nested data.'
    )

    result = PageIntelligenceResponseParser().parse(
        f"Provider output:\n{json.dumps(response_data)}\nEnd output."
    )

    assert "{braces}" in result.classification.reasoning
    assert '"yes"' in result.classification.reasoning


def test_parser_rejects_malformed_json() -> None:
    with pytest.raises(AIResponseValidationError):
        PageIntelligenceResponseParser().parse("{not valid JSON")


def test_parser_rejects_missing_required_fields() -> None:
    with pytest.raises(AIResponseValidationError):
        PageIntelligenceResponseParser().parse(
            json.dumps({"summary": "Incomplete"})
        )


@pytest.mark.parametrize(
    "content",
    [
        "There is no structured response here.",
        '{"first": true}\n{"second": true}',
        '[{"summary": "Array response"}]',
        '```json\n{"summary": "Missing closing fence"}',
        '```json\n{"summary": "Incomplete"} trailing text\n```',
        '```json\n{"summary": "Incomplete"}\n``` trailing text',
    ],
    ids=[
        "no-object",
        "multiple-objects",
        "top-level-array",
        "missing-fence",
        "content-inside-fence",
        "malformed-closing-fence",
    ],
)
def test_parser_rejects_unsafe_or_ambiguous_content(content: str) -> None:
    with pytest.raises(AIResponseValidationError):
        PageIntelligenceResponseParser().parse(content)


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
