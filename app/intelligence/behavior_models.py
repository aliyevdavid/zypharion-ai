from enum import StrEnum

from pydantic import BaseModel, Field

from app.intelligence.evidence_models import EvidenceItem


class BehaviorType(StrEnum):
    """Broad category of testable behavior observable by browser intelligence."""

    NAVIGATION = "navigation"
    FORM_SUBMISSION = "form_submission"
    AUTHENTICATION = "authentication"
    SEARCH = "search"
    DATA_ENTRY = "data_entry"
    USER_ACTION = "user_action"


class BehaviorSource(StrEnum):
    """Public application signal from which a behavior was observed."""

    FORM = "form"
    INPUT = "input"
    BUTTON = "button"
    LINK = "link"
    PAGE_STRUCTURE = "page_structure"
    CLASSIFICATION = "classification"


class ApplicationBehavior(BaseModel):
    """An observable application capability, not a generated test case.

    Instances summarize deterministic, page-level browser observations. They
    do not claim to model the complete application and contain no test steps,
    expected results, assertions, selectors, or executable automation.
    """

    behavior_type: BehaviorType
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source: BehaviorSource
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
