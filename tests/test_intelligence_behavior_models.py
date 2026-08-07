import json

import pytest
from pydantic import ValidationError

from app.intelligence import (
    ApplicationBehavior,
    BehaviorSource,
    BehaviorType,
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
)


def _minimal_behavior() -> ApplicationBehavior:
    return ApplicationBehavior(
        behavior_type=BehaviorType.NAVIGATION,
        name="Navigate to another page",
        description="The application exposes a link to another page.",
        source=BehaviorSource.LINK,
    )


def test_behavior_type_has_the_supported_observable_values() -> None:
    assert [item.value for item in BehaviorType] == [
        "navigation",
        "form_submission",
        "authentication",
        "search",
        "data_entry",
        "user_action",
    ]


def test_behavior_source_has_the_supported_public_values() -> None:
    assert [item.value for item in BehaviorSource] == [
        "form",
        "input",
        "button",
        "link",
        "page_structure",
        "classification",
    ]


def test_minimal_application_behavior_uses_optional_defaults() -> None:
    behavior = _minimal_behavior()

    assert behavior.confidence is None
    assert behavior.evidence == []


def test_full_application_behavior_serializes_deterministically() -> None:
    behavior = ApplicationBehavior(
        behavior_type=BehaviorType.AUTHENTICATION,
        name="Submit login form",
        description="The application accepts authentication credentials.",
        source=BehaviorSource.FORM,
        evidence=[
            EvidenceItem(
                type=EvidenceType.STRUCTURE,
                source=EvidenceSource.DETERMINISTIC,
                description="Password input detected",
                confidence=0.9,
            )
        ],
        confidence=0.85,
    )
    expected = {
        "behavior_type": "authentication",
        "name": "Submit login form",
        "description": "The application accepts authentication credentials.",
        "source": "form",
        "evidence": [
            {
                "type": "structure",
                "source": "deterministic",
                "description": "Password input detected",
                "confidence": 0.9,
                "severity": None,
            }
        ],
        "confidence": 0.85,
    }

    assert behavior.model_dump(mode="json") == expected
    assert behavior.model_dump_json() == json.dumps(
        expected,
        separators=(",", ":"),
    )


@pytest.mark.parametrize("confidence", [0.0, 1.0])
def test_application_behavior_accepts_confidence_boundaries(
    confidence: float,
) -> None:
    behavior = ApplicationBehavior(
        behavior_type=BehaviorType.NAVIGATION,
        name="Navigate to another page",
        description="The application exposes a link to another page.",
        source=BehaviorSource.LINK,
        confidence=confidence,
    )

    assert behavior.confidence == confidence


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_application_behavior_rejects_confidence_outside_unit_interval(
    confidence: float,
) -> None:
    with pytest.raises(ValidationError):
        ApplicationBehavior(
            behavior_type=BehaviorType.SEARCH,
            name="Search application content",
            description="The application accepts a search query.",
            source=BehaviorSource.INPUT,
            confidence=confidence,
        )


@pytest.mark.parametrize("field", ["name", "description"])
def test_application_behavior_rejects_empty_required_text(field: str) -> None:
    values = {
        "behavior_type": BehaviorType.USER_ACTION,
        "name": "Activate control",
        "description": "The application exposes an interactive control.",
        "source": BehaviorSource.BUTTON,
    }
    values[field] = ""

    with pytest.raises(ValidationError):
        ApplicationBehavior(**values)


def test_application_behavior_evidence_lists_are_not_shared() -> None:
    first = _minimal_behavior()
    second = _minimal_behavior()
    first.evidence.append(
        EvidenceItem(
            type=EvidenceType.BEHAVIOR,
            source=EvidenceSource.DETERMINISTIC,
            description="Navigation link detected",
        )
    )

    assert len(first.evidence) == 1
    assert second.evidence == []


def test_equivalent_application_behaviors_compare_equal() -> None:
    assert _minimal_behavior() == _minimal_behavior()


def test_serialized_application_behavior_can_be_loaded_again() -> None:
    behavior = _minimal_behavior()
    payload = json.loads(behavior.model_dump_json())

    assert ApplicationBehavior.model_validate(payload) == behavior


def test_behavior_contract_contains_no_test_scenario_or_automation_fields() -> None:
    assert set(ApplicationBehavior.model_fields) == {
        "behavior_type",
        "name",
        "description",
        "source",
        "evidence",
        "confidence",
    }
