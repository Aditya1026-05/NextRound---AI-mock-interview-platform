from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.logging import setup_logging

# Set up structured logging prior to app boot
setup_logging()

app = FastAPI(
    title="InterviewOS API",
    description="Production-grade AI-powered mock interview simulator API backend.",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Standard CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
async def health_check():
    """Simple check for system availability."""
    return {"status": "ok"}
