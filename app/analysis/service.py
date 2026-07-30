from collections.abc import Callable
from time import perf_counter
from typing import Protocol

from app.ai import AIIntelligenceEngine, AIIntelligenceResult
from app.analysis.models import (
    AnalysisError,
    AnalysisStage,
    AnalysisStatus,
    PageAnalysisRequest,
    PageAnalysisResult,
)
from app.intelligence import (
    BrowserIntelligenceResult,
    PageAnalysisResult as DeterministicPageAnalysisResult,
)


class BrowserAnalyzer(Protocol):
    """Callable contract implemented by the existing browser extractor."""

    def __call__(self, url: str) -> BrowserIntelligenceResult: ...


class DeterministicAnalyzer(Protocol):
    """Callable contract implemented by the deterministic analyzer."""

    def __call__(
        self,
        result: BrowserIntelligenceResult,
    ) -> DeterministicPageAnalysisResult: ...


class PageAnalysisService:
    """Coordinate browser, deterministic, and optional AI intelligence."""

    def __init__(
        self,
        browser_analyzer: BrowserAnalyzer,
        deterministic_analyzer: DeterministicAnalyzer,
        ai_engine: AIIntelligenceEngine | None = None,
        *,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        self._browser_analyzer = browser_analyzer
        self._deterministic_analyzer = deterministic_analyzer
        self._ai_engine = ai_engine
        self._clock = clock

    def analyze(
        self,
        request: PageAnalysisRequest,
    ) -> PageAnalysisResult:
        """Run all requested analysis stages and return a controlled result."""
        started_at = self._clock()
        url = str(request.url)

        try:
            browser_result = self._browser_analyzer(url)
        except Exception:
            return self._result(
                started_at=started_at,
                url=url,
                status=AnalysisStatus.FAILED,
                errors=[
                    AnalysisError(
                        stage=AnalysisStage.BROWSER,
                        code="browser_analysis_failed",
                        message="Browser analysis could not be completed.",
                    )
                ],
            )

        if not browser_result.success:
            return self._result(
                started_at=started_at,
                url=url,
                status=AnalysisStatus.FAILED,
                browser_result=browser_result,
                errors=[
                    AnalysisError(
                        stage=AnalysisStage.BROWSER,
                        code="browser_analysis_failed",
                        message="Browser analysis was unsuccessful.",
                    )
                ],
            )

        try:
            intelligence = self._deterministic_analyzer(browser_result)
        except Exception:
            return self._result(
                started_at=started_at,
                url=url,
                status=AnalysisStatus.PARTIAL_SUCCESS,
                browser_result=browser_result,
                errors=[
                    AnalysisError(
                        stage=AnalysisStage.INTELLIGENCE,
                        code="deterministic_intelligence_failed",
                        message=(
                            "Deterministic intelligence could not be completed."
                        ),
                    )
                ],
            )

        if not request.use_ai:
            return self._result(
                started_at=started_at,
                url=url,
                status=AnalysisStatus.SUCCESS,
                browser_result=browser_result,
                intelligence=intelligence,
            )

        if self._ai_engine is None:
            return self._result(
                started_at=started_at,
                url=url,
                status=AnalysisStatus.PARTIAL_SUCCESS,
                browser_result=browser_result,
                intelligence=intelligence,
                errors=[
                    AnalysisError(
                        stage=AnalysisStage.INTELLIGENCE,
                        code="ai_intelligence_unavailable",
                        message="AI intelligence is not available.",
                    )
                ],
            )

        try:
            ai_intelligence = self._ai_engine.analyze(intelligence)
        except Exception:
            return self._result(
                started_at=started_at,
                url=url,
                status=AnalysisStatus.PARTIAL_SUCCESS,
                browser_result=browser_result,
                intelligence=intelligence,
                errors=[
                    AnalysisError(
                        stage=AnalysisStage.INTELLIGENCE,
                        code="ai_intelligence_failed",
                        message="AI intelligence could not be completed.",
                    )
                ],
            )

        return self._result(
            started_at=started_at,
            url=url,
            status=AnalysisStatus.SUCCESS,
            browser_result=browser_result,
            intelligence=intelligence,
            ai_intelligence=ai_intelligence,
        )

    def _result(
        self,
        *,
        started_at: float,
        url: str,
        status: AnalysisStatus,
        browser_result: BrowserIntelligenceResult | None = None,
        intelligence: DeterministicPageAnalysisResult | None = None,
        ai_intelligence: AIIntelligenceResult | None = None,
        errors: list[AnalysisError] | None = None,
    ) -> PageAnalysisResult:
        duration_ms = max(0, round((self._clock() - started_at) * 1000))
        return PageAnalysisResult(
            url=url,
            status=status,
            browser_result=browser_result,
            intelligence=intelligence,
            ai_intelligence=ai_intelligence,
            errors=errors or [],
            duration_ms=duration_ms,
        )
