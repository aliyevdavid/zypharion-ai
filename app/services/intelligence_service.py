from app.intelligence import (
    BrowserIntelligenceResult,
    PageAnalysisResult,
    analyze_browser_intelligence,
    analyze_page,
)


class IntelligenceService:
    """
    Application service responsible for browser intelligence
    and higher-level page analysis.
    """

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