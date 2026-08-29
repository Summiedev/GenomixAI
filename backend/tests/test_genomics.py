import httpx
import pytest
from sqlalchemy import select

from app.db.session import get_db
from app.main import create_app
from app.models import GenomicProfile, Patient

ORG_A = "00000000-0000-0000-0000-0000000000a1"
ORG_B = "00000000-0000-0000-0000-0000000000b1"


async def genomics_client(db_session, settings):
    application = create_app(settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://test")


async def auth_headers(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "physician.a@genomixai.demo", "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_genomic_profile_variants_interpretation_and_provenance(db_session, settings) -> None:
    patient = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    profile_without_interpretation = await db_session.scalar(
        select(GenomicProfile).where(GenomicProfile.source_version == "research-demo-1")
    )
    assert patient is not None and profile_without_interpretation is not None
    async with await genomics_client(db_session, settings) as client:
        headers = await auth_headers(client)
        profiles = await client.get(
            f"/api/v1/patients/{patient.id}/genomics",
            params={"organization_id": ORG_A},
            headers=headers,
        )
        detail = await client.get(
            f"/api/v1/patients/{patient.id}/genomics/{profile_without_interpretation.id}",
            params={"organization_id": ORG_A},
            headers=headers,
        )

    assert profiles.status_code == 200
    first = next(item for item in profiles.json()["items"] if item["source"] == "SYNTHETIC")
    assert {variant["gene"] for variant in first["variants"]} == {"CYP2C19", "DPYD"}
    assert first["source"] == "SYNTHETIC"
    assert first["validation_status"] == "NOT_CLINICALLY_VALIDATED"
    assert first["interpretations"][0]["source_version"] == "demo-interpretation-1"
    assert first["interpretations"][0]["evidence_references"][0]["source"] == "SYNTHETIC"
    assert detail.status_code == 200
    assert detail.json()["variants"] == []
    assert detail.json()["interpretations"] == []


@pytest.mark.asyncio
async def test_genomics_patient_and_organization_access_isolation(db_session, settings) -> None:
    patient_b = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000002")
    )
    assert patient_b is not None
    async with await genomics_client(db_session, settings) as client:
        headers = await auth_headers(client)
        wrong_organization = await client.get(
            f"/api/v1/patients/{patient_b.id}/genomics",
            params={"organization_id": ORG_A},
            headers=headers,
        )
        inaccessible_organization = await client.get(
            f"/api/v1/patients/{patient_b.id}/genomics",
            params={"organization_id": ORG_B},
            headers=headers,
        )

    assert wrong_organization.status_code == 404
    assert inaccessible_organization.status_code == 403
