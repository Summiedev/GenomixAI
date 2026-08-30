from uuid import UUID

import httpx
import pytest
from sqlalchemy import select

from app.db.session import get_db
from app.main import create_app
from app.models import (
    AssessmentEvidence,
    AssessmentFinding,
    Medication,
    MedicationAssessment,
    Patient,
    PharmacistReview,
)

ORG_A = "00000000-0000-0000-0000-0000000000a1"
ORG_B = "00000000-0000-0000-0000-0000000000b1"


async def assessment_client(db_session, settings):
    application = create_app(settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://test")


async def login(client: httpx.AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def seeded_ids(db_session) -> tuple[UUID, UUID, UUID, UUID]:
    patient = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    patient_b = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000002")
    )
    clopidogrel = await db_session.scalar(
        select(Medication).where(Medication.generic_name == "Clopidogrel")
    )
    aspirin = await db_session.scalar(
        select(Medication).where(Medication.generic_name == "Aspirin")
    )
    assert patient and patient_b and clopidogrel and aspirin
    return patient.id, patient_b.id, clopidogrel.id, aspirin.id


@pytest.mark.asyncio
async def test_create_multi_medication_assessment_and_persist_analysis(
    db_session, settings
) -> None:
    patient_id, _, clopidogrel_id, aspirin_id = await seeded_ids(db_session)
    async with await assessment_client(db_session, settings) as client:
        physician = await login(client, "physician.a@genomixai.demo")
        created = await client.post(
            f"/api/v1/patients/{patient_id}/medication-assessments",
            params={"organization_id": ORG_A},
            headers=physician,
            json={
                "medications": [
                    {"medication_id": str(clopidogrel_id), "dose": "75", "dose_unit": "mg"},
                    {"medication_id": str(aspirin_id), "dose": "81", "dose_unit": "mg"},
                ]
            },
        )
        assert created.status_code == 201
        assessment_id = created.json()["id"]
        assert created.json()["status"] == "DRAFT"
        assert created.json()["engine_version"]
        assert len(created.json()["medications"]) == 2

        analyzed = await client.post(
            f"/api/v1/assessments/{assessment_id}/analyze",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        assert analyzed.status_code == 200
        assert analyzed.json()["status"] == "ANALYZED"
        assert analyzed.json()["pharmacogenomic_findings"]
        assert analyzed.json()["alternatives"]
        assert analyzed.json()["evidence"]

        retrieved = await client.get(
            f"/api/v1/assessments/{assessment_id}",
            params={"organization_id": ORG_A},
            headers=physician,
        )
    assert retrieved.status_code == 200
    assert retrieved.json()["id"] == assessment_id
    assert retrieved.json()["status"] == "ANALYZED"

    db_session.expire_all()
    persisted = await db_session.scalar(
        select(MedicationAssessment).where(MedicationAssessment.id == UUID(assessment_id))
    )
    finding_count = await db_session.scalar(
        select(AssessmentFinding.id).where(AssessmentFinding.assessment_id == UUID(assessment_id))
    )
    evidence_count = await db_session.scalar(
        select(AssessmentEvidence.id).where(
            AssessmentEvidence.finding_id.in_(
                select(AssessmentFinding.id).where(
                    AssessmentFinding.assessment_id == UUID(assessment_id)
                )
            )
        )
    )
    assert persisted is not None and persisted.engine_version
    assert finding_count is not None
    assert evidence_count is not None


@pytest.mark.asyncio
async def test_assessment_validation_and_organization_ownership(db_session, settings) -> None:
    patient_id, patient_b_id, clopidogrel_id, _ = await seeded_ids(db_session)
    async with await assessment_client(db_session, settings) as client:
        physician_a = await login(client, "physician.a@genomixai.demo")
        invalid_medication = await client.post(
            f"/api/v1/patients/{patient_id}/medication-assessments",
            params={"organization_id": ORG_A},
            headers=physician_a,
            json={"medications": [{"medication_id": "00000000-0000-0000-0000-000000000000"}]},
        )
        duplicate_medications = await client.post(
            f"/api/v1/patients/{patient_id}/medication-assessments",
            params={"organization_id": ORG_A},
            headers=physician_a,
            json={
                "medications": [
                    {"medication_id": str(clopidogrel_id)},
                    {"medication_id": str(clopidogrel_id)},
                ]
            },
        )
        cross_organization_patient = await client.post(
            f"/api/v1/patients/{patient_b_id}/medication-assessments",
            params={"organization_id": ORG_A},
            headers=physician_a,
            json={"medications": [{"medication_id": str(clopidogrel_id)}]},
        )
    assert invalid_medication.status_code == 422
    assert duplicate_medications.status_code == 422
    assert cross_organization_patient.status_code == 404


async def create_analyzed_assessment(client, patient_id: UUID, medication_id: UUID, headers):
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


@pytest.mark.asyncio
async def test_pharmacist_review_workflow_is_org_scoped_and_role_limited(
    db_session, settings
) -> None:
    patient_id, _, clopidogrel_id, _ = await seeded_ids(db_session)
    async with await assessment_client(db_session, settings) as client:
        physician = await login(client, "physician.a@genomixai.demo")
        pharmacist_a = await login(client, "pharmacist.a@genomixai.demo")
        pharmacist_b = await login(client, "pharmacist.b@genomixai.demo")
        assessment_id = await create_analyzed_assessment(
            client, patient_id, clopidogrel_id, physician
        )
        requested = await client.post(
            f"/api/v1/assessments/{assessment_id}/request-pharmacist-review",
            params={"organization_id": ORG_A},
            headers=physician,
            json={"priority": "HIGH", "physician_message": "Please review."},
        )
        assert requested.status_code == 201
        review_id = requested.json()["id"]

        queue_a = await client.get(
            "/api/v1/pharmacist/reviews",
            params={"organization_id": ORG_A},
            headers=pharmacist_a,
        )
        queue_b = await client.get(
            "/api/v1/pharmacist/reviews",
            params={"organization_id": ORG_B},
            headers=pharmacist_b,
        )
        started = await client.post(
            f"/api/v1/pharmacist/reviews/{review_id}/start",
            params={"organization_id": ORG_A},
            headers=pharmacist_a,
        )
        submitted = await client.post(
            f"/api/v1/pharmacist/reviews/{review_id}/submit",
            params={"organization_id": ORG_A},
            headers=pharmacist_a,
            json={
                "pharmacist_recommendation": "Proceed only after clinical review.",
                "pharmacist_rationale": "Evidence and patient factors reviewed.",
                "monitoring_recommendations": ["Monitor as clinically indicated."],
                "recommended_changes": [{"field": "dose", "action": "review"}],
            },
        )
        physician_view = await client.get(
            f"/api/v1/pharmacist/reviews/{review_id}",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        pharmacist_finalize_attempt = await client.post(
            f"/api/v1/assessments/{assessment_id}/analyze",
            params={"organization_id": ORG_A},
            headers=pharmacist_a,
        )
        invalid_start = await client.post(
            f"/api/v1/pharmacist/reviews/{review_id}/start",
            params={"organization_id": ORG_A},
            headers=pharmacist_a,
        )
    assert requested.json()["status"] == "REQUESTED"
    assert any(item["id"] == review_id for item in queue_a.json())
    assert queue_b.status_code == 200 and queue_b.json() == []
    assert started.status_code == 200 and started.json()["status"] == "IN_PROGRESS"
    assert submitted.status_code == 200 and submitted.json()["status"] == "SUBMITTED"
    assert physician_view.status_code == 200
    assert physician_view.json()["pharmacist_recommendation"]
    assert pharmacist_finalize_attempt.status_code == 403
    assert invalid_start.status_code == 409

    persisted_review = await db_session.scalar(
        select(PharmacistReview).where(PharmacistReview.id == UUID(review_id))
    )
    assert persisted_review is not None
