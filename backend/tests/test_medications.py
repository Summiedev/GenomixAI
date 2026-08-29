import httpx
import pytest
from sqlalchemy import select

from app.db.session import get_db
from app.main import create_app
from app.models import Medication, Patient

ORG_A = "00000000-0000-0000-0000-0000000000a1"
ORG_B = "00000000-0000-0000-0000-0000000000b1"


async def medication_client(db_session, settings):
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
async def test_medication_reference_orders_statuses_and_history(db_session, settings) -> None:
    patient = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    medication = await db_session.scalar(
        select(Medication).where(Medication.generic_name == "Aspirin")
    )
    assert patient is not None and medication is not None
    async with await medication_client(db_session, settings) as client:
        headers = await auth_headers(client)
        reference = await client.post(
            "/api/v1/medications",
            headers=headers,
            json={"generic_name": "Metformin", "strength": "500 mg", "dosage_form": "TABLET"},
        )
        order = await client.post(
            f"/api/v1/patients/{patient.id}/medication-orders",
            params={"organization_id": ORG_A},
            headers=headers,
            json={
                "medication_id": str(medication.id),
                "dose": "81",
                "dose_unit": "mg",
                "route": "ORAL",
                "frequency": "ONCE_DAILY",
                "duration_value": 30,
                "duration_unit": "DAYS",
                "start_date": "2026-03-01",
            },
        )
        order_id = order.json()["id"]
        active = await client.patch(
            f"/api/v1/patients/{patient.id}/medication-orders/{order_id}/status",
            params={"organization_id": ORG_A},
            headers=headers,
            json={"status": "ACTIVE", "reason": "Explicitly approved"},
        )
        orders = await client.get(
            f"/api/v1/patients/{patient.id}/medications",
            params={"organization_id": ORG_A, "status": "ACTIVE"},
            headers=headers,
        )

    assert reference.status_code == 201
    assert order.status_code == 201
    assert order.json()["status"] == "PROPOSED"
    assert active.status_code == 200
    assert active.json()["status"] == "ACTIVE"
    assert len(active.json()["status_history"]) == 2
    assert orders.status_code == 200
    assert all(item["status"] == "ACTIVE" for item in orders.json()["items"])


@pytest.mark.asyncio
async def test_medication_validation_and_organization_isolation(db_session, settings) -> None:
    patient = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    patient_b = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000002")
    )
    medication = await db_session.scalar(
        select(Medication).where(Medication.generic_name == "Aspirin")
    )
    assert patient is not None and patient_b is not None and medication is not None
    async with await medication_client(db_session, settings) as client:
        headers = await auth_headers(client)
        invalid = await client.post(
            f"/api/v1/patients/{patient.id}/medication-orders",
            params={"organization_id": ORG_A},
            headers=headers,
            json={
                "medication_id": str(medication.id),
                "dose": "-1",
                "dose_unit": "mg",
                "route": "ORAL",
                "frequency": "ONCE_DAILY",
                "start_date": "2026-03-01",
            },
        )
        cross_patient = await client.get(
            f"/api/v1/patients/{patient_b.id}/medication-orders",
            params={"organization_id": ORG_A},
            headers=headers,
        )
        bad_transition = await client.patch(
            f"/api/v1/patients/{patient.id}/medication-orders/00000000-0000-0000-0000-000000000000/status",
            params={"organization_id": ORG_A},
            headers=headers,
            json={"status": "ACTIVE"},
        )

    assert invalid.status_code == 422
    assert cross_patient.status_code == 404
    assert bad_transition.status_code == 404
