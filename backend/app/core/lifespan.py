import os
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI

from app.core.config import settings
from app.db.session import engine

logger = structlog.get_logger()

# Global redis pool holder
redis_client: aioredis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    logger.info("Initializing resources inside application lifespan...")

    # Ensure UPLOAD_DIR exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Initialize and validate LLM Workload Profiles registry
    from app.llm.registry import LLMRegistry

    try:
        LLMRegistry()
        logger.info("LLM Workload Profiles registry validated successfully")
    except Exception as e:
        logger.error("LLM Workload Profiles validation failed on startup", error=str(e))
        raise e

    # Initialize Redis connection pool
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    yield

    # Cleanup resources
    logger.info("Shutting down resources inside application lifespan...")
    if redis_client:
        await redis_client.close()

    await engine.dispose()
