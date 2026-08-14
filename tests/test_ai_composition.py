from dataclasses import dataclass, field
from unittest.mock import Mock, patch

import pytest

from app.ai import (
    AIEngine,
    AIIntelligenceEngine,
    LLMIntelligenceEngine,
    MockAIEngine,
    create_intelligence_engine,
)
from app.ai.page_intelligence_parser import (
    PageIntelligenceResponseParser,
)
from app.ai.prompts import PageIntelligencePromptBuilder
from app.ai.providers import AzureOpenAIEngine
from app.core.settings import Settings


@dataclass
class FakeResponsesAPI:
    calls: list[dict[str, object]] = field(default_factory=list)

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        raise AssertionError("Composition must not make a provider request")


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


def test_composition_uses_default_mock_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    engine = create_intelligence_engine(Settings())

    assert isinstance(engine, LLMIntelligenceEngine)
    assert isinstance(engine._ai_engine, MockAIEngine)


def test_composition_uses_explicit_mock_provider() -> None:
    engine = create_intelligence_engine(Settings(ai_provider="mock"))

    assert isinstance(engine._ai_engine, MockAIEngine)


def test_composition_uses_injected_azure_client_without_request() -> None:
    client = FakeAzureClient()

    engine = create_intelligence_engine(
        _azure_settings(),
        azure_client=client,
    )

    assert isinstance(engine._ai_engine, AzureOpenAIEngine)
    assert client.responses.calls == []


def test_injected_ai_engine_bypasses_provider_construction() -> None:
    provider = Mock(spec=AIEngine)

    with patch(
        "app.ai.composition.create_ai_provider",
        side_effect=AssertionError("Provider factory must be bypassed"),
    ):
        engine = create_intelligence_engine(
            Settings(ai_provider="unsupported"),
            ai_engine=provider,
        )

    assert engine._ai_engine is provider


def test_composition_wires_prompt_builder_and_response_parser() -> None:
    engine = create_intelligence_engine(Settings(ai_provider="mock"))

    assert isinstance(
        engine._prompt_builder,
        PageIntelligencePromptBuilder,
    )
    assert isinstance(
        engine._response_parser,
        PageIntelligenceResponseParser,
    )


def test_composed_engine_preserves_intelligence_contract() -> None:
    engine = create_intelligence_engine(Settings(ai_provider="mock"))

    assert isinstance(engine, AIIntelligenceEngine)


def test_composition_preserves_factory_azure_validation() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "AZURE_OPENAI_ENDPOINT is required when "
            "AI_PROVIDER=azure_openai"
        ),
    ):
        create_intelligence_engine(
            _azure_settings(azure_openai_endpoint=None),
            azure_client=FakeAzureClient(),
        )
