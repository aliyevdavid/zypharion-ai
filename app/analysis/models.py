from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl

from app.ai import AIIntelligenceResult
from app.intelligence import (
    BrowserIntelligenceResult,
    PageAnalysisResult as DeterministicPageAnalysisResult,
)


class AnalysisStatus(StrEnum):
    """Overall outcome of the page-analysis workflow."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class AnalysisStage(StrEnum):
    """Workflow stage at which an analysis error occurred."""

    VALIDATION = "validation"
    BROWSER = "browser"
    EXTRACTION = "extraction"
    INTELLIGENCE = "intelligence"


class AnalysisError(BaseModel):
    """Safe, structured error information suitable for API responses."""

    stage: AnalysisStage
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


class PageAnalysisRequest(BaseModel):
    """Application-level request for a complete webpage analysis."""

    url: HttpUrl
    use_ai: bool = False


class PageAnalysisResult(BaseModel):
    """Application-level result supporting success, partial data, and failure."""

    url: str
    status: AnalysisStatus
    browser_result: BrowserIntelligenceResult | None = None
    intelligence: DeterministicPageAnalysisResult | None = None
    ai_intelligence: AIIntelligenceResult | None = None
    errors: list[AnalysisError] = Field(default_factory=list)
    duration_ms: int | None = Field(default=None, ge=0)
