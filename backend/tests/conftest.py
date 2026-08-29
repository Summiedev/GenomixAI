import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from alembic import command
from app.core.config import Settings
from app.db.session import create_engine


def database_url() -> str:
    return os.environ.get(
        "TEST_DATABASE_URL",
        os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://localhost:5432/genomixai",
        ),
    )


def make_alembic_config() -> Config:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url().replace("%", "%%"))
    return config


@pytest.fixture(scope="session")
def migrated_database() -> Iterator[None]:
    """Use an isolated PostgreSQL test database and keep it migration-managed."""

    command.upgrade(make_alembic_config(), "head")
    yield
    command.downgrade(make_alembic_config(), "base")


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url=database_url(), jwt_secret="test-only-secret")


@pytest.fixture
def alembic_config() -> Config:
    return make_alembic_config()


@pytest.fixture
async def db_engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    engine = create_engine(settings)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(
    db_engine: AsyncEngine, migrated_database: None
) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
