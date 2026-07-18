import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


@pytest_asyncio.fixture
async def db():
    """Yield an async database session wrapped in a rolling transaction."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.connect() as conn:
        transaction = await conn.begin()
        async with async_session(bind=conn) as session:
            yield session
            await session.rollback()
        await transaction.rollback()

    await engine.dispose()
