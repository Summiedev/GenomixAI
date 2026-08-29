import time
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import create_app
from app.models import User, UserStatus


async def client_for(db_session, settings: Settings):
    application = create_app(settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application), base_url="http://test"
    )
    return application, client


@pytest.mark.asyncio
async def test_valid_login_and_current_user_resolves_physician(db_session, settings) -> None:
    _, client = await client_for(db_session, settings)
    async with client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "physician.a@genomixai.demo", "password": "ChangeMe123!"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        current = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert current.status_code == 200
    assert current.json()["membership"]["role"] == "PHYSICIAN"
    assert current.json()["membership"]["department"]["name"] == "Cardiology"
    assert current.json()["membership"]["organization"]["name"] == "Hospital A"


@pytest.mark.asyncio
async def test_pharmacist_login_resolves_pharmacist(db_session, settings) -> None:
    _, client = await client_for(db_session, settings)
    async with client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "pharmacist.a@genomixai.demo", "password": "ChangeMe123!"},
        )
        current = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )

    assert login.status_code == 200
    assert current.json()["membership"]["role"] == "CLINICAL_PHARMACIST"
    assert current.json()["membership"]["department"]["name"] == "Pharmacy"


@pytest.mark.asyncio
async def test_invalid_and_nonexistent_login_are_denied(db_session, settings) -> None:
    _, client = await client_for(db_session, settings)
    async with client:
        invalid_password = await client.post(
            "/api/v1/auth/login",
            json={"email": "physician.a@genomixai.demo", "password": "wrong"},
        )
        nonexistent = await client.post(
            "/api/v1/auth/login",
            json={"email": "missing@genomixai.demo", "password": "wrong"},
        )

    assert invalid_password.status_code == 401
    assert nonexistent.status_code == 401
    assert invalid_password.json() == nonexistent.json()


@pytest.mark.asyncio
async def test_inactive_user_and_revoked_token_are_denied(db_session, settings) -> None:
    user = await db_session.scalar(select(User).where(User.email == "physician.b@genomixai.demo"))
    user.status = UserStatus.INACTIVE
    await db_session.commit()

    _, client = await client_for(db_session, settings)
    async with client:
        inactive = await client.post(
            "/api/v1/auth/login",
            json={"email": "physician.b@genomixai.demo", "password": "ChangeMe123!"},
        )
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "physician.a@genomixai.demo", "password": "ChangeMe123!"},
        )
        token = login.json()["access_token"]
        logout = await client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )
        after_logout = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

    assert inactive.status_code == 401
    assert logout.status_code == 204
    assert after_logout.status_code == 401

    user.status = UserStatus.ACTIVE
    await db_session.commit()


@pytest.mark.asyncio
async def test_malformed_expired_and_bad_signature_tokens_are_denied(db_session, settings) -> None:
    _, client = await client_for(db_session, settings)
    async with client:
        malformed = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer malformed"}
        )
        token, _, _ = create_access_token(UUID("00000000-0000-0000-0000-0000000a0101"), settings)
        bad_signature = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token[:-1]}x"}
        )
        # A validly signed token with an expired exp claim is rejected before the
        # database lookup. The helper's time source is patched only for creation.
        original_time = time.time
        time.time = lambda: original_time() - 3600
        expired, _, _ = create_access_token(UUID("00000000-0000-0000-0000-0000000a0101"), settings)
        time.time = original_time
        expired_response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}
        )

    assert malformed.status_code == 401
    assert bad_signature.status_code == 401
    assert expired_response.status_code == 401
