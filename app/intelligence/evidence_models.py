from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceType(StrEnum):
    """The kind of application signal supporting a conclusion."""

    CONTENT = "content"
    STRUCTURE = "structure"
    BEHAVIOR = "behavior"
    METADATA = "metadata"


class EvidenceSource(StrEnum):
    """The intelligence mechanism that produced an evidence item."""

    DETERMINISTIC = "deterministic"
    AI = "ai"


class EvidenceItem(BaseModel):
    """Provider-neutral evidence supporting an intelligence conclusion."""

    type: EvidenceType
    source: EvidenceSource
    description: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    severity: str | None = None
