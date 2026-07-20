import traceback

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.core.middleware.logging_middleware import LoggingMiddleware

logger = structlog.get_logger()

# Set up structured logging prior to app boot
setup_logging()

app = FastAPI(
    title="NextRound API",
    description="Production-grade AI-powered mock interview simulator API backend.",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Logging middleware runs first to correlate request contextvars
app.add_middleware(LoggingMiddleware)

# Standard CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check():
    """Simple check for system availability."""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception handler.
    Logs exceptions with full context and returns clean error payloads to client.
    """
    context = structlog.contextvars.get_contextvars()
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    logger.critical(
        f"Unhandled exception occurred: {exc}",
        category="API",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        stack_trace=tb,
        **context
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact support."}
    )
