import json

from app.ai.engine import AIEngine
from app.ai.models import AIRequest, AIResponse


class MockAIEngine(AIEngine):
    """
    Deterministic AI engine used during local development and testing.

    It does not call an external model.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    def generate(self, request: AIRequest) -> AIResponse:
        context_summary = request.context or "No context supplied"
        content = {
            "classification": {
                "category": "unknown",
                "confidence": 1.0,
                "reasoning": (
                    "Deterministic mock classification for local validation."
                ),
            },
            "summary": "Deterministic mock page intelligence completed.",
            "recommendations": [],
        }

        return AIResponse(
            content=json.dumps(content, sort_keys=True),
            provider=self.provider_name,
            model="deterministic-mock-v1",
            metadata={
                "has_context": request.context is not None,
                "context_length": len(context_summary),
            },
        )
