from app.ai import AIIntelligenceEngine, create_intelligence_engine
from app.analysis.service import (
    BrowserAnalyzer,
    DeterministicAnalyzer,
    PageAnalysisService,
)
from app.core.settings import Settings, get_settings
from app.intelligence import analyze_browser_intelligence, analyze_page


def create_page_analysis_service(
    settings: Settings | None = None,
    *,
    browser_analyzer: BrowserAnalyzer = analyze_page,
    deterministic_analyzer: DeterministicAnalyzer = (
        analyze_browser_intelligence
    ),
    ai_engine: AIIntelligenceEngine | None = None,
) -> PageAnalysisService:
    """Compose the page-analysis workflow without running any analysis."""
    resolved_settings = settings if settings is not None else get_settings()
    resolved_ai_engine = (
        ai_engine
        if ai_engine is not None
        else create_intelligence_engine(resolved_settings)
    )

    return PageAnalysisService(
        browser_analyzer=browser_analyzer,
        deterministic_analyzer=deterministic_analyzer,
        ai_engine=resolved_ai_engine,
    )
