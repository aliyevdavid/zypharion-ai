import json

from pydantic import ValidationError

from app.ai.models import AIIntelligenceResult


class AIResponseValidationError(ValueError):
    """Provider content could not be decoded into page intelligence."""


class PageIntelligenceResponseParser:
    """
    Decode and validate provider output for page intelligence.
    """

    def parse(self, content: str) -> AIIntelligenceResult:
        try:
            response_data = json.loads(content)
            return AIIntelligenceResult.model_validate(response_data)
        except (json.JSONDecodeError, ValidationError) as error:
            raise AIResponseValidationError(
                "AI response is not valid page intelligence."
            ) from error
