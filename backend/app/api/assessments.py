"""Persisted medication assessments and server-side analysis."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.patient_access import require_accessible_patient
from app.clinical_engine.context_builder import (
    AdverseDrugReactionContext,
    AllergyContext,
    ConditionContext,
    GenomicFindingContext,
    LabContext,
    MedicationContext,
    PatientClinicalContext,
    VitalContext,
)
from app.clinical_engine.pipeline import ClinicalAssessmentPipeline
from app.clinical_engine.result import FindingCategory
from app.clinical_engine.state_machine import AssessmentState
from app.clinical_engine.version import ENGINE_VERSION
from app.core.audit import append_audit_event
from app.core.authorization import require_organization_membership, require_role
from app.db.session import get_db
from app.models import (
    AdverseDrugReaction,
    Allergy,
    AssessmentEvidence,
    AssessmentFinding,
    AssessmentMedication,
    AssessmentRecommendation,
    AuditAction,
    Condition,
    ContraindicationRule,
    DoseRule,
    DrugDrugInteraction,
    GenomicProfile,
    GenomicRecordStatus,
    LabResult,
    Medication,
    MedicationAssessment,
    MedicationOrder,
    MedicationOrderStatus,
    MedicationStatus,
    MonitoringRule,
    OrganizationMembership,
    PharmacogenomicRule,
    PharmacogenomicRuleAlternative,
    Role,
    Vital,
)
from app.models.clinical import RecordStatus
from app.models.knowledge import KnowledgeStatus
from app.models.patient import Patient

router = APIRouter(tags=["medication assessments"])
CONTEXT_VERSION = "clinical-context-v1"


class AssessmentMedicationCreate(BaseModel):
    medication_id: UUID
    dose: Decimal | None = None
    dose_unit: str | None = Field(default=None, max_length=30)
    route: str | None = Field(default=None, max_length=50)
    frequency: str | None = Field(default=None, max_length=100)
    indication: str | None = Field(default=None, max_length=500)
    source: str = Field(default="MANUAL", min_length=1, max_length=50)

    @field_validator("dose")
    @classmethod
    def validate_dose(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and (not value.is_finite() or value <= 0):
            raise ValueError("dose must be finite and greater than zero")
        return value


class MedicationAssessmentCreate(BaseModel):
    medications: list[AssessmentMedicationCreate] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_unique_medications(self) -> "MedicationAssessmentCreate":
        identifiers = [medication.medication_id for medication in self.medications]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("an assessment cannot contain the same medication twice")
        return self


class AssessmentMedicationResponse(BaseModel):
    id: UUID
    medication_id: UUID
    medication: str
    standardized_code: str | None
    dose: str | None
    dose_unit: str | None
    route: str | None
    frequency: str | None
    indication: str | None
    source: str


class AssessmentEvidenceResponse(BaseModel):
    id: UUID
    evidence_source_id: UUID
    source_organization: str
    source_title: str
    source_version: str | None
    evidence_level: str | None
    source_url: str | None
    reference_identifier: str | None


class AssessmentFindingResponse(BaseModel):
    id: UUID
    category: FindingCategory
    severity: str
    classification: str
    summary: str
    details: str
    rule_type: str | None
    rule_id: str | None
    medication_references: list[str]
    actionable: bool
    metadata: dict
    evidence: list[AssessmentEvidenceResponse]


class AssessmentRecommendationResponse(BaseModel):
    id: UUID
    medication_id: UUID | None
    medication: str
    classification: str
    clinical_rationale: str
    patient_specific_rationale: str | None
    important_limitations: str | None
    contraindications: list[str]
    evidence: list[AssessmentEvidenceResponse]


class MedicationAssessmentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    organization_id: UUID
    created_by: UUID
    patient_context_version: str
    patient_context_reference: str
    engine_version: str
    status: AssessmentState
    created_at: datetime
    updated_at: datetime
    medications: list[AssessmentMedicationResponse]
    findings: list[AssessmentFindingResponse]
    recommendations: list[AssessmentRecommendationResponse]
    pharmacogenomic_findings: list[AssessmentFindingResponse]
    interaction_findings: list[AssessmentFindingResponse]
    allergy_findings: list[AssessmentFindingResponse]
    adverse_reaction_findings: list[AssessmentFindingResponse]
    clinical_factor_findings: list[AssessmentFindingResponse]
    dose_considerations: list[AssessmentFindingResponse]
    monitoring_recommendations: list[AssessmentFindingResponse]
    alternatives: list[AssessmentRecommendationResponse]
    evidence: list[AssessmentEvidenceResponse]
    ml_predictions: list[AssessmentFindingResponse]


@router.post(
    "/patients/{patient_id}/medication-assessments",
    response_model=MedicationAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assessment(
    patient_id: UUID,
    body: MedicationAssessmentCreate,
    request: Request,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        require_role(Role.PHYSICIAN, Role.HOSPITAL_ADMIN, Role.PLATFORM_ADMIN)
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MedicationAssessmentResponse:
    await require_accessible_patient(db, patient_id, membership)
    medication_ids = [medication.medication_id for medication in body.medications]
    medications = (
        await db.scalars(
            select(Medication).where(
                Medication.id.in_(medication_ids), Medication.status == MedicationStatus.ACTIVE
            )
        )
    ).all()
    medication_by_id = {medication.id: medication for medication in medications}
    if len(medication_by_id) != len(medication_ids):
        raise HTTPException(
            status_code=422, detail="One or more medications are invalid or inactive"
        )

    assessment = MedicationAssessment(
        patient_id=patient_id,
        organization_id=membership.organization_id,
        created_by=membership.user_id,
        patient_context_version=CONTEXT_VERSION,
        patient_context_reference="pending",
        engine_version=ENGINE_VERSION,
        status=AssessmentState.DRAFT,
    )
    db.add(assessment)
    await db.flush()
    assessment.patient_context_reference = (
        f"patient:{patient_id}:organization:{membership.organization_id}:assessment:{assessment.id}"
    )
    for medication_input in body.medications:
        db.add(
            AssessmentMedication(
                assessment_id=assessment.id,
                medication_id=medication_input.medication_id,
                dose=str(medication_input.dose) if medication_input.dose is not None else None,
                dose_unit=medication_input.dose_unit,
                route=medication_input.route,
                frequency=medication_input.frequency,
                indication=medication_input.indication,
                source=medication_input.source,
            )
        )
    append_audit_event(
        db,
        action=AuditAction.ASSESSMENT_CREATED,
        actor_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="MedicationAssessment",
        resource_id=assessment.id,
        request=request,
        metadata={"medication_count": len(body.medications)},
    )
    await db.commit()
    assessment = await _load_assessment(db, assessment.id, membership)
    return _assessment_response(assessment)


@router.get("/assessments/{assessment_id}", response_model=MedicationAssessmentResponse)
async def get_assessment(
    assessment_id: UUID,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MedicationAssessmentResponse:
    assessment = await _load_assessment(db, assessment_id, membership)
    await require_accessible_patient(db, assessment.patient_id, membership)
    return _assessment_response(assessment)


@router.get("/patients/{patient_id}/assessments", response_model=list[MedicationAssessmentResponse])
async def list_assessments(
    patient_id: UUID,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[MedicationAssessmentResponse]:
    await require_accessible_patient(db, patient_id, membership)
    assessments = (
        await db.scalars(
            _assessment_query().where(
                MedicationAssessment.patient_id == patient_id,
                MedicationAssessment.organization_id == membership.organization_id,
            )
        )
    ).all()
    return [_assessment_response(assessment) for assessment in assessments]


@router.post("/assessments/{assessment_id}/analyze", response_model=MedicationAssessmentResponse)
async def analyze_assessment(
    assessment_id: UUID,
    request: Request,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        require_role(Role.PHYSICIAN, Role.HOSPITAL_ADMIN, Role.PLATFORM_ADMIN)
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MedicationAssessmentResponse:
    assessment = await _load_assessment(db, assessment_id, membership)
    await require_accessible_patient(db, assessment.patient_id, membership)
    if assessment.status is not AssessmentState.DRAFT:
        raise HTTPException(status_code=409, detail="Only draft assessments can be analyzed")

    context = await _build_patient_context(db, assessment.patient_id, membership.organization_id)
    pipeline = await _build_pipeline(db)
    proposed = [_assessment_medication_context(item) for item in assessment.medications]
    result = pipeline.assess(context, proposed)
    for finding in result.findings:
        finding_record = AssessmentFinding(
            assessment_id=assessment.id,
            category=finding.category,
            severity=finding.severity,
            classification=finding.classification,
            summary=finding.summary,
            details=finding.details,
            rule_type=finding.category.value,
            rule_id=finding.rule_id,
            medication_references=list(finding.medications),
            actionable=finding.actionable,
            metadata_json=finding.metadata,
        )
        db.add(finding_record)
        await db.flush()
        _add_evidence(db, finding_record.id, None, finding.evidence)
    for recommendation in result.recommendations:
        source_assessment_medication = next(
            (
                item
                for item in assessment.medications
                if item.medication_id == _uuid_or_none(recommendation.trigger_medication_id)
            ),
            None,
        )
        recommendation_record = AssessmentRecommendation(
            assessment_id=assessment.id,
            assessment_medication_id=(
                source_assessment_medication.id if source_assessment_medication else None
            ),
            medication_id=_uuid_or_none(recommendation.medication_id),
            medication_name=recommendation.medication,
            classification=recommendation.classification,
            clinical_rationale=recommendation.clinical_rationale,
            patient_specific_rationale=recommendation.patient_specific_rationale,
            important_limitations=recommendation.important_limitations,
            contraindications=list(recommendation.contraindications),
        )
        db.add(recommendation_record)
        await db.flush()
        _add_evidence(db, None, recommendation_record.id, recommendation.evidence)
    assessment.status = AssessmentState.ANALYZED
    append_audit_event(
        db,
        action=AuditAction.ASSESSMENT_ANALYZED,
        actor_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="MedicationAssessment",
        resource_id=assessment.id,
        request=request,
        metadata={
            "finding_count": len(result.findings),
            "recommendation_count": len(result.recommendations),
        },
    )
    await db.commit()
    assessment = await _load_assessment(db, assessment.id, membership)
    return _assessment_response(assessment)


async def _load_assessment(
    db: AsyncSession, assessment_id: UUID, membership: OrganizationMembership
) -> MedicationAssessment:
    assessment = await db.scalar(
        _assessment_query().where(
            MedicationAssessment.id == assessment_id,
            MedicationAssessment.organization_id == membership.organization_id,
        )
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Medication assessment not found")
    return assessment


def _assessment_query():
    return (
        select(MedicationAssessment)
        .execution_options(populate_existing=True)
        .options(
            selectinload(MedicationAssessment.medications).joinedload(
                AssessmentMedication.medication
            ),
            selectinload(MedicationAssessment.findings).selectinload(AssessmentFinding.evidence),
            selectinload(MedicationAssessment.recommendations).joinedload(
                AssessmentRecommendation.medication
            ),
            selectinload(MedicationAssessment.recommendations).selectinload(
                AssessmentRecommendation.evidence
            ),
        )
        .order_by(MedicationAssessment.created_at.desc(), MedicationAssessment.id)
    )


def _assessment_medication_context(item: AssessmentMedication) -> MedicationContext:
    return MedicationContext(
        name=item.medication.generic_name,
        medication_id=str(item.medication.id),
        standardized_code=item.medication.standardized_code,
        brand_name=item.medication.brand_name,
        dose=Decimal(item.dose) if item.dose is not None else None,
        dose_unit=item.dose_unit,
        status="PROPOSED",
    )


async def _build_patient_context(
    db: AsyncSession, patient_id: UUID, organization_id: UUID
) -> PatientClinicalContext:
    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    conditions = (
        await db.scalars(
            select(Condition).where(
                Condition.patient_id == patient_id,
                Condition.organization_id == organization_id,
                Condition.status == RecordStatus.ACTIVE,
            )
        )
    ).all()
    orders = (
        await db.scalars(
            select(MedicationOrder)
            .options(joinedload(MedicationOrder.medication))
            .where(
                MedicationOrder.patient_id == patient_id,
                MedicationOrder.organization_id == organization_id,
                MedicationOrder.status == MedicationOrderStatus.ACTIVE,
            )
        )
    ).all()
    allergies = (
        await db.scalars(
            select(Allergy).where(
                Allergy.patient_id == patient_id,
                Allergy.organization_id == organization_id,
                Allergy.status == RecordStatus.ACTIVE,
            )
        )
    ).all()
    reactions = (
        await db.scalars(
            select(AdverseDrugReaction).where(
                AdverseDrugReaction.patient_id == patient_id,
                AdverseDrugReaction.organization_id == organization_id,
                AdverseDrugReaction.status == RecordStatus.ACTIVE,
            )
        )
    ).all()
    labs = (
        await db.scalars(
            select(LabResult).where(
                LabResult.patient_id == patient_id,
                LabResult.organization_id == organization_id,
                LabResult.status == RecordStatus.ACTIVE,
            )
        )
    ).all()
    vitals = (
        await db.scalars(
            select(Vital).where(
                Vital.patient_id == patient_id,
                Vital.organization_id == organization_id,
                Vital.status == RecordStatus.ACTIVE,
            )
        )
    ).all()
    profiles = (
        await db.scalars(
            select(GenomicProfile)
            .options(selectinload(GenomicProfile.variants))
            .where(
                GenomicProfile.patient_id == patient_id,
                GenomicProfile.organization_id == organization_id,
                GenomicProfile.status == GenomicRecordStatus.ACTIVE,
            )
        )
    ).all()
    genomic = [
        GenomicFindingContext(
            gene=variant.gene,
            phenotype=variant.phenotype,
            genotype=variant.genotype,
            variant=variant.variant,
            source=variant.source.value,
            profile_id=str(profile.id),
        )
        for profile in profiles
        for variant in profile.variants
        if variant.status is GenomicRecordStatus.ACTIVE
    ]
    return PatientClinicalContext(
        patient_id=str(patient.id),
        demographics={
            "date_of_birth": patient.date_of_birth.isoformat(),
            "sex": patient.sex.value,
        },
        conditions=[ConditionContext(name=item.name, code=item.code) for item in conditions],
        medications=[
            MedicationContext(
                name=order.medication.generic_name,
                medication_id=str(order.medication.id),
                standardized_code=order.medication.standardized_code,
                brand_name=order.medication.brand_name,
                dose=order.dose,
                dose_unit=order.dose_unit,
                status=order.status.value,
            )
            for order in orders
        ],
        allergies=[
            AllergyContext(
                allergen=item.allergen,
                reaction=item.reaction,
                severity=item.severity,
            )
            for item in allergies
        ],
        adverse_drug_reactions=[
            AdverseDrugReactionContext(
                medication=item.medication,
                reaction=item.reaction,
                severity=item.severity,
            )
            for item in reactions
        ],
        labs=[
            LabContext(
                test_name=item.test_name,
                numeric_value=item.numeric_value,
                unit=item.unit,
                value=item.value,
                reference_range=item.reference_range,
            )
            for item in labs
        ],
        vitals=[
            VitalContext(vital_type=item.vital_type.value, value=item.value, unit=item.unit)
            for item in vitals
        ],
        genomic_findings=genomic,
    )


async def _build_pipeline(db: AsyncSession) -> ClinicalAssessmentPipeline:
    pgx_rules = (
        await db.scalars(
            select(PharmacogenomicRule)
            .options(
                joinedload(PharmacogenomicRule.medication),
                joinedload(PharmacogenomicRule.evidence_source),
                selectinload(PharmacogenomicRule.alternatives).joinedload(
                    PharmacogenomicRuleAlternative.alternative_medication
                ),
                selectinload(PharmacogenomicRule.alternatives).joinedload(
                    PharmacogenomicRuleAlternative.evidence_source
                ),
            )
            .where(PharmacogenomicRule.status == KnowledgeStatus.ACTIVE)
        )
    ).all()
    interaction_rules = (
        await db.scalars(
            select(DrugDrugInteraction)
            .options(
                joinedload(DrugDrugInteraction.medication),
                joinedload(DrugDrugInteraction.interacting_medication),
                joinedload(DrugDrugInteraction.evidence_source),
            )
            .where(DrugDrugInteraction.status == KnowledgeStatus.ACTIVE)
        )
    ).all()
    contraindication_rules = (
        await db.scalars(
            select(ContraindicationRule)
            .options(
                joinedload(ContraindicationRule.medication),
                joinedload(ContraindicationRule.evidence_source),
            )
            .where(ContraindicationRule.status == KnowledgeStatus.ACTIVE)
        )
    ).all()
    dose_rules = (
        await db.scalars(
            select(DoseRule)
            .options(joinedload(DoseRule.medication), joinedload(DoseRule.evidence_source))
            .where(DoseRule.status == KnowledgeStatus.ACTIVE)
        )
    ).all()
    monitoring_rules = (
        await db.scalars(
            select(MonitoringRule)
            .options(
                joinedload(MonitoringRule.medication), joinedload(MonitoringRule.evidence_source)
            )
            .where(MonitoringRule.status == KnowledgeStatus.ACTIVE)
        )
    ).all()
    return ClinicalAssessmentPipeline(
        pharmacogenomic_rules=pgx_rules,
        interaction_rules=interaction_rules,
        contraindication_rules=contraindication_rules,
        dose_rules=dose_rules,
        monitoring_rules=monitoring_rules,
    )


def _add_evidence(db, finding_id, recommendation_id, evidence_items) -> None:
    for evidence in evidence_items:
        source_id = _uuid_or_none(evidence.source_id)
        if source_id is None:
            continue
        db.add(
            AssessmentEvidence(
                finding_id=finding_id,
                recommendation_id=recommendation_id,
                evidence_source_id=source_id,
                source_organization=evidence.organization,
                source_title=evidence.title,
                source_version=evidence.source_version,
                evidence_level=evidence.evidence_level,
                source_url=evidence.source_url,
                reference_identifier=evidence.reference_identifier,
            )
        )


def _assessment_response(assessment: MedicationAssessment) -> MedicationAssessmentResponse:
    medications = [
        AssessmentMedicationResponse(
            id=item.id,
            medication_id=item.medication_id,
            medication=item.medication.generic_name,
            standardized_code=item.medication.standardized_code,
            dose=item.dose,
            dose_unit=item.dose_unit,
            route=item.route,
            frequency=item.frequency,
            indication=item.indication,
            source=item.source,
        )
        for item in assessment.medications
    ]
    findings = [_finding_response(item) for item in assessment.findings]
    recommendations = [_recommendation_response(item) for item in assessment.recommendations]
    grouped = {
        "pharmacogenomic_findings": [
            item for item in findings if item.category is FindingCategory.PHARMACOGENOMICS
        ],
        "interaction_findings": [
            item for item in findings if item.category is FindingCategory.DRUG_INTERACTION
        ],
        "allergy_findings": [item for item in findings if item.category is FindingCategory.ALLERGY],
        "adverse_reaction_findings": [
            item for item in findings if item.category is FindingCategory.ADVERSE_DRUG_REACTION
        ],
        "clinical_factor_findings": [
            item for item in findings if item.category is FindingCategory.CLINICAL_FACTOR
        ],
        "dose_considerations": [item for item in findings if item.category is FindingCategory.DOSE],
        "monitoring_recommendations": [
            item for item in findings if item.category is FindingCategory.MONITORING
        ],
        "ml_predictions": [item for item in findings if item.category is FindingCategory.ML],
    }
    evidence = [
        _evidence_response(item) for finding in assessment.findings for item in finding.evidence
    ] + [
        _evidence_response(item)
        for recommendation in assessment.recommendations
        for item in recommendation.evidence
    ]
    return MedicationAssessmentResponse(
        id=assessment.id,
        patient_id=assessment.patient_id,
        organization_id=assessment.organization_id,
        created_by=assessment.created_by,
        patient_context_version=assessment.patient_context_version,
        patient_context_reference=assessment.patient_context_reference,
        engine_version=assessment.engine_version,
        status=assessment.status,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        medications=medications,
        findings=findings,
        recommendations=recommendations,
        alternatives=recommendations,
        evidence=evidence,
        **grouped,
    )


def _finding_response(finding: AssessmentFinding) -> AssessmentFindingResponse:
    return AssessmentFindingResponse(
        id=finding.id,
        category=finding.category,
        severity=finding.severity.value,
        classification=finding.classification,
        summary=finding.summary,
        details=finding.details,
        rule_type=finding.rule_type,
        rule_id=finding.rule_id,
        medication_references=finding.medication_references,
        actionable=finding.actionable,
        metadata=finding.metadata_json,
        evidence=[_evidence_response(item) for item in finding.evidence],
    )


def _recommendation_response(
    recommendation: AssessmentRecommendation,
) -> AssessmentRecommendationResponse:
    return AssessmentRecommendationResponse(
        id=recommendation.id,
        medication_id=recommendation.medication_id,
        medication=recommendation.medication_name,
        classification=recommendation.classification.value,
        clinical_rationale=recommendation.clinical_rationale,
        patient_specific_rationale=recommendation.patient_specific_rationale,
        important_limitations=recommendation.important_limitations,
        contraindications=recommendation.contraindications,
        evidence=[_evidence_response(item) for item in recommendation.evidence],
    )


def _evidence_response(evidence: AssessmentEvidence) -> AssessmentEvidenceResponse:
    return AssessmentEvidenceResponse(
        id=evidence.id,
        evidence_source_id=evidence.evidence_source_id,
        source_organization=evidence.source_organization,
        source_title=evidence.source_title,
        source_version=evidence.source_version,
        evidence_level=evidence.evidence_level,
        source_url=evidence.source_url,
        reference_identifier=evidence.reference_identifier,
    )


def _uuid_or_none(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except ValueError:
        return None


__all__ = ["router"]
