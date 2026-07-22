from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


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


class PageClassification(BaseModel):
    """
    The predicted page type and the evidence supporting that prediction.
    """

    page_type: PageType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class PageAnalysisRequest(BaseModel):
    """
    API request used to analyze a public web page.
    """

    url: HttpUrl


class PageAnalysisResult(BaseModel):
    """
    Final structured output produced by the intelligence analysis layer.
    """

    requested_url: str
    final_url: str
    title: str
    classification: PageClassification
    detected_features: list[str] = Field(default_factory=list)
    findings: list[AnalysisFinding] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)