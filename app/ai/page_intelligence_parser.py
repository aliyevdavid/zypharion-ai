import json

from app.ai.models import AIIntelligenceResult


class PageIntelligenceResponseParser:
    """
    Decode and validate provider output for page intelligence.
    """

    def parse(self, content: str) -> AIIntelligenceResult:
        response_data = json.loads(content)

        return AIIntelligenceResult.model_validate(response_data)
