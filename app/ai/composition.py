from typing import Any

from app.ai.engine import AIEngine
from app.ai.intelligence_engine import LLMIntelligenceEngine
from app.ai.page_intelligence_parser import (
    PageIntelligenceResponseParser,
)
from app.ai.prompts import PageIntelligencePromptBuilder
from app.ai.providers import create_ai_provider
from app.core.settings import Settings


def create_intelligence_engine(
    settings: Settings,
    *,
    ai_engine: AIEngine | None = None,
    azure_client: Any | None = None,
) -> LLMIntelligenceEngine:
    """Compose page intelligence dependencies without making an AI request."""
    provider = (
        ai_engine
        if ai_engine is not None
        else create_ai_provider(settings, azure_client=azure_client)
    )

    return LLMIntelligenceEngine(
        provider,
        prompt_builder=PageIntelligencePromptBuilder(),
        response_parser=PageIntelligenceResponseParser(),
    )
