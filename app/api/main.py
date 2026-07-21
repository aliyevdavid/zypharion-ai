from fastapi import FastAPI, Query

from app.automation.smoke_runner import run_smoke_tests


app = FastAPI(
    title="Zypharion API",
    description="AI Software Intelligence Platform backend API.",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict:
    return {
        "message": "Welcome to Zypharion AI Software Intelligence Platform",
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "zypharion-api",
        "version": "0.1.0",
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