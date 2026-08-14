from unittest.mock import Mock

import pytest

from app.ai import LLMIntelligenceEngine, MockAIEngine
from app.analysis import PageAnalysisRequest, PageAnalysisService
from app.intelligence import (
    BehaviorSource,
    BehaviorType,
    BrowserIntelligenceResult,
    ButtonInfo,
    EvidenceSource,
    EvidenceType,
    FormInfo,
    InputInfo,
    LinkInfo,
    PageMetrics,
    analyze_browser_intelligence,
    discover_application_behaviors,
)


def _result(**overrides: object) -> BrowserIntelligenceResult:
    values: dict[str, object] = {
        "requested_url": "https://example.com/",
        "final_url": "https://example.com/",
        "title": "",
        "success": True,
        "metrics": PageMetrics(load_time_ms=10),
    }
    values.update(overrides)
    return BrowserIntelligenceResult(**values)


def test_empty_and_noisy_structures_do_not_produce_behaviors() -> None:
    result = _result(
        links=[LinkInfo(text=" ", href="#", is_external=False)],
        buttons=[ButtonInfo(text="...", button_type="button")],
    )

    assert discover_application_behaviors(result) == []


def test_meaningful_links_produce_one_navigation_behavior() -> None:
    result = _result(
        links=[
            LinkInfo(text="Account", href="/account", is_external=False),
            LinkInfo(text="Help", href="https://help.example.com", is_external=True),
        ]
    )

    behaviors = discover_application_behaviors(result)

    assert [(item.behavior_type, item.source) for item in behaviors] == [
        (BehaviorType.NAVIGATION, BehaviorSource.LINK)
    ]
    assert [item.description for item in behaviors[0].evidence] == [
        "Link observed: text=Account, href=/account",
        "Link observed: text=Help, href=https://help.example.com",
    ]


def test_password_and_login_form_produce_authentication_behaviors() -> None:
    result = _result(
        forms=[FormInfo(action="/login", method="post")],
        inputs=[InputInfo(name="password", input_type="password")],
        buttons=[ButtonInfo(text="Sign in", button_type="submit")],
    )

    behaviors = discover_application_behaviors(result)

    sources = [
        item.source
        for item in behaviors
        if item.behavior_type is BehaviorType.AUTHENTICATION
    ]
    assert sources == [
        BehaviorSource.INPUT,
        BehaviorSource.BUTTON,
        BehaviorSource.FORM,
    ]


def test_search_signals_produce_input_button_and_form_behaviors() -> None:
    result = _result(
        forms=[FormInfo(action="/search")],
        inputs=[InputInfo(name="q", input_type="search", placeholder="Find products")],
        buttons=[ButtonInfo(text="Search", button_type="submit")],
    )

    behaviors = discover_application_behaviors(result)

    sources = [
        item.source
        for item in behaviors
        if item.behavior_type is BehaviorType.SEARCH
    ]
    assert sources == [
        BehaviorSource.INPUT,
        BehaviorSource.BUTTON,
        BehaviorSource.FORM,
    ]


def test_general_inputs_forms_and_action_buttons_map_to_distinct_behaviors() -> None:
    result = _result(
        forms=[FormInfo(action="/profile", method="post")],
        inputs=[
            InputInfo(name="email", input_type="email"),
            InputInfo(name="birthday", input_type="date"),
        ],
        buttons=[
            ButtonInfo(text="Save", button_type="submit"),
            ButtonInfo(text="Export", button_type="button"),
        ],
    )

    behaviors = discover_application_behaviors(result)
    pairs = [(item.behavior_type, item.source) for item in behaviors]

    assert (BehaviorType.DATA_ENTRY, BehaviorSource.INPUT) in pairs
    assert (BehaviorType.FORM_SUBMISSION, BehaviorSource.BUTTON) in pairs
    assert (BehaviorType.FORM_SUBMISSION, BehaviorSource.FORM) in pairs
    assert (BehaviorType.USER_ACTION, BehaviorSource.BUTTON) in pairs


def test_evidence_is_structured_deterministic_and_duplicate_signals_are_folded() -> None:
    duplicated_input = InputInfo(name="email", input_type="email")
    result = _result(inputs=[duplicated_input, duplicated_input.model_copy()])

    first = discover_application_behaviors(result)
    second = discover_application_behaviors(result)

    assert first == second
    assert len(first) == 1
    assert len(first[0].evidence) == 1
    evidence = first[0].evidence[0]
    assert evidence.type is EvidenceType.STRUCTURE
    assert evidence.source is EvidenceSource.DETERMINISTIC
    assert evidence.confidence is None


def test_behavior_order_is_stable_and_classification_does_not_duplicate_signals() -> None:
    result = _result(
        title="Search",
        links=[LinkInfo(text="Home", href="/", is_external=False)],
        forms=[FormInfo(action="/search")],
        inputs=[InputInfo(name="query", input_type="search")],
        buttons=[ButtonInfo(text="Search", button_type="submit")],
    )

    first = analyze_browser_intelligence(result)
    second = analyze_browser_intelligence(result)

    assert first.behaviors == second.behaviors
    assert [(item.behavior_type, item.source) for item in first.behaviors] == [
        (BehaviorType.NAVIGATION, BehaviorSource.LINK),
        (BehaviorType.SEARCH, BehaviorSource.INPUT),
        (BehaviorType.SEARCH, BehaviorSource.BUTTON),
        (BehaviorType.FORM_SUBMISSION, BehaviorSource.BUTTON),
        (BehaviorType.FORM_SUBMISSION, BehaviorSource.FORM),
        (BehaviorType.SEARCH, BehaviorSource.FORM),
    ]
    assert all(item.source is not BehaviorSource.CLASSIFICATION for item in first.behaviors)


def test_classification_adds_only_unobserved_high_level_behavior() -> None:
    analysis = analyze_browser_intelligence(_result(title="Sign in to your account"))

    assert [(item.behavior_type, item.source) for item in analysis.behaviors] == [
        (BehaviorType.AUTHENTICATION, BehaviorSource.CLASSIFICATION)
    ]
    assert analysis.behaviors[0].evidence[0].source is EvidenceSource.DETERMINISTIC


@pytest.mark.parametrize("use_ai", [False, True])
def test_analysis_workflows_preserve_deterministic_behaviors(use_ai: bool) -> None:
    browser_result = _result(
        links=[LinkInfo(text="Account", href="/account", is_external=False)]
    )
    service = PageAnalysisService(
        Mock(return_value=browser_result),
        analyze_browser_intelligence,
        LLMIntelligenceEngine(MockAIEngine()),
    )

    result = service.analyze(
        PageAnalysisRequest(url="https://example.com", use_ai=use_ai)
    )

    assert result.intelligence is not None
    assert (
        result.intelligence.behaviors[0].behavior_type
        is BehaviorType.NAVIGATION
    )
    assert result.model_dump(mode="json")["intelligence"]["behaviors"][0] == {
        "behavior_type": "navigation",
        "name": "Link navigation",
        "description": "The page exposes meaningful links for navigation.",
        "source": "link",
        "evidence": [
            {
                "type": "behavior",
                "source": "deterministic",
                "description": "Link observed: text=Account, href=/account",
                "confidence": None,
                "severity": None,
            }
        ],
        "confidence": None,
    }
