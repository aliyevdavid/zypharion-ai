from abc import ABC, abstractmethod

from app.ai.models import AIRequest, AIResponse


class AIEngine(ABC):
    """
    Provider-independent contract for Zypharion AI engines.

    Concrete implementations may call OpenAI, Azure OpenAI,
    a local model, or a deterministic mock used by automated tests.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate an AI response for a validated request."""
        raise NotImplementedError