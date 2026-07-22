from fastapi import FastAPI, Query

from app.automation.smoke_runner import run_smoke_tests
from app.core.settings import get_settings
from app.intelligence.analysis_models import (
    PageAnalysisRequest,
    PageAnalysisResult,
)
from app.intelligence.models import (
    BrowserIntelligenceRequest,
    BrowserIntelligenceResult,
)
from app.services import IntelligenceService


settings = get_settings()
intelligence_service = IntelligenceService()

app = FastAPI(
    title=settings.app_name,
    description="AI Software Intelligence Platform backend API.",
    version=settings.app_version,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to Zypharion AI Software Intelligence Platform",
        "status": "running",
        "environment": settings.environment,
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "zypharion-api",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/automation/smoke")
def automation_smoke_tests(
    url: str = Query(
        ...,
        description="Public URL that Zypharion should validate",
        examples=["https://example.com"],
    ),
) -> dict:
    return run_smoke_tests(url)


@app.post(
    "/intelligence/analyze",
    response_model=BrowserIntelligenceResult,
    summary="Extract browser intelligence",
    description=(
        "Open a public URL with Playwright and return structured browser "
        "observations including metadata, headings, links, images, forms, "
        "buttons, inputs, console errors, and basic timing metrics."
    ),
)
def analyze_browser_page(
    request: BrowserIntelligenceRequest,
) -> BrowserIntelligenceResult:
    return intelligence_service.analyze_browser(str(request.url))


@app.post(
    "/ai/analyze",
    response_model=PageAnalysisResult,
    summary="Generate explainable page analysis",
    description=(
        "Open a public URL, collect structured browser intelligence, and "
        "apply Zypharion's deterministic reasoning engine to classify the "
        "page and generate explainable findings and recommendations."
    ),
)
def analyze_page_intelligence(
    request: PageAnalysisRequest,
) -> PageAnalysisResult:
    return intelligence_service.analyze_page(str(request.url))