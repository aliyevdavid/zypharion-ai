from typing import Protocol, final

from app.ai.engine import AIEngine
from app.ai.models import AIRequest, AIResponse


class _ProviderResponse(Protocol):
    output_text: object


class _ResponsesAPI(Protocol):
    def create(
        self,
        *,
        model: str,
        input: str,
        temperature: float,
    ) -> _ProviderResponse:
        """Create a provider response."""
        ...


class _OpenAICompatibleClient(Protocol):
    responses: _ResponsesAPI


@final
class AzureOpenAIEngine(AIEngine):
    """
    Provider adapter for an injected Azure OpenAI-compatible client.
    """

    def __init__(
        self,
        client: _OpenAICompatibleClient,
        deployment_name: str,
    ) -> None:
        normalized_deployment_name = deployment_name.strip()
        if not normalized_deployment_name:
            raise ValueError("deployment_name must not be empty")

        self._client = client
        self._deployment_name = normalized_deployment_name

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    def generate(self, request: AIRequest) -> AIResponse:
        response = self._client.responses.create(
            model=self._deployment_name,
            input=request.prompt,
            temperature=request.temperature,
        )
        output_text = response.output_text

        if not isinstance(output_text, str):
            raise TypeError("response.output_text must be a string")

        if not output_text.strip():
            raise ValueError("response.output_text must not be empty")

        return AIResponse(
            content=output_text,
            provider=self.provider_name,
            model=self._deployment_name,
        )
