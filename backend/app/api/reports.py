"""Persisted PDF reports for medication assessments."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.assessments import _assessment_response, _load_assessment
from app.api.patient_access import require_accessible_patient
from app.core.audit import append_audit_event
from app.core.authorization import require_organization_membership, require_role
from app.db.session import get_db
from app.models import (
    AssessmentReport,
    AuditAction,
    GenomicDataSource,
    GenomicProfile,
    OrganizationMembership,
    PharmacistReview,
    PhysicianDecision,
    Role,
)
from app.reports.pdf import render_assessment_pdf

router = APIRouter(tags=["assessment reports"])


class AssessmentReportResponse(BaseModel):
    id: UUID
    assessment_id: UUID
    organization_id: UUID
    generated_by: UUID
    generated_at: datetime
    content_type: str
    filename: str
    synthetic_data_marker: bool
    download_path: str


@router.post(
    "/assessments/{assessment_id}/reports",
    response_model=AssessmentReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assessment_report(
    assessment_id: UUID,
    request: Request,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        require_role(Role.PHYSICIAN, Role.HOSPITAL_ADMIN, Role.PLATFORM_ADMIN)
    ),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AssessmentReportResponse:
    assessment = await _load_assessment(db, assessment_id, membership)
    patient = await require_accessible_patient(db, assessment.patient_id, membership)
    decisions = (
        await db.scalars(
            select(PhysicianDecision)
            .options(selectinload(PhysicianDecision.medications))
            .where(
                PhysicianDecision.assessment_id == assessment.id,
                PhysicianDecision.organization_id == membership.organization_id,
            )
            .order_by(PhysicianDecision.created_at)
        )
    ).all()
    profiles = (
        await db.scalars(
            select(GenomicProfile).where(
                GenomicProfile.patient_id == assessment.patient_id,
                GenomicProfile.organization_id == membership.organization_id,
            )
        )
    ).all()
    reviews = (
        await db.scalars(
            select(PharmacistReview)
            .where(
                PharmacistReview.assessment_id == assessment.id,
                PharmacistReview.organization_id == membership.organization_id,
            )
            .order_by(PharmacistReview.created_at)
        )
    ).all()
    synthetic_data = any(
        profile.source in {GenomicDataSource.SYNTHETIC, GenomicDataSource.RESEARCH_DATASET}
        for profile in profiles
    )
    assessment_data = _assessment_response(assessment).model_dump(mode="json")
    report_data = {
        "report_type": "MEDICATION_ASSESSMENT",
        "synthetic_data": synthetic_data,
        "data_quality_note": (
            "Genomic inputs include synthetic or research data and are not clinically validated."
            if synthetic_data
            else ""
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "patient": {
            "id": str(patient.id),
            "genomix_patient_id": patient.genomix_patient_id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth.isoformat(),
        },
        "organization": {
            "id": str(membership.organization.id),
            "name": membership.organization.name,
        },
        "assessment": assessment_data,
        "clinical_factors_considered": {
            "conditions": assessment_data["clinical_factor_findings"],
            "allergies": assessment_data["allergy_findings"],
            "adverse_reactions": assessment_data["adverse_reaction_findings"],
            "labs_and_vitals": assessment_data["clinical_factor_findings"],
        },
        "pharmacist_reviews": [
            {
                "id": str(review.id),
                "status": review.status.value,
                "priority": review.priority.value,
                "physician_message": review.physician_message,
                "pharmacist_recommendation": review.pharmacist_recommendation,
                "pharmacist_rationale": review.pharmacist_rationale,
                "monitoring_recommendations": review.monitoring_recommendations,
                "recommended_changes": review.recommended_changes,
            }
            for review in reviews
        ],
        "final_physician_decisions": [
            {
                "id": str(decision.id),
                "decision": decision.decision.value,
                "decision_rationale": decision.decision_rationale,
                "assessment_version": decision.assessment_version,
                "finalized": decision.finalized,
                "finalized_at": decision.finalized_at.isoformat()
                if decision.finalized_at
                else None,
                "pharmacist_review_id": str(decision.pharmacist_review_id)
                if decision.pharmacist_review_id
                else None,
                "medications": [
                    {
                        "medication_id": str(item.medication_id),
                        "medication_order_id": str(item.medication_order_id)
                        if item.medication_order_id
                        else None,
                        "dose": str(item.dose),
                        "dose_unit": item.dose_unit,
                        "route": item.route,
                        "frequency": item.frequency,
                        "duration_value": str(item.duration_value)
                        if item.duration_value is not None
                        else None,
                        "duration_unit": item.duration_unit,
                        "indication": item.indication,
                        "start_date": item.start_date.isoformat(),
                        "end_date": item.end_date.isoformat() if item.end_date else None,
                    }
                    for item in decision.medications
                ],
            }
            for decision in decisions
        ],
        "engine_version": assessment.engine_version,
        "timestamps": {
            "assessment_created_at": assessment.created_at.isoformat(),
            "assessment_updated_at": assessment.updated_at.isoformat(),
        },
    }
    pdf_content = render_assessment_pdf(report_data)
    generated_at = datetime.now(UTC)
    report = AssessmentReport(
        assessment_id=assessment.id,
        organization_id=membership.organization_id,
        generated_by=membership.user_id,
        generated_at=generated_at,
        filename=f"genomixai-assessment-{assessment.id}.pdf",
        synthetic_data_marker=synthetic_data,
        report_data=report_data,
        pdf_content=pdf_content,
    )
    db.add(report)
    await db.flush()
    append_audit_event(
        db,
        action=AuditAction.REPORT_GENERATED,
        actor_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="AssessmentReport",
        resource_id=report.id,
        request=request,
        metadata={"assessment_id": str(assessment.id), "synthetic_data": synthetic_data},
    )
    await db.commit()
    return _report_response(report)


@router.get("/assessments/{assessment_id}/reports/{report_id}")
async def get_assessment_report(
    assessment_id: UUID,
    report_id: UUID,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Response:
    report = await db.scalar(
        select(AssessmentReport).where(
            AssessmentReport.id == report_id,
            AssessmentReport.assessment_id == assessment_id,
            AssessmentReport.organization_id == membership.organization_id,
        )
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Assessment report not found")
    return Response(
        content=report.pdf_content,
        media_type=report.content_type,
        headers={"Content-Disposition": f'attachment; filename="{report.filename}"'},
    )


def _report_response(report: AssessmentReport) -> AssessmentReportResponse:
    return AssessmentReportResponse(
        id=report.id,
        assessment_id=report.assessment_id,
        organization_id=report.organization_id,
        generated_by=report.generated_by,
        generated_at=report.generated_at,
        content_type=report.content_type,
        filename=report.filename,
        synthetic_data_marker=report.synthetic_data_marker,
        download_path=f"/api/v1/assessments/{report.assessment_id}/reports/{report.id}",
    )


__all__ = ["router"]
