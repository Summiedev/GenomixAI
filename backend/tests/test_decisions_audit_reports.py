from uuid import UUID

import httpx
import pytest
from sqlalchemy import select

from app.db.session import get_db
from app.main import create_app
from app.models import (
    AssessmentReport,
    AuditAction,
    AuditEvent,
    Medication,
    MedicationAssessment,
    Patient,
    PhysicianDecision,
)

ORG_A = "00000000-0000-0000-0000-0000000000a1"
ORG_B = "00000000-0000-0000-0000-0000000000b1"


async def workflow_client(db_session, settings):
    application = create_app(settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://test")


async def auth(client: httpx.AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ChangeMe123!"},
        headers={"X-Request-ID": "test-login-request"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def ids(db_session) -> tuple[UUID, UUID, UUID]:
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
    return patient.id, clopidogrel.id, aspirin.id


async def analyzed_assessment(client, patient_id: UUID, medication_id: UUID, headers):
    created = await client.post(
        f"/api/v1/patients/{patient_id}/medication-assessments",
        params={"organization_id": ORG_A},
        headers=headers,
        json={"medications": [{"medication_id": str(medication_id)}]},
    )
    assert created.status_code == 201
    assessment_id = created.json()["id"]
    analyzed = await client.post(
        f"/api/v1/assessments/{assessment_id}/analyze",
        params={"organization_id": ORG_A},
        headers=headers,
    )
    assert analyzed.status_code == 200
    return assessment_id


def final_medication(medication_id: UUID) -> dict:
    return {
        "medication_id": str(medication_id),
        "dose": "75",
        "dose_unit": "mg",
        "route": "ORAL",
        "frequency": "ONCE_DAILY",
        "indication": "Antiplatelet therapy",
        "start_date": "2026-08-30",
    }


@pytest.mark.asyncio
async def test_physician_final_decision_creates_order_and_retains_proposal(
    db_session, settings
) -> None:
    patient_id, clopidogrel_id, _ = await ids(db_session)
    async with await workflow_client(db_session, settings) as client:
        physician = await auth(client, "physician.a@genomixai.demo")
        assessment_id = await analyzed_assessment(client, patient_id, clopidogrel_id, physician)
        decision = await client.post(
            f"/api/v1/assessments/{assessment_id}/final-decision",
            params={"organization_id": ORG_A},
            headers={**physician, "X-Correlation-ID": "decision-flow"},
            json={
                "decision": "MODIFY",
                "decision_rationale": "Modified after clinical review.",
                "medications": [final_medication(clopidogrel_id)],
            },
        )
        assessment = await client.get(
            f"/api/v1/assessments/{assessment_id}",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        orders = await client.get(
            f"/api/v1/patients/{patient_id}/medication-orders",
            params={"organization_id": ORG_A, "status": "ACTIVE"},
            headers=physician,
        )
    assert decision.status_code == 201
    assert decision.json()["finalized"] is True
    assert decision.json()["decision"] == "MODIFY"
    assert decision.json()["medications"][0]["medication_order_id"]
    assert assessment.status_code == 200
    assert assessment.json()["status"] == "FINALIZED"
    assert len(assessment.json()["medications"]) == 1
    assert orders.status_code == 200
    assert any(item["source"].startswith("ASSESSMENT:") for item in orders.json()["items"])

    stored_decision = await db_session.scalar(
        select(PhysicianDecision).where(PhysicianDecision.id == UUID(decision.json()["id"]))
    )
    stored_assessment = await db_session.scalar(
        select(MedicationAssessment).where(MedicationAssessment.id == UUID(assessment_id))
    )
    assert stored_decision is not None and stored_assessment is not None
    assert stored_decision.assessment_id == stored_assessment.id


@pytest.mark.asyncio
async def test_finalization_after_pharmacist_review_and_immutable_final_state(
    db_session, settings
) -> None:
    patient_id, clopidogrel_id, _ = await ids(db_session)
    async with await workflow_client(db_session, settings) as client:
        physician = await auth(client, "physician.a@genomixai.demo")
        pharmacist = await auth(client, "pharmacist.a@genomixai.demo")
        assessment_id = await analyzed_assessment(client, patient_id, clopidogrel_id, physician)
        requested = await client.post(
            f"/api/v1/assessments/{assessment_id}/request-pharmacist-review",
            params={"organization_id": ORG_A},
            headers=physician,
            json={},
        )
        review_id = requested.json()["id"]
        started = await client.post(
            f"/api/v1/pharmacist/reviews/{review_id}/start",
            params={"organization_id": ORG_A},
            headers=pharmacist,
        )
        assert started.status_code == 200
        submitted = await client.post(
            f"/api/v1/pharmacist/reviews/{review_id}/submit",
            params={"organization_id": ORG_A},
            headers=pharmacist,
            json={
                "pharmacist_recommendation": "Use only after physician confirmation.",
                "pharmacist_rationale": "Reviewed the evidence and patient context.",
            },
        )
        assert submitted.status_code == 200
        finalized = await client.post(
            f"/api/v1/assessments/{assessment_id}/decision",
            params={"organization_id": ORG_A},
            headers=physician,
            json={
                "decision": "ACCEPT",
                "decision_rationale": "Accepted with pharmacist recommendation considered.",
                "pharmacist_review_id": review_id,
                "medications": [final_medication(clopidogrel_id)],
            },
        )
        after_final = await client.post(
            f"/api/v1/assessments/{assessment_id}/decision",
            params={"organization_id": ORG_A},
            headers=physician,
            json={
                "decision": "DECLINE",
                "decision_rationale": "Attempted correction without correction workflow.",
            },
        )
        pharmacist_attempt = await client.post(
            f"/api/v1/assessments/{assessment_id}/decision",
            params={"organization_id": ORG_A},
            headers=pharmacist,
            json={
                "decision": "ACCEPT",
                "decision_rationale": "Pharmacist must not finalize.",
                "medications": [final_medication(clopidogrel_id)],
            },
        )
    assert finalized.status_code == 201
    assert finalized.json()["pharmacist_review_id"] == review_id
    assert after_final.status_code == 409
    assert pharmacist_attempt.status_code == 403


@pytest.mark.asyncio
async def test_audit_events_and_report_are_persisted_and_tenant_scoped(
    db_session, settings
) -> None:
    patient_id, clopidogrel_id, _ = await ids(db_session)
    async with await workflow_client(db_session, settings) as client:
        physician_a = await auth(client, "physician.a@genomixai.demo")
        physician_b = await auth(client, "physician.b@genomixai.demo")
        assessment_id = await analyzed_assessment(client, patient_id, clopidogrel_id, physician_a)
        report = await client.post(
            f"/api/v1/assessments/{assessment_id}/reports",
            params={"organization_id": ORG_A},
            headers=physician_a,
        )
        download = await client.get(
            f"/api/v1/assessments/{assessment_id}/reports/{report.json()['id']}",
            params={"organization_id": ORG_A},
            headers=physician_a,
        )
        denied = await client.get(
            f"/api/v1/assessments/{assessment_id}/reports/{report.json()['id']}",
            params={"organization_id": ORG_B},
            headers=physician_b,
        )
        audit = await client.get(
            "/api/v1/audit/events",
            params={"organization_id": ORG_A, "resource_type": "AssessmentReport"},
            headers=await auth(client, "physician.a@genomixai.demo"),
        )
        audit_denied = await client.get(
            "/api/v1/audit/events",
            params={
                "organization_id": ORG_B,
                "resource_type": "AssessmentReport",
                "resource_id": report.json()["id"],
            },
            headers=physician_b,
        )
    assert report.status_code == 201
    assert report.json()["synthetic_data_marker"] is True
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/pdf")
    assert download.content.startswith(b"%PDF-1.4")
    assert denied.status_code == 404
    assert audit.status_code == 200
    assert audit.json() and audit.json()[0]["action"] == "REPORT_GENERATED"
    assert audit_denied.status_code == 200 and audit_denied.json() == []

    stored_report = await db_session.scalar(
        select(AssessmentReport).where(AssessmentReport.id == UUID(report.json()["id"]))
    )
    audit_event = await db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.action == AuditAction.REPORT_GENERATED,
            AuditEvent.resource_id == UUID(report.json()["id"]),
        )
    )
    assert (
        stored_report is not None and stored_report.report_data["assessment"]["id"] == assessment_id
    )
    assert audit_event is not None and audit_event.organization_id == UUID(ORG_A)
