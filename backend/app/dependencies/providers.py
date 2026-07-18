"""Application-level resource providers.

Minimal stubs only.
"""

from app.db.session import async_session_maker


async def get_db():
    """Yield database session."""
    async with async_session_maker() as session:
        yield session

async def get_redis():
    """Yield Redis connection client."""
    pass
