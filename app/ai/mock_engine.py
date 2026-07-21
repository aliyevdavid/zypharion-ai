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

        return AIResponse(
            content=(
                "Mock analysis completed for instruction: "
                f"{request.instruction}"
            ),
            provider=self.provider_name,
            model="deterministic-mock-v1",
            metadata={
                "has_context": request.context is not None,
                "context_length": len(context_summary),
            },
        )