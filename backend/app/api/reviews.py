"""Physician-to-pharmacist medication assessment review workflow."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.assessments import _load_assessment
from app.api.patient_access import require_accessible_patient
from app.clinical_engine.state_machine import (
    AssessmentState,
    AssessmentStateMachine,
    AssessmentTransitionError,
)
from app.core.audit import append_audit_event
from app.core.authorization import require_role
from app.core.notifications import notify_active_role, notify_user
from app.db.session import get_db
from app.models import (
    AuditAction,
    MedicationAssessment,
    NotificationType,
    OrganizationMembership,
    PharmacistReview,
    PharmacistReviewStatus,
    ReviewPriority,
    Role,
)

router = APIRouter(tags=["pharmacist reviews"])


class PharmacistReviewRequest(BaseModel):
    priority: ReviewPriority = ReviewPriority.NORMAL
    physician_message: str | None = Field(default=None, max_length=5000)


class PharmacistReviewSubmit(BaseModel):
    pharmacist_recommendation: str = Field(min_length=1, max_length=10000)
    pharmacist_rationale: str = Field(min_length=1, max_length=10000)
    monitoring_recommendations: list[str] = Field(default_factory=list, max_length=50)
    recommended_changes: list[dict] = Field(default_factory=list, max_length=50)


class PharmacistReviewReturn(BaseModel):
    message: str | None = Field(default=None, max_length=5000)


class PharmacistReviewResponse(BaseModel):
    id: UUID
    assessment_id: UUID
    organization_id: UUID
    requested_by: UUID
    assigned_pharmacist_id: UUID | None
    priority: ReviewPriority
    status: PharmacistReviewStatus
    physician_message: str | None
    pharmacist_recommendation: str | None
    pharmacist_rationale: str | None
    monitoring_recommendations: list[str]
    recommended_changes: list[dict]
    assigned_at: datetime | None
    started_at: datetime | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime


@router.post(
    "/assessments/{assessment_id}/request-pharmacist-review",
    response_model=PharmacistReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_pharmacist_review(
    assessment_id: UUID,
    body: PharmacistReviewRequest,
    request: Request,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        require_role(Role.PHYSICIAN, Role.HOSPITAL_ADMIN, Role.PLATFORM_ADMIN)
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PharmacistReviewResponse:
    assessment = await _load_assessment(db, assessment_id, membership)
    await require_accessible_patient(db, assessment.patient_id, membership)
    if assessment.status is not AssessmentState.ANALYZED:
        raise HTTPException(
            status_code=409, detail="Only analyzed assessments can be sent for review"
        )
    existing = await db.scalar(
        select(PharmacistReview).where(
            PharmacistReview.assessment_id == assessment.id,
            PharmacistReview.status.in_(
                [
                    PharmacistReviewStatus.REQUESTED,
                    PharmacistReviewStatus.IN_PROGRESS,
                    PharmacistReviewStatus.SUBMITTED,
                ]
            ),
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="An active pharmacist review already exists")
    _transition_assessment(assessment, AssessmentState.PENDING_PHARMACIST_REVIEW, membership)
    review = PharmacistReview(
        assessment_id=assessment.id,
        organization_id=membership.organization_id,
        requested_by=membership.user_id,
        priority=body.priority,
        status=PharmacistReviewStatus.REQUESTED,
        physician_message=body.physician_message,
    )
    db.add(review)
    await db.flush()
    await notify_active_role(
        db,
        organization_id=membership.organization_id,
        role=Role.CLINICAL_PHARMACIST,
        notification_type=NotificationType.PHARMACIST_REVIEW_REQUESTED,
        title="New pharmacist review requested",
        message="A physician has requested your review of a medication assessment.",
        resource_type="PharmacistReview",
        resource_id=review.id,
    )
    append_audit_event(
        db,
        action=AuditAction.PHARMACIST_REVIEW_REQUESTED,
        actor_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="PharmacistReview",
        resource_id=review.id,
        request=request,
    )
    await db.commit()
    await db.refresh(review)
    return review


@router.get("/pharmacist/reviews", response_model=list[PharmacistReviewResponse])
async def list_pharmacist_reviews(
    organization_id: UUID,
    review_status: PharmacistReviewStatus | None = Query(default=None, alias="status"),
    membership: OrganizationMembership = Depends(
        require_role(Role.CLINICAL_PHARMACIST, Role.HOSPITAL_ADMIN, Role.PLATFORM_ADMIN)
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[PharmacistReview]:
    filters = [PharmacistReview.organization_id == membership.organization_id]
    if review_status is not None:
        filters.append(PharmacistReview.status == review_status)
    else:
        filters.append(
            PharmacistReview.status.in_(
                [PharmacistReviewStatus.REQUESTED, PharmacistReviewStatus.IN_PROGRESS]
            )
        )
    return list(
        (
            await db.scalars(
                select(PharmacistReview)
                .options(joinedload(PharmacistReview.assessment))
                .where(*filters)
                .order_by(PharmacistReview.priority.desc(), PharmacistReview.created_at)
            )
        ).all()
    )


@router.get("/pharmacist/reviews/{review_id}", response_model=PharmacistReviewResponse)
async def get_pharmacist_review(
    review_id: UUID,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        require_role(
            Role.PHYSICIAN,
            Role.CLINICAL_PHARMACIST,
            Role.HOSPITAL_ADMIN,
            Role.PLATFORM_ADMIN,
        )
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PharmacistReviewResponse:
    return await _load_review(db, review_id, membership)


@router.post("/pharmacist/reviews/{review_id}/start", response_model=PharmacistReviewResponse)
async def start_pharmacist_review(
    review_id: UUID,
    request: Request,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        require_role(Role.CLINICAL_PHARMACIST, Role.HOSPITAL_ADMIN, Role.PLATFORM_ADMIN)
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PharmacistReviewResponse:
    review = await _load_review(db, review_id, membership)
    if review.status is not PharmacistReviewStatus.REQUESTED:
        raise HTTPException(status_code=409, detail="Only requested reviews can be started")
    if review.assigned_pharmacist_id not in (None, membership.user_id):
        raise HTTPException(status_code=403, detail="Review is assigned to another pharmacist")
    assessment = await _load_assessment(db, review.assessment_id, membership)
    _transition_assessment(assessment, AssessmentState.IN_PHARMACIST_REVIEW, membership)
    now = datetime.now(UTC)
    review.assigned_pharmacist_id = membership.user_id
    review.assigned_at = review.assigned_at or now
    review.started_at = now
    review.status = PharmacistReviewStatus.IN_PROGRESS
    await notify_user(
        db,
        recipient_user_id=membership.user_id,
        organization_id=membership.organization_id,
        notification_type=NotificationType.PHARMACIST_ASSIGNED,
        title="Pharmacist review assigned",
        message="You are now assigned to this medication assessment review.",
        resource_type="PharmacistReview",
        resource_id=review.id,
    )
    await notify_user(
        db,
        recipient_user_id=review.requested_by,
        organization_id=membership.organization_id,
        notification_type=NotificationType.PHARMACIST_REVIEW_STARTED,
        title="Pharmacist started review",
        message="The assigned pharmacist has started reviewing your medication assessment.",
        resource_type="PharmacistReview",
        resource_id=review.id,
    )
    append_audit_event(
        db,
        action=AuditAction.PHARMACIST_REVIEW_OPENED,
        actor_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="PharmacistReview",
        resource_id=review.id,
        request=request,
    )
    await db.commit()
    return await _load_review(db, review_id, membership)


@router.post("/pharmacist/reviews/{review_id}/submit", response_model=PharmacistReviewResponse)
async def submit_pharmacist_review(
    review_id: UUID,
    body: PharmacistReviewSubmit,
    request: Request,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        require_role(Role.CLINICAL_PHARMACIST, Role.HOSPITAL_ADMIN, Role.PLATFORM_ADMIN)
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PharmacistReviewResponse:
    review = await _load_review(db, review_id, membership)
    _ensure_assigned(review, membership)
    if review.status is not PharmacistReviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="Only in-progress reviews can be submitted")
    assessment = await _load_assessment(db, review.assessment_id, membership)
    _transition_assessment(assessment, AssessmentState.PHARMACIST_RECOMMENDED, membership)
    review.status = PharmacistReviewStatus.SUBMITTED
    review.pharmacist_recommendation = body.pharmacist_recommendation
    review.pharmacist_rationale = body.pharmacist_rationale
    review.monitoring_recommendations = body.monitoring_recommendations
    review.recommended_changes = body.recommended_changes
    review.submitted_at = datetime.now(UTC)
    await notify_user(
        db,
        recipient_user_id=review.requested_by,
        organization_id=membership.organization_id,
        notification_type=NotificationType.PHARMACIST_RECOMMENDATION_SUBMITTED,
        title="Pharmacist recommendation submitted",
        message="A pharmacist recommendation is available for physician review.",
        resource_type="PharmacistReview",
        resource_id=review.id,
    )
    append_audit_event(
        db,
        action=AuditAction.PHARMACIST_RECOMMENDATION_SUBMITTED,
        actor_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="PharmacistReview",
        resource_id=review.id,
        request=request,
    )
    await db.commit()
    return await _load_review(db, review_id, membership)


@router.post("/pharmacist/reviews/{review_id}/return", response_model=PharmacistReviewResponse)
async def return_pharmacist_review(
    review_id: UUID,
    body: PharmacistReviewReturn,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        require_role(Role.CLINICAL_PHARMACIST, Role.HOSPITAL_ADMIN, Role.PLATFORM_ADMIN)
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PharmacistReviewResponse:
    review = await _load_review(db, review_id, membership)
    _ensure_assigned(review, membership)
    if review.status is not PharmacistReviewStatus.SUBMITTED:
        raise HTTPException(status_code=409, detail="Only submitted reviews can be returned")
    assessment = await _load_assessment(db, review.assessment_id, membership)
    _transition_assessment(assessment, AssessmentState.RETURNED_TO_PHYSICIAN, membership)
    review.status = PharmacistReviewStatus.RETURNED
    if body.message:
        review.pharmacist_rationale = (
            f"{review.pharmacist_rationale or ''}\nReturn message: {body.message}".strip()
        )
    await notify_user(
        db,
        recipient_user_id=review.requested_by,
        organization_id=membership.organization_id,
        notification_type=NotificationType.ASSESSMENT_RETURNED_TO_PHYSICIAN,
        title="Assessment returned to physician",
        message="The pharmacist review has been returned for physician action.",
        resource_type="MedicationAssessment",
        resource_id=review.assessment_id,
    )
    await db.commit()
    return await _load_review(db, review_id, membership)


async def _load_review(
    db: AsyncSession, review_id: UUID, membership: OrganizationMembership
) -> PharmacistReview:
    review = await db.scalar(
        select(PharmacistReview).where(
            PharmacistReview.id == review_id,
            PharmacistReview.organization_id == membership.organization_id,
        )
    )
    if review is None:
        raise HTTPException(status_code=404, detail="Pharmacist review not found")
    return review


def _ensure_assigned(review: PharmacistReview, membership: OrganizationMembership) -> None:
    if review.assigned_pharmacist_id != membership.user_id:
        raise HTTPException(status_code=403, detail="Review is not assigned to this pharmacist")


def _transition_assessment(
    assessment: MedicationAssessment,
    target: AssessmentState,
    membership: OrganizationMembership,
) -> None:
    machine = AssessmentStateMachine(assessment.status)
    try:
        machine.transition(target, membership.role)
    except AssessmentTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    assessment.status = machine.state


__all__ = ["router"]
