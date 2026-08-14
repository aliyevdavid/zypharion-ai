from dataclasses import dataclass, field

import pytest

from app.ai import AIRequest, MockAIEngine
from app.ai.providers import AzureOpenAIEngine, create_ai_provider
from app.core.settings import Settings


@dataclass
class FakeProviderResponse:
    output_text: str = "Provider result"


@dataclass
class FakeResponsesAPI:
    calls: list[dict[str, object]] = field(default_factory=list)

    def create(
        self,
        *,
        model: str,
        input: str,
        temperature: float,
    ) -> FakeProviderResponse:
        self.calls.append(
            {
                "model": model,
                "input": input,
                "temperature": temperature,
            }
        )
        return FakeProviderResponse()


@dataclass
class FakeAzureClient:
    responses: FakeResponsesAPI = field(default_factory=FakeResponsesAPI)


def _azure_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "ai_provider": "azure_openai",
        "azure_openai_endpoint": "https://example.openai.azure.com/",
        "azure_openai_api_key": "test-key",
        "azure_openai_deployment": "test-deployment",
        "azure_openai_api_version": "2024-10-21",
    }
    values.update(overrides)
    return Settings(**values)


def test_factory_selects_mock_provider() -> None:
    provider = create_ai_provider(Settings(ai_provider="mock"))

    assert isinstance(provider, MockAIEngine)


def test_factory_selects_azure_openai_provider() -> None:
    provider = create_ai_provider(
        _azure_settings(),
        azure_client=FakeAzureClient(),
    )

    assert isinstance(provider, AzureOpenAIEngine)


def test_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported AI provider: 'other'"):
        create_ai_provider(Settings(ai_provider="other"))


@pytest.mark.parametrize(
    ("setting_name", "environment_name"),
    [
        ("azure_openai_endpoint", "AZURE_OPENAI_ENDPOINT"),
        ("azure_openai_api_key", "AZURE_OPENAI_API_KEY"),
        ("azure_openai_deployment", "AZURE_OPENAI_DEPLOYMENT"),
        ("azure_openai_api_version", "AZURE_OPENAI_API_VERSION"),
    ],
)
def test_factory_requires_azure_settings(
    setting_name: str,
    environment_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            f"{environment_name} is required when "
            "AI_PROVIDER=azure_openai"
        ),
    ):
        create_ai_provider(_azure_settings(**{setting_name: "  "}))


def test_factory_uses_injected_azure_client() -> None:
    client = FakeAzureClient()
    provider = create_ai_provider(
        _azure_settings(azure_openai_deployment=" injected-deployment "),
        azure_client=client,
    )
    request = AIRequest(instruction="Analyze", temperature=0.0)

    result = provider.generate(request)

    assert client.responses.calls == [
        {
            "model": "injected-deployment",
            "input": request.prompt,
            "temperature": 0.0,
        }
    ]
    assert result.provider == "azure_openai"


@pytest.mark.parametrize(
    "provider_name",
    ["MOCK", " mock ", "Azure_OpenAI", " AZURE_OPENAI "],
)
def test_factory_normalizes_provider_name(provider_name: str) -> None:
    settings = _azure_settings(ai_provider=provider_name)
    client = FakeAzureClient()

    provider = create_ai_provider(settings, azure_client=client)

    expected_type = (
        MockAIEngine
        if provider_name.strip().lower() == "mock"
        else AzureOpenAIEngine
    )
    assert isinstance(provider, expected_type)
