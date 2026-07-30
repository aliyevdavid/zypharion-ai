import json

import pytest
from pydantic import ValidationError

from app.ai import AIIntelligenceResult, AIRequest, MockAIEngine


def test_mock_ai_engine_returns_structured_response() -> None:
    engine = MockAIEngine()
    request = AIRequest(
        instruction="Analyze the login page",
        context="The login page contains username and password fields.",
    )

    response = engine.generate(request)

    assert response.provider == "mock"
    assert response.model == "deterministic-mock-v1"
    parsed = AIIntelligenceResult.model_validate(json.loads(response.content))
    assert parsed.classification.category == "unknown"
    assert parsed.summary == "Deterministic mock page intelligence completed."
    assert parsed.recommendations == []
    assert response.metadata["has_context"] is True


def test_ai_request_rejects_empty_instruction() -> None:
    with pytest.raises(ValidationError):
        AIRequest(instruction="")
