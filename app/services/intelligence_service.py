from app.intelligence.extractor import analyze_page
from app.intelligence.models import BrowserIntelligenceResult


class IntelligenceService:
    """
    Application service responsible for orchestrating browser intelligence.

    The API layer calls this service instead of invoking Playwright directly.
    This keeps HTTP concerns separate from browser extraction logic.
    """

    def analyze(self, url: str) -> BrowserIntelligenceResult:
        return analyze_page(url)