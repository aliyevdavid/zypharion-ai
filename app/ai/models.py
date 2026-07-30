from enum import StrEnum

from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    """
    Provider-independent request sent to an AI engine.
    """

    instruction: str = Field(min_length=1)
    context: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class AIResponse(BaseModel):
    """
    Provider-independent result returned by an AI engine.
    """

    content: str
    provider: str
    model: str
    metadata: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict
    )


class AIPageClassification(BaseModel):
    """
    Future AI-oriented page classification output.
    """

    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class RecommendationPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AIRecommendation(BaseModel):
    """
    A structured recommendation produced by AI intelligence.
    """

    title: str
    description: str
    priority: RecommendationPriority


class AIIntelligenceResult(BaseModel):
    """
    Typed output from a page-focused AI intelligence engine.
    """

    classification: AIPageClassification
    summary: str
    recommendations: list[AIRecommendation] = Field(default_factory=list)
