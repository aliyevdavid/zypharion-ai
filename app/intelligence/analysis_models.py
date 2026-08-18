from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl

from app.intelligence.behavior_models import ApplicationBehavior
from app.intelligence.evidence_models import EvidenceItem


class PageType(StrEnum):
    """
    High-level classification assigned to an analyzed web page.
    """

    AUTHENTICATION = "authentication"
    SEARCH = "search"
    DOCUMENTATION = "documentation"
    MARKETING = "marketing"
    DASHBOARD = "dashboard"
    FORM = "form"
    UNKNOWN = "unknown"


class AnalysisFinding(BaseModel):
    """
    A structured insight discovered during page analysis.
    """

    category: str
    message: str
    severity: str = "info"


class IntelligenceExplanation(BaseModel):
    """Deterministic explanation of an intelligence conclusion."""

    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    uncertainty: str | None = None


class PageClassification(BaseModel):
    """
    The predicted page type and the evidence supporting that prediction.
    """

    page_type: PageType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    structured_evidence: list[EvidenceItem] = Field(default_factory=list)
    explanation: IntelligenceExplanation | None = None


class PageAnalysisRequest(BaseModel):
    """
    API request used to analyze a public web page.
    """

    url: HttpUrl


class PageAnalysisResult(BaseModel):
    """
    Final structured output produced by the intelligence analysis layer.

    Each result receives a unique identifier for correlation. The identifier
    also supports future persistence, comparison, reporting, and historical
    analysis; those capabilities are not provided by this model.
    """

    analysis_id: UUID = Field(default_factory=uuid4)
    requested_url: str
    final_url: str
    title: str
    classification: PageClassification
    behaviors: list[ApplicationBehavior] = Field(default_factory=list)
    detected_features: list[str] = Field(default_factory=list)
    findings: list[AnalysisFinding] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
