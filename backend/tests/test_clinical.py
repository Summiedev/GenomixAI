import httpx
import pytest
from sqlalchemy import select

from app.db.session import get_db
from app.main import create_app
from app.models import Patient

ORG_A = "00000000-0000-0000-0000-0000000000a1"
ORG_B = "00000000-0000-0000-0000-0000000000b1"


async def clinical_client(db_session, settings):
    application = create_app(settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://test")


async def auth_headers(client, email="physician.a@genomixai.demo"):
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "ChangeMe123!"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_all_clinical_domains_create_and_read(db_session, settings) -> None:
    patient = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    assert patient is not None
    async with await clinical_client(db_session, settings) as client:
        headers = await auth_headers(client)
        base = {"organization_id": ORG_A}
        encounter = await client.post(
            f"/api/v1/patients/{patient.id}/encounters",
            params=base,
            headers=headers,
            json={
                "encounter_type": "OUTPATIENT",
                "started_at": "2026-01-01T10:00:00Z",
                "reason": "Annual review",
            },
        )
        encounter_id = encounter.json()["id"]
        requests = [
            ("conditions", {"name": "Hypertension", "code": "I10", "onset_date": "2025-01-01"}),
            (
                "notes",
                {"note_type": "PROGRESS", "content": "Stable.", "noted_at": "2026-01-01T11:00:00Z"},
            ),
            (
                "vitals",
                {
                    "vital_type": "HEART_RATE",
                    "value": "72",
                    "unit": "bpm",
                    "measured_at": "2026-01-01T11:00:00Z",
                },
            ),
            (
                "labs",
                {
                    "test_name": "LDL",
                    "value": "120",
                    "numeric_value": "120",
                    "unit": "mg/dL",
                    "collected_at": "2026-01-01T12:00:00Z",
                },
            ),
            ("allergies", {"allergen": "Penicillin", "reaction": "Rash", "severity": "MODERATE"}),
            (
                "adverse-reactions",
                {
                    "medication": "Aspirin",
                    "reaction": "Dyspepsia",
                    "occurred_at": "2026-01-01T13:00:00Z",
                },
            ),
        ]
        created = []
        for suffix, body in requests:
            body["encounter_id"] = encounter_id
            response = await client.post(
                f"/api/v1/patients/{patient.id}/{suffix}",
                params=base,
                headers=headers,
                json=body,
            )
            assert response.status_code == 201, response.text
            created.append(response.json())
        reads = []
        for suffix, _ in requests:
            response = await client.get(
                f"/api/v1/patients/{patient.id}/{suffix}",
                params=base,
                headers=headers,
            )
            assert response.status_code == 200
            assert response.json()["total"] == 1
            reads.append(response.json()["items"][0])

    assert encounter.status_code == 201
    assert created[0]["name"] == "Hypertension"
    assert reads[2]["vital_type"] == "HEART_RATE"
    assert reads[3]["numeric_value"] == "120.00000"


@pytest.mark.asyncio
async def test_clinical_pagination_sorting_validation_and_isolation(db_session, settings) -> None:
    patient = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    patient_b = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000002")
    )
    assert patient is not None and patient_b is not None
    async with await clinical_client(db_session, settings) as client:
        headers = await auth_headers(client)
        for index in range(3):
            response = await client.post(
                f"/api/v1/patients/{patient.id}/notes",
                params={"organization_id": ORG_A},
                headers=headers,
                json={
                    "note_type": "PROGRESS",
                    "content": f"Note {index}",
                    "noted_at": f"2026-02-0{index + 1}T10:00:00Z",
                },
            )
            assert response.status_code == 201
        page = await client.get(
            f"/api/v1/patients/{patient.id}/notes",
            params={"organization_id": ORG_A, "page": 2, "page_size": 2},
            headers=headers,
        )
        invalid = await client.post(
            f"/api/v1/patients/{patient.id}/vitals",
            params={"organization_id": ORG_A},
            headers=headers,
            json={
                "vital_type": "NOT_A_VITAL",
                "value": 1,
                "unit": "x",
                "measured_at": "2026-02-01T10:00:00Z",
            },
        )
        cross_patient = await client.get(
            f"/api/v1/patients/{patient_b.id}/notes",
            params={"organization_id": ORG_A},
            headers=headers,
        )
        timeline = await client.get(
            f"/api/v1/patients/{patient.id}/timeline",
            params={"organization_id": ORG_A, "event_type": "CLINICAL_NOTE"},
            headers=headers,
        )

    assert page.status_code == 200
    assert page.json()["total"] >= 3
    assert page.json()["items"][0]["content"] == "Note 0"
    assert invalid.status_code == 422
    assert cross_patient.status_code == 404
    assert timeline.status_code == 200
    assert timeline.json()["total"] >= 3
    assert all(item["event_type"] == "CLINICAL_NOTE" for item in timeline.json()["items"])


@pytest.mark.asyncio
async def test_timeline_filter_date_order_resource_and_org_scope(db_session, settings) -> None:
    patient = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    assert patient is not None
    async with await clinical_client(db_session, settings) as client:
        headers = await auth_headers(client)
        response = await client.get(
            f"/api/v1/patients/{patient.id}/timeline",
            params={
                "organization_id": ORG_A,
                "from_timestamp": "2025-12-31T00:00:00Z",
                "to_timestamp": "2026-01-02T00:00:00Z",
            },
            headers=headers,
        )
        other_org = await client.get(
            f"/api/v1/patients/{patient.id}/timeline",
            params={"organization_id": ORG_B},
            headers=headers,
        )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(
        items[index]["timestamp"] >= items[index + 1]["timestamp"]
        for index in range(len(items) - 1)
    )
    assert all(item["linked_resource_id"] for item in items)
    assert other_org.status_code == 403
