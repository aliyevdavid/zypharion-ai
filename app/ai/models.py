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