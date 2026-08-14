from dataclasses import dataclass

from app.ai import (
    AIIntelligenceEngine,
    AIIntelligenceResult,
    DeterministicIntelligenceEngine,
)
from app.intelligence import (
    BrowserIntelligenceResult,
    PageAnalysisResult,
    analyze_browser_intelligence,
    analyze_page,
)


@dataclass(frozen=True)
class PageIntelligenceResult:
    """
    Internal pipeline result containing deterministic and AI intelligence.
    """

    page_analysis: PageAnalysisResult
    ai_intelligence: AIIntelligenceResult


class IntelligenceService:
    """
    Application service responsible for browser intelligence
    and higher-level page analysis.
    """

    def __init__(
        self,
        ai_engine: AIIntelligenceEngine | None = None,
    ) -> None:
        self._ai_engine = (
            ai_engine
            if ai_engine is not None
            else DeterministicIntelligenceEngine()
        )

    def analyze_browser(
        self,
        url: str,
    ) -> BrowserIntelligenceResult:
        """
        Execute browser intelligence only.
        """
        return analyze_page(url)

    def analyze_page(
        self,
        url: str,
    ) -> PageAnalysisResult:
        """
        Execute the complete browser intelligence workflow.

        Browser
            ↓
        Browser Intelligence
            ↓
        Analysis Engine
            ↓
        Structured Analysis Result
        """

        browser_result = self.analyze_browser(url)

        return analyze_browser_intelligence(browser_result)

    def analyze_page_with_ai(
        self,
        url: str,
    ) -> PageIntelligenceResult:
        """
        Run deterministic analysis followed by page-focused AI intelligence.
        """
        page_analysis = self.analyze_page(url)
        ai_intelligence = self._ai_engine.analyze(page_analysis)

        return PageIntelligenceResult(
            page_analysis=page_analysis,
            ai_intelligence=ai_intelligence,
        )
