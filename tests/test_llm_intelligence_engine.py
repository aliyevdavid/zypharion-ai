from unittest.mock import Mock

from app.ai import (
    AIEngine,
    AIIntelligenceResult,
    AIPageClassification,
    AIRecommendation,
    AIRequest,
    AIResponse,
    LLMIntelligenceEngine,
    RecommendationPriority,
)
from app.ai.page_intelligence_parser import (
    PageIntelligenceResponseParser,
)
from app.ai.prompts import PageIntelligencePromptBuilder
from app.intelligence.analysis_models import (
    PageAnalysisResult,
    PageClassification,
    PageType,
)


def _build_analysis() -> PageAnalysisResult:
    return PageAnalysisResult(
        requested_url="https://example.com/requested",
        final_url="https://example.com/final",
        title="Example Dashboard",
        classification=PageClassification(
            page_type=PageType.DASHBOARD,
            confidence=0.85,
            evidence=["Dashboard-related text detected"],
        ),
    )


def _build_result() -> AIIntelligenceResult:
    return AIIntelligenceResult(
        classification=AIPageClassification(
            category="dashboard",
            confidence=0.9,
            reasoning="Dashboard controls were detected.",
        ),
        summary="An interactive application dashboard.",
        recommendations=[
            AIRecommendation(
                title="Test dashboard",
                description="Add dashboard coverage.",
                priority=RecommendationPriority.MEDIUM,
            )
        ],
    )


def _result_content() -> str:
    return _build_result().model_dump_json()


def test_llm_engine_orchestrates_injected_dependencies() -> None:
    analysis = _build_analysis()
    request = AIRequest(instruction="Test request")
    response = AIResponse(
        content="exact provider content",
        provider="test",
        model="test-model",
    )
    result = _build_result()
    prompt_builder = Mock(spec=PageIntelligencePromptBuilder)
    prompt_builder.build.return_value = request
    provider = Mock(spec=AIEngine)
    provider.generate.return_value = response
    parser = Mock(spec=PageIntelligenceResponseParser)
    parser.parse.return_value = result
    engine = LLMIntelligenceEngine(
        provider,
        prompt_builder=prompt_builder,
        response_parser=parser,
    )

    actual_result = engine.analyze(analysis)

    prompt_builder.build.assert_called_once_with(analysis)
    assert prompt_builder.build.call_args.args[0] is analysis
    provider.generate.assert_called_once_with(request)
    assert provider.generate.call_args.args[0] is request
    parser.parse.assert_called_once_with(response.content)
    assert parser.parse.call_args.args[0] is response.content
    assert actual_result is result


def test_llm_engine_is_stable_with_deterministic_dependencies() -> None:
    provider = Mock(spec=AIEngine)
    provider.generate.return_value = AIResponse(
        content=_result_content(),
        provider="test",
        model="test-model",
    )
    engine = LLMIntelligenceEngine(provider)
    analysis = _build_analysis()

    first_result = engine.analyze(analysis)
    second_result = engine.analyze(analysis)

    assert first_result == second_result
    first_request = provider.generate.call_args_list[0].args[0]
    second_request = provider.generate.call_args_list[1].args[0]
    assert first_request == second_request


def test_llm_engine_convenience_methods_return_expected_parts() -> None:
    provider = Mock(spec=AIEngine)
    provider.generate.return_value = AIResponse(
        content=_result_content(),
        provider="test",
        model="test-model",
    )
    engine = LLMIntelligenceEngine(provider)
    analysis = _build_analysis()

    classification = engine.classify_page(analysis)
    summary = engine.generate_summary(analysis)
    recommendations = engine.generate_recommendations(analysis)

    assert classification == _build_result().classification
    assert summary == _build_result().summary
    assert recommendations == _build_result().recommendations
    assert provider.generate.call_count == 3
