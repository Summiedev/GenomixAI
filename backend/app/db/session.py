from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    runtime_settings = settings or get_settings()
    return create_async_engine(runtime_settings.database_url, pool_pre_ping=True)


engine = create_engine()
AsyncSessionFactory = async_sessionmaker[AsyncSession]
async_session_factory = AsyncSessionFactory(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield one request-scoped session and always close it."""

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def verify_database_connection(session: AsyncSession) -> bool:
    await session.execute(text("SELECT 1"))
    return True
