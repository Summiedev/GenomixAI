import httpx
import pytest

from app.main import create_app


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(settings) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(settings)),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "genomixai-backend"}


@pytest.mark.asyncio
async def test_invalid_route_returns_404(settings) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(settings)),
        base_url="http://test",
    ) as client:
        response = await client.get("/does-not-exist")

    assert response.status_code == 404


def test_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("PROJECT_NAME", "Test Backend")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://tester:secret@localhost/test_db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "45")

    from app.core.config import Settings

    loaded = Settings()
    assert loaded.app_env == "test"
    assert loaded.project_name == "Test Backend"
    assert loaded.database_url.endswith("/test_db")
    assert loaded.access_token_expire_minutes == 45


def test_application_does_not_create_schema(monkeypatch, settings) -> None:
    from app.db.base import Base

    def fail_create_all(*args, **kwargs):
        raise AssertionError("startup must not call create_all")

    monkeypatch.setattr(Base.metadata, "create_all", fail_create_all)
    create_app(settings)
