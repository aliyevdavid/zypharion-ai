import pytest
from pydantic import ValidationError

from app.ai import AIRequest, MockAIEngine


def test_mock_ai_engine_returns_structured_response() -> None:
    engine = MockAIEngine()
    request = AIRequest(
        instruction="Analyze the login page",
        context="The login page contains username and password fields.",
    )

    response = engine.generate(request)

    assert response.provider == "mock"
    assert response.model == "deterministic-mock-v1"
    assert "Analyze the login page" in response.content
    assert response.metadata["has_context"] is True


def test_ai_request_rejects_empty_instruction() -> None:
    with pytest.raises(ValidationError):
        AIRequest(instruction="")