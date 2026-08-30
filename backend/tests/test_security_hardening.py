import httpx
import pytest
from fastapi import HTTPException, Request
from sqlalchemy import select

from app.clinical_engine.context_builder import MedicationContext, PatientClinicalContext
from app.clinical_engine.ml.predictor import NullPredictor
from app.clinical_engine.ml.schemas import MLPrediction
from app.clinical_engine.pipeline import ClinicalAssessmentPipeline
from app.core.authorization import get_authenticated_user_id
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app
from app.models import Medication, Patient

ORG_A = "00000000-0000-0000-0000-0000000000a1"
UNKNOWN_ORG = "00000000-0000-0000-0000-0000000000ff"


async def security_client(db_session, settings):
    application = create_app(settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://test")


async def token(client, email):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_untrusted_organization_and_role_boundaries_are_denied(db_session, settings):
    patient = await db_session.scalar(
        select(Patient).where(Patient.genomix_patient_id == "GX-000001")
    )
    medication = await db_session.scalar(
        select(Medication).where(Medication.generic_name == "Aspirin")
    )
    assert patient and medication
    async with await security_client(db_session, settings) as client:
        physician = await token(client, "physician.a@genomixai.demo")
        pharmacist = await token(client, "pharmacist.a@genomixai.demo")
        wrong_tenant = await client.get(
            f"/api/v1/patients/{patient.id}",
            params={"organization_id": UNKNOWN_ORG},
            headers=physician,
        )
        physician_queue = await client.get(
            "/api/v1/pharmacist/reviews",
            params={"organization_id": ORG_A},
            headers=physician,
        )
        pharmacist_decision = await client.post(
            "/api/v1/assessments/00000000-0000-0000-0000-000000000001/decision",
            params={"organization_id": ORG_A},
            headers=pharmacist,
            json={"decision": "ACCEPT", "decision_rationale": "Not permitted"},
        )
        malformed = await client.get(
            "/api/v1/patients/not-a-uuid",
            params={"organization_id": ORG_A},
            headers=physician,
        )
    assert wrong_tenant.status_code == 403
    assert physician_queue.status_code == 403
    assert pharmacist_decision.status_code == 403
    assert malformed.status_code == 422
    assert "Traceback" not in malformed.text
    assert "password" not in malformed.text.lower()


def test_production_configuration_rejects_weak_secret_and_wildcard_cors():
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(app_env="production", jwt_secret="short")
    with pytest.raises(ValueError, match="Wildcard CORS"):
        Settings(cors_origins=["*"])


@pytest.mark.asyncio
async def test_cors_allows_only_configured_origins(settings):
    settings.cors_origins = ["https://clinical.example"]
    application = create_app(settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application), base_url="http://test"
    ) as client:
        allowed = await client.options(
            "/health",
            headers={
                "Origin": "https://clinical.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        denied = await client.options(
            "/health",
            headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"},
        )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://clinical.example"
    assert "access-control-allow-origin" not in denied.headers


@pytest.mark.asyncio
async def test_authentication_does_not_use_request_state_as_a_principal(db_session, settings):
    request = Request({"type": "http", "headers": [], "app": create_app(settings)})
    request.state.user_id = "00000000-0000-0000-0000-0000000000b1"
    # The dependency must follow the token. A nonexistent token subject still
    # fails authentication, rather than accepting request.state.user_id.
    with pytest.raises(HTTPException) as error:
        await get_authenticated_user_id(request, None, db_session)
    assert error.value.status_code == 401


def test_ml_failure_is_non_blocking_and_metadata_is_preserved():
    class FailingPredictor(NullPredictor):
        def predict(self, context, proposed_medications):
            raise RuntimeError("model unavailable")

    context = PatientClinicalContext()
    result = ClinicalAssessmentPipeline(predictor=FailingPredictor()).assess(
        context, [MedicationContext(medication_id="aspirin", name="Aspirin")]
    )
    assert result.findings == ()

    class TestPredictor(NullPredictor):
        def predict(self, context, proposed_medications):
            return MLPrediction(
                label="TEST_MODEL_RESULT",
                probability=0.7,
                model_name="test-model",
                model_version="1",
                feature_schema_version="test-v1",
            )

    prediction = ClinicalAssessmentPipeline(predictor=TestPredictor()).assess(
        context, [MedicationContext(medication_id="aspirin", name="Aspirin")]
    )
    finding = prediction.findings[0]
    assert finding.metadata["model_name"] == "test-model"
    assert finding.metadata["probability"] == 0.7
