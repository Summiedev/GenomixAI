from uuid import UUID

import httpx
import pytest
from sqlalchemy import select

from app.db.session import get_db
from app.main import create_app
from app.models import AuditAction, AuditEvent, Medication, Patient

ORG_A = "00000000-0000-0000-0000-0000000000a1"
ORG_B = "00000000-0000-0000-0000-0000000000b1"


async def client_for(db_session, settings):
    app = create_app(settings)

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def login(client, email):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_postgres_clinical_workflow_notifications_and_tenant_isolation(
    db_session, db_engine, settings
):
    patient = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    clopidogrel = await db_session.scalar(
        select(Medication).where(Medication.generic_name == "Clopidogrel")
    )
    aspirin = await db_session.scalar(
        select(Medication).where(Medication.generic_name == "Aspirin")
    )
    assert patient and clopidogrel and aspirin

    async with await client_for(db_session, settings) as client:
        physician = await login(client, "physician.a@genomixai.demo")
        pharmacist = await login(client, "pharmacist.a@genomixai.demo")
        hospital_b = await login(client, "physician.b@genomixai.demo")

        search = await client.get(
            "/api/v1/patients",
            params={"organization_id": ORG_A, "search": "Ada"},
            headers=physician,
        )
        chart = await client.get(
            f"/api/v1/patients/{patient.id}",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        timeline = await client.get(
            f"/api/v1/patients/{patient.id}/timeline",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        genomics = await client.get(
            f"/api/v1/patients/{patient.id}/genomics",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        created = await client.post(
            f"/api/v1/patients/{patient.id}/medication-assessments",
            params={"organization_id": ORG_A},
            headers=physician,
            json={
                "medications": [
                    {
                        "medication_id": str(clopidogrel.id),
                        "dose": "75",
                        "dose_unit": "mg",
                        "route": "ORAL",
                        "frequency": "ONCE_DAILY",
                    },
                    {
                        "medication_id": str(aspirin.id),
                        "dose": "81",
                        "dose_unit": "mg",
                        "route": "ORAL",
                        "frequency": "ONCE_DAILY",
                    },
                ]
            },
        )
        assessment_id = created.json()["id"]
        analyzed = await client.post(
            f"/api/v1/assessments/{assessment_id}/analyze",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        requested = await client.post(
            f"/api/v1/assessments/{assessment_id}/request-pharmacist-review",
            params={"organization_id": ORG_A},
            headers=physician,
            json={
                "priority": "HIGH",
                "physician_message": "Please review the structured findings.",
            },
        )
        review_id = requested.json()["id"]
        pharmacist_notifications = await client.get(
            "/api/v1/notifications", params={"organization_id": ORG_A}, headers=pharmacist
        )
        started = await client.post(
            f"/api/v1/pharmacist/reviews/{review_id}/start",
            params={"organization_id": ORG_A},
            headers=pharmacist,
        )
        submitted = await client.post(
            f"/api/v1/pharmacist/reviews/{review_id}/submit",
            params={"organization_id": ORG_A},
            headers=pharmacist,
            json={
                "pharmacist_recommendation": "Proceed with physician review.",
                "pharmacist_rationale": "Evidence and patient context reviewed.",
            },
        )
        physician_notifications = await client.get(
            "/api/v1/notifications", params={"organization_id": ORG_A}, headers=physician
        )
        final = await client.post(
            f"/api/v1/assessments/{assessment_id}/final-decision",
            params={"organization_id": ORG_A},
            headers=physician,
            json={
                "decision": "ACCEPT",
                "decision_rationale": "Finalized after pharmacist review.",
                "pharmacist_review_id": review_id,
                "medications": [
                    {
                        "medication_id": str(clopidogrel.id),
                        "dose": "75",
                        "dose_unit": "mg",
                        "route": "ORAL",
                        "frequency": "ONCE_DAILY",
                        "start_date": "2026-08-30",
                    },
                    {
                        "medication_id": str(aspirin.id),
                        "dose": "81",
                        "dose_unit": "mg",
                        "route": "ORAL",
                        "frequency": "ONCE_DAILY",
                        "start_date": "2026-08-30",
                    },
                ],
            },
        )
        report = await client.post(
            f"/api/v1/assessments/{assessment_id}/reports",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        marked = await client.post(
            f"/api/v1/notifications/{physician_notifications.json()[0]['id']}/read",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        hospital_b_patient = await client.get(
            f"/api/v1/patients/{patient.id}", params={"organization_id": ORG_B}, headers=hospital_b
        )
        hospital_b_assessment = await client.get(
            f"/api/v1/assessments/{assessment_id}",
            params={"organization_id": ORG_B},
            headers=hospital_b,
        )
        hospital_b_review = await client.get(
            f"/api/v1/pharmacist/reviews/{review_id}",
            params={"organization_id": ORG_B},
            headers=hospital_b,
        )
        hospital_b_notifications = await client.get(
            "/api/v1/notifications", params={"organization_id": ORG_B}, headers=hospital_b
        )

    assert (
        search.status_code
        == chart.status_code
        == timeline.status_code
        == genomics.status_code
        == 200
    )
    assert len(created.json()["medications"]) == 2
    assert analyzed.status_code == 200
    assert requested.status_code == 201 and started.status_code == submitted.status_code == 200
    assert any(
        item["notification_type"] == "PHARMACIST_REVIEW_REQUESTED"
        for item in pharmacist_notifications.json()
    )
    assert any(
        item["notification_type"] == "PHARMACIST_RECOMMENDATION_SUBMITTED"
        for item in physician_notifications.json()
    )
    assert final.status_code == 201
    assert report.status_code == 201 and report.json()["synthetic_data_marker"] is True
    assert marked.status_code == 200
    assert (
        hospital_b_patient.status_code
        == hospital_b_assessment.status_code
        == hospital_b_review.status_code
        == 404
    )
    assert hospital_b_notifications.status_code == 200 and hospital_b_notifications.json() == []

    await db_session.commit()
    stored_audit = await db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.action == AuditAction.FINAL_DECISION_RECORDED,
            AuditEvent.resource_type == "PhysicianDecision",
            AuditEvent.resource_id == UUID(final.json()["id"]),
        )
    )
    assert stored_audit is not None and stored_audit.organization_id == UUID(ORG_A)
