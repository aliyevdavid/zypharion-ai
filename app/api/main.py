from functools import lru_cache

from fastapi import APIRouter, Depends, FastAPI, Query, Request

from app.analysis import (
    PageAnalysisRequest as ApplicationPageAnalysisRequest,
    PageAnalysisResult as ApplicationPageAnalysisResult,
    PageAnalysisService,
    create_page_analysis_service,
)
from app.automation.smoke_runner import run_smoke_tests
from app.core.settings import Settings, get_settings
from app.intelligence.analysis_models import (
    PageAnalysisRequest,
    PageAnalysisResult,
)
from app.intelligence.models import (
    BrowserIntelligenceRequest,
    BrowserIntelligenceResult,
)
from app.services import IntelligenceService


intelligence_service = IntelligenceService()
router = APIRouter()


@lru_cache
def get_page_analysis_service() -> PageAnalysisService:
    """Compose the complete page-analysis workflow for API requests."""
    return create_page_analysis_service()


@router.get("/")
async def root(request: Request) -> dict[str, str]:
    settings: Settings = request.app.state.settings
    return {
        "message": "Zypharion Quality Engineering Intelligence Platform",
        "status": "running",
        "environment": settings.environment,
    }


@router.get("/health")
async def health_check(request: Request) -> dict[str, str]:
    settings: Settings = request.app.state.settings
    return {
        "status": "healthy",
        "service": "zypharion-api",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/automation/smoke")
def automation_smoke_tests(
    url: str = Query(
        ...,
        description="Public URL that the backend API should validate",
        examples=["https://example.com"],
    ),
) -> dict:
    return run_smoke_tests(url)


@router.post(
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


@router.post(
    "/ai/analyze",
    response_model=PageAnalysisResult,
    summary="Generate explainable page analysis",
    description=(
        "Open a public URL, collect structured browser intelligence, and "
        "apply the deterministic reasoning engine to classify the "
        "page and generate explainable findings and recommendations."
    ),
)
def analyze_page_intelligence(
    request: PageAnalysisRequest,
) -> PageAnalysisResult:
    return intelligence_service.analyze_page(str(request.url))


@router.post(
    "/api/v1/analyze",
    response_model=ApplicationPageAnalysisResult,
    summary="Run complete page analysis",
    description=(
        "Run browser extraction and deterministic analysis, with optional "
        "AI intelligence, and return a structured workflow result."
    ),
)
def analyze_application_page(
    request: ApplicationPageAnalysisRequest,
    service: PageAnalysisService = Depends(get_page_analysis_service),
) -> ApplicationPageAnalysisResult:
    return service.analyze(request)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a configured API application without external runtime work."""
    resolved_settings = settings if settings is not None else get_settings()
    application = FastAPI(
        title=resolved_settings.app_name,
        description=(
            "Backend API for Zypharion, an AI-powered Quality Engineering "
            "intelligence platform."
        ),
        version=resolved_settings.app_version,
    )
    application.state.settings = resolved_settings
    application.include_router(router)
    return application


app = create_app()
