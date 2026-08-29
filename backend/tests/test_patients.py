import httpx
import pytest
from sqlalchemy import select

from app.db.session import get_db
from app.main import create_app
from app.models import Organization, Patient, PatientStatus


async def patient_client(db_session, settings):
    application = create_app(settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://test")


async def login(client, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_patient_search_by_name_mrn_and_genomix_id(db_session, settings) -> None:
    async with await patient_client(db_session, settings) as client:
        token = await login(client, "physician.a@genomixai.demo")
        headers = {"Authorization": f"Bearer {token}"}
        for term in ("Amara", "HA-0001", "GX-000001"):
            response = await client.get(
                "/api/v1/patients",
                params={"organization_id": "00000000-0000-0000-0000-0000000000a1", "search": term},
                headers=headers,
            )
            assert response.status_code == 200
            assert response.json()["total"] == 1
            assert response.json()["items"][0]["genomix_patient_id"] == "GX-000001"


@pytest.mark.asyncio
async def test_patient_details_pagination_and_malformed_identifier(db_session, settings) -> None:
    organization = await db_session.scalar(
        select(Organization).where(Organization.slug == "hospital-a")
    )
    patients = (
        await db_session.scalars(select(Patient).where(Patient.genomix_patient_id == "GX-000001"))
    ).all()
    assert organization is not None and len(patients) == 1
    async with await patient_client(db_session, settings) as client:
        token = await login(client, "physician.a@genomixai.demo")
        headers = {"Authorization": f"Bearer {token}"}
        page = await client.get(
            "/api/v1/patients",
            params={
                "organization_id": str(organization.id),
                "page": 1,
                "page_size": 1,
            },
            headers=headers,
        )
        detail = await client.get(
            f"/api/v1/patients/{patients[0].id}",
            params={"organization_id": str(organization.id)},
            headers=headers,
        )
        malformed = await client.get(
            "/api/v1/patients/not-a-uuid",
            params={"organization_id": str(organization.id)},
            headers=headers,
        )

    assert page.status_code == 200
    assert page.json()["page_size"] == 1
    assert detail.status_code == 200
    assert detail.json()["mrn"] == "HA-0001"
    assert malformed.status_code == 422


@pytest.mark.asyncio
async def test_hospital_isolation_and_inactive_patient_behavior(db_session, settings) -> None:
    hospital_b = await db_session.scalar(
        select(Organization).where(Organization.slug == "hospital-b")
    )
    patient_b = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000002")
    )
    assert hospital_b is not None and patient_b is not None

    async with await patient_client(db_session, settings) as client:
        token = await login(client, "physician.a@genomixai.demo")
        headers = {"Authorization": f"Bearer {token}"}
        cross_hospital = await client.get(
            f"/api/v1/patients/{patient_b.id}",
            params={"organization_id": str(hospital_b.id)},
            headers=headers,
        )
        known_uuid = await client.get(
            f"/api/v1/patients/{patient_b.id}",
            params={"organization_id": "00000000-0000-0000-0000-0000000000a1"},
            headers=headers,
        )

    assert cross_hospital.status_code == 403
    assert known_uuid.status_code == 404

    patient_a = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    patient_a.status = PatientStatus.INACTIVE
    await db_session.commit()
    async with await patient_client(db_session, settings) as client:
        token = await login(client, "physician.a@genomixai.demo")
        response = await client.get(
            "/api/v1/patients",
            params={"organization_id": "00000000-0000-0000-0000-0000000000a1", "search": "Amara"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json()["total"] == 0
    patient_a.status = PatientStatus.ACTIVE
    await db_session.commit()
