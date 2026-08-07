import pytest
from pydantic import ValidationError

from app.intelligence import EvidenceItem, EvidenceSource, EvidenceType


def test_evidence_item_serializes_enums_and_optional_fields() -> None:
    evidence = EvidenceItem(
        type=EvidenceType.CONTENT,
        source=EvidenceSource.DETERMINISTIC,
        description="Authentication-related text detected",
        confidence=0.85,
        severity="info",
    )

    assert evidence.model_dump(mode="json") == {
        "type": "content",
        "source": "deterministic",
        "description": "Authentication-related text detected",
        "confidence": 0.85,
        "severity": "info",
    }


def test_evidence_item_uses_none_for_optional_field_defaults() -> None:
    evidence = EvidenceItem(
        type="structure",
        source="ai",
        description="The page contains a sign-in form",
    )

    assert evidence.confidence is None
    assert evidence.severity is None


@pytest.mark.parametrize("evidence_type", list(EvidenceType))
def test_evidence_type_values_are_accepted(evidence_type: EvidenceType) -> None:
    evidence = EvidenceItem(
        type=evidence_type,
        source=EvidenceSource.DETERMINISTIC,
        description="Observed application signal",
    )

    assert evidence.type is evidence_type


@pytest.mark.parametrize("source", list(EvidenceSource))
def test_evidence_source_values_are_accepted(source: EvidenceSource) -> None:
    evidence = EvidenceItem(
        type=EvidenceType.BEHAVIOR,
        source=source,
        description="Observed application behavior",
    )

    assert evidence.source is source


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_evidence_item_rejects_confidence_outside_unit_interval(
    confidence: float,
) -> None:
    with pytest.raises(ValidationError):
        EvidenceItem(
            type=EvidenceType.METADATA,
            source=EvidenceSource.AI,
            description="Metadata supports the conclusion",
            confidence=confidence,
        )


def test_evidence_item_rejects_empty_description() -> None:
    with pytest.raises(ValidationError):
        EvidenceItem(
            type=EvidenceType.CONTENT,
            source=EvidenceSource.DETERMINISTIC,
            description="",
        )


def test_evidence_items_with_the_same_values_are_equal() -> None:
    values = {
        "type": EvidenceType.STRUCTURE,
        "source": EvidenceSource.AI,
        "description": "Navigation structure supports the conclusion",
    }

    assert EvidenceItem(**values) == EvidenceItem(**values)


def test_minimal_serialized_evidence_can_be_loaded_again() -> None:
    payload = {
        "type": "content",
        "source": "deterministic",
        "description": "A password input was observed",
    }

    evidence = EvidenceItem.model_validate(payload)

    assert evidence.model_dump(exclude_none=True, mode="json") == payload
