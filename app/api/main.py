from fastapi import FastAPI

app = FastAPI(
    title="Zypharion API",
    description="AI Software Intelligence Platform backend API.",
    version="0.1.0",
)

@app.get("/")
async def root():
    return {"message": "Welcome to Zypharion AI Software Intelligence Platform",
            "status": "running",
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy",
            "service": "zypharion-api",
            "version": "0.1.0",
    }