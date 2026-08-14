from dataclasses import dataclass, field

import pytest

from app.ai import AIEngine, AIRequest, AIResponse
from app.ai.providers import AzureOpenAIEngine


@dataclass
class FakeProviderResponse:
    output_text: object


@dataclass
class FakeResponsesAPI:
    output_text: object = "Provider result"
    calls: list[dict[str, object]] = field(default_factory=list)
    error: Exception | None = None

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
        if self.error is not None:
            raise self.error

        return FakeProviderResponse(output_text=self.output_text)


@dataclass
class FakeClient:
    responses: FakeResponsesAPI


def _build_engine(
    *,
    output_text: object = "Provider result",
    deployment_name: str = "page-intelligence",
) -> tuple[AzureOpenAIEngine, FakeResponsesAPI]:
    responses = FakeResponsesAPI(output_text=output_text)
    client = FakeClient(responses=responses)

    return AzureOpenAIEngine(client, deployment_name), responses


def test_azure_engine_implements_ai_engine() -> None:
    engine, _ = _build_engine()

    assert isinstance(engine, AIEngine)
    assert engine.provider_name == "azure_openai"


def test_azure_engine_maps_request_and_response() -> None:
    engine, responses = _build_engine(
        output_text="  exact provider output  ",
        deployment_name="  azure-deployment  ",
    )
    request = AIRequest(
        instruction="Classify this page.",
        context='{"title":"Example"}',
        temperature=0.0,
    )

    result = engine.generate(request)

    assert responses.calls == [
        {
            "model": "azure-deployment",
            "input": request.prompt,
            "temperature": 0.0,
        }
    ]
    assert result == AIResponse(
        content="  exact provider output  ",
        provider="azure_openai",
        model="azure-deployment",
    )


def test_azure_engine_is_deterministic_for_identical_responses() -> None:
    engine, _ = _build_engine(output_text="Stable result")
    request = AIRequest(instruction="Analyze")

    first_result = engine.generate(request)
    second_result = engine.generate(request)

    assert first_result == second_result


@pytest.mark.parametrize("deployment_name", ["", "   "])
def test_azure_engine_rejects_empty_deployment_name(
    deployment_name: str,
) -> None:
    client = FakeClient(responses=FakeResponsesAPI())

    with pytest.raises(
        ValueError,
        match="deployment_name must not be empty",
    ):
        AzureOpenAIEngine(client, deployment_name)


def test_azure_engine_rejects_non_string_output() -> None:
    engine, _ = _build_engine(output_text=None)

    with pytest.raises(
        TypeError,
        match="response.output_text must be a string",
    ):
        engine.generate(AIRequest(instruction="Analyze"))


@pytest.mark.parametrize("output_text", ["", "   "])
def test_azure_engine_rejects_empty_output(
    output_text: str,
) -> None:
    engine, _ = _build_engine(output_text=output_text)

    with pytest.raises(
        ValueError,
        match="response.output_text must not be empty",
    ):
        engine.generate(AIRequest(instruction="Analyze"))


def test_azure_engine_propagates_provider_exception() -> None:
    provider_error = RuntimeError("Provider unavailable")
    responses = FakeResponsesAPI(error=provider_error)
    engine = AzureOpenAIEngine(
        FakeClient(responses=responses),
        "page-intelligence",
    )

    with pytest.raises(RuntimeError) as raised_error:
        engine.generate(AIRequest(instruction="Analyze"))

    assert raised_error.value is provider_error
