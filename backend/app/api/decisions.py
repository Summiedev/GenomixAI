"""Physician decision capture and transactional medication finalization."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.assessments import _load_assessment
from app.api.patient_access import require_accessible_patient
from app.clinical_engine.state_machine import (
    AssessmentState,
    AssessmentStateMachine,
    AssessmentTransitionError,
)
from app.core.audit import append_audit_event
from app.core.authorization import require_organization_membership, require_role
from app.core.notifications import notify_active_role, notify_user
from app.db.session import get_db
from app.models import (
    AuditAction,
    DurationUnit,
    Medication,
    MedicationAssessment,
    MedicationOrder,
    MedicationOrderStatus,
    MedicationOrderStatusHistory,
    MedicationStatus,
    NotificationType,
    OrganizationMembership,
    PharmacistReview,
    PharmacistReviewStatus,
    PhysicianDecision,
    PhysicianDecisionMedication,
    PhysicianDecisionType,
    Role,
)
from app.models.timeline import ClinicalEvent, ClinicalEventType

router = APIRouter(tags=["physician decisions"])


class FinalMedicationCreate(BaseModel):
    medication_id: UUID
    dose: Decimal
    dose_unit: str = Field(min_length=1, max_length=30)
    route: str = Field(min_length=1, max_length=50)
    frequency: str = Field(min_length=1, max_length=100)
    duration_value: Decimal | None = None
    duration_unit: DurationUnit | None = None
    indication: str | None = Field(default=None, max_length=500)
    start_date: date
    end_date: date | None = None

    @field_validator("dose", "duration_value")
    @classmethod
    def validate_positive_numbers(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and (not value.is_finite() or value <= 0):
            raise ValueError("dose and duration values must be finite and greater than zero")
        return value

    @model_validator(mode="after")
    def validate_dates_and_duration(self) -> "FinalMedicationCreate":
        if (self.duration_value is None) != (self.duration_unit is None):
            raise ValueError("duration_value and duration_unit must be supplied together")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class PhysicianDecisionCreate(BaseModel):
    decision: PhysicianDecisionType
    decision_rationale: str = Field(min_length=1, max_length=10000)
    medications: list[FinalMedicationCreate] = Field(default_factory=list, max_length=20)
    pharmacist_review_id: UUID | None = None
    finalize: bool | None = None

    @model_validator(mode="after")
    def validate_unique_medications(self) -> "PhysicianDecisionCreate":
        medication_ids = [item.medication_id for item in self.medications]
        if len(medication_ids) != len(set(medication_ids)):
            raise ValueError("a final decision cannot contain the same medication twice")
        return self


class FinalMedicationResponse(BaseModel):
    id: UUID
    medication_id: UUID
    medication_order_id: UUID | None
    dose: Decimal
    dose_unit: str
    route: str
    frequency: str
    duration_value: Decimal | None
    duration_unit: str | None
    indication: str | None
    start_date: date
    end_date: date | None


class PhysicianDecisionResponse(BaseModel):
    id: UUID
    assessment_id: UUID
    organization_id: UUID
    physician_id: UUID
    pharmacist_review_id: UUID | None
    decision: PhysicianDecisionType
    decision_rationale: str
    assessment_version: str
    finalized: bool
    finalized_at: datetime | None
    created_at: datetime
    updated_at: datetime
    medications: list[FinalMedicationResponse]


@router.get(
    "/assessments/{assessment_id}/decisions",
    response_model=list[PhysicianDecisionResponse],
)
async def list_physician_decisions(
    assessment_id: UUID,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[PhysicianDecisionResponse]:
    assessment = await _load_assessment(db, assessment_id, membership)
    await require_accessible_patient(db, assessment.patient_id, membership)
    decisions = (
        await db.scalars(
            select(PhysicianDecision.id)
            .where(
                PhysicianDecision.assessment_id == assessment.id,
                PhysicianDecision.organization_id == membership.organization_id,
            )
            .order_by(PhysicianDecision.created_at)
        )
    ).all()
    return [await _load_decision(db, decision_id, membership) for decision_id in decisions]


@router.post(
    "/assessments/{assessment_id}/decision",
    response_model=PhysicianDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/assessments/{assessment_id}/final-decision",
    response_model=PhysicianDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_physician_decision(
    assessment_id: UUID,
    body: PhysicianDecisionCreate,
    request: Request,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        require_role(Role.PHYSICIAN, Role.HOSPITAL_ADMIN, Role.PLATFORM_ADMIN)
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PhysicianDecisionResponse:
    assessment = await _load_assessment(db, assessment_id, membership)
    await require_accessible_patient(db, assessment.patient_id, membership)
    if assessment.status in {AssessmentState.FINALIZED, AssessmentState.CANCELLED}:
        raise HTTPException(status_code=409, detail="This assessment is immutable")
    if assessment.status not in {
        AssessmentState.ANALYZED,
        AssessmentState.PHARMACIST_RECOMMENDED,
        AssessmentState.RETURNED_TO_PHYSICIAN,
    }:
        raise HTTPException(
            status_code=409, detail="Assessment is not ready for physician decision"
        )

    should_finalize = (
        body.finalize
        if body.finalize is not None
        else body.decision is not PhysicianDecisionType.REQUEST_CLARIFICATION
    )
    if body.decision is PhysicianDecisionType.REQUEST_CLARIFICATION:
        if should_finalize or body.medications:
            raise HTTPException(
                status_code=422,
                detail="Clarification requests cannot finalize or include final medications",
            )
    elif not should_finalize:
        raise HTTPException(status_code=422, detail="Therapy decisions must be finalized")
    elif body.decision is PhysicianDecisionType.DECLINE and body.medications:
        raise HTTPException(status_code=422, detail="Declined therapy cannot include medications")
    elif body.decision is PhysicianDecisionType.MODIFY and not body.medications:
        raise HTTPException(status_code=422, detail="Modified therapy requires final medications")

    review = await _resolve_review(db, assessment, membership, body.pharmacist_review_id)
    final_medications = body.medications
    if body.decision is PhysicianDecisionType.ACCEPT and not final_medications:
        final_medications = _copy_complete_proposal(assessment)
    active_medications = await _active_medications(db, final_medications)
    decision_count = await db.scalar(
        select(func.count(PhysicianDecision.id)).where(
            PhysicianDecision.assessment_id == assessment.id,
            PhysicianDecision.organization_id == membership.organization_id,
        )
    )
    decision = PhysicianDecision(
        assessment_id=assessment.id,
        organization_id=membership.organization_id,
        physician_id=membership.user_id,
        pharmacist_review_id=review.id if review else None,
        decision=body.decision,
        decision_rationale=body.decision_rationale,
        assessment_version=f"assessment-v{int(decision_count or 0) + 1}",
        finalized=should_finalize,
        finalized_at=datetime.now(UTC) if should_finalize else None,
    )
    db.add(decision)
    await db.flush()

    if should_finalize:
        _transition_to_finalized(assessment, membership)
        for item in final_medications:
            medication = active_medications[item.medication_id]
            order = MedicationOrder(
                patient_id=assessment.patient_id,
                organization_id=membership.organization_id,
                medication_id=medication.id,
                medication=medication,
                dose=item.dose,
                dose_unit=item.dose_unit,
                route=item.route,
                frequency=item.frequency,
                duration_value=item.duration_value,
                duration_unit=item.duration_unit,
                indication=item.indication,
                start_date=item.start_date,
                end_date=item.end_date,
                prescriber_id=membership.user_id,
                status=MedicationOrderStatus.ACTIVE,
                source=f"ASSESSMENT:{assessment.id}",
            )
            db.add(order)
            await db.flush()
            history = MedicationOrderStatusHistory(
                order_id=order.id,
                from_status=None,
                to_status=MedicationOrderStatus.ACTIVE,
                changed_by=membership.user_id,
                changed_at=datetime.now(UTC),
                reason=f"Finalized from medication assessment {assessment.id}",
            )
            db.add(history)
            await db.flush()
            db.add(
                PhysicianDecisionMedication(
                    decision_id=decision.id,
                    medication_id=medication.id,
                    medication_order_id=order.id,
                    dose=item.dose,
                    dose_unit=item.dose_unit,
                    route=item.route,
                    frequency=item.frequency,
                    duration_value=item.duration_value,
                    duration_unit=item.duration_unit.value if item.duration_unit else None,
                    indication=item.indication,
                    start_date=item.start_date,
                    end_date=item.end_date,
                )
            )
            db.add(
                ClinicalEvent(
                    patient_id=assessment.patient_id,
                    organization_id=membership.organization_id,
                    event_type=ClinicalEventType.FINAL_DECISION,
                    event_timestamp=datetime.combine(
                        item.start_date, datetime.min.time(), tzinfo=UTC
                    ),
                    actor_id=membership.user_id,
                    department_id=membership.department_id,
                    linked_resource_type="PhysicianDecision",
                    linked_resource_id=decision.id,
                    dedupe_key=f"PhysicianDecision:{decision.id}:{medication.id}",
                    summary=(
                        f"Final physician decision: {body.decision.value} {medication.generic_name}"
                    ),
                    source="CLINICAL_WORKFLOW",
                )
            )
    append_audit_event(
        db,
        action=AuditAction.FINAL_DECISION_RECORDED,
        actor_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="PhysicianDecision",
        resource_id=decision.id,
        request=request,
        metadata={"decision": body.decision.value, "finalized": should_finalize},
    )
    if body.decision is PhysicianDecisionType.MODIFY:
        append_audit_event(
            db,
            action=AuditAction.ASSESSMENT_MODIFIED,
            actor_id=membership.user_id,
            organization_id=membership.organization_id,
            resource_type="MedicationAssessment",
            resource_id=assessment.id,
            request=request,
            metadata={"decision_version": decision.assessment_version},
        )
    if review is not None:
        append_audit_event(
            db,
            action=AuditAction.PHYSICIAN_REVIEWED_RECOMMENDATION,
            actor_id=membership.user_id,
            organization_id=membership.organization_id,
            resource_type="PharmacistReview",
            resource_id=review.id,
            request=request,
        )
        if review.assigned_pharmacist_id is not None:
            await notify_user(
                db,
                recipient_user_id=review.assigned_pharmacist_id,
                organization_id=membership.organization_id,
                notification_type=NotificationType.FINAL_DECISION_RECORDED,
                title="Final physician decision recorded",
                message="The physician has recorded a final decision for the reviewed assessment.",
                resource_type="PhysicianDecision",
                resource_id=decision.id,
            )
    else:
        await notify_active_role(
            db,
            organization_id=membership.organization_id,
            role=Role.CLINICAL_PHARMACIST,
            notification_type=NotificationType.FINAL_DECISION_RECORDED,
            title="Final physician decision recorded",
            message="A final physician decision has been recorded for a medication assessment.",
            resource_type="PhysicianDecision",
            resource_id=decision.id,
        )
    await db.commit()
    return await _load_decision(db, decision.id, membership)


async def _resolve_review(
    db: AsyncSession,
    assessment: MedicationAssessment,
    membership: OrganizationMembership,
    review_id: UUID | None,
) -> PharmacistReview | None:
    query = select(PharmacistReview).where(
        PharmacistReview.assessment_id == assessment.id,
        PharmacistReview.organization_id == membership.organization_id,
    )
    if review_id is not None:
        review = await db.scalar(query.where(PharmacistReview.id == review_id))
        if review is None:
            raise HTTPException(status_code=404, detail="Pharmacist review not found")
    else:
        review = await db.scalar(
            query.where(
                PharmacistReview.status.in_(
                    [PharmacistReviewStatus.SUBMITTED, PharmacistReviewStatus.RETURNED]
                )
            ).order_by(PharmacistReview.created_at.desc())
        )
    if review is not None and review.status not in {
        PharmacistReviewStatus.SUBMITTED,
        PharmacistReviewStatus.RETURNED,
    }:
        raise HTTPException(status_code=409, detail="Pharmacist review is not complete")
    return review


async def _active_medications(
    db: AsyncSession, items: list[FinalMedicationCreate]
) -> dict[UUID, Medication]:
    if not items:
        return {}
    medications = (
        await db.scalars(
            select(Medication).where(
                Medication.id.in_([item.medication_id for item in items]),
                Medication.status == MedicationStatus.ACTIVE,
            )
        )
    ).all()
    result = {medication.id: medication for medication in medications}
    if len(result) != len(items):
        raise HTTPException(status_code=422, detail="One or more final medications are invalid")
    return result


def _copy_complete_proposal(assessment: MedicationAssessment) -> list[FinalMedicationCreate]:
    copied: list[FinalMedicationCreate] = []
    for item in assessment.medications:
        if not all((item.dose, item.dose_unit, item.route, item.frequency)):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Accept requires complete final medication details; provide the final "
                    "medications explicitly when the proposal is incomplete"
                ),
            )
        copied.append(
            FinalMedicationCreate(
                medication_id=item.medication_id,
                dose=Decimal(item.dose),
                dose_unit=item.dose_unit,
                route=item.route,
                frequency=item.frequency,
                indication=item.indication,
                start_date=date.today(),
            )
        )
    return copied


def _transition_to_finalized(
    assessment: MedicationAssessment, membership: OrganizationMembership
) -> None:
    machine = AssessmentStateMachine(assessment.status)
    try:
        machine.transition(AssessmentState.FINALIZED, membership.role)
    except AssessmentTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    assessment.status = machine.state


async def _load_decision(
    db: AsyncSession, decision_id: UUID, membership: OrganizationMembership
) -> PhysicianDecisionResponse:
    decision = await db.scalar(
        select(PhysicianDecision)
        .options(
            selectinload(PhysicianDecision.medications).joinedload(
                PhysicianDecisionMedication.medication
            )
        )
        .where(
            PhysicianDecision.id == decision_id,
            PhysicianDecision.organization_id == membership.organization_id,
        )
    )
    if decision is None:
        raise HTTPException(status_code=404, detail="Physician decision not found")
    return PhysicianDecisionResponse(
        id=decision.id,
        assessment_id=decision.assessment_id,
        organization_id=decision.organization_id,
        physician_id=decision.physician_id,
        pharmacist_review_id=decision.pharmacist_review_id,
        decision=decision.decision,
        decision_rationale=decision.decision_rationale,
        assessment_version=decision.assessment_version,
        finalized=decision.finalized,
        finalized_at=decision.finalized_at,
        created_at=decision.created_at,
        updated_at=decision.updated_at,
        medications=[
            FinalMedicationResponse(
                id=item.id,
                medication_id=item.medication_id,
                medication_order_id=item.medication_order_id,
                dose=item.dose,
                dose_unit=item.dose_unit,
                route=item.route,
                frequency=item.frequency,
                duration_value=item.duration_value,
                duration_unit=item.duration_unit,
                indication=item.indication,
                start_date=item.start_date,
                end_date=item.end_date,
            )
            for item in decision.medications
        ],
    )


__all__ = ["router"]
