from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import append_audit_event
from app.core.authorization import require_organization_membership
from app.db.session import get_db
from app.models import (
    AuditAction,
    OrganizationMembership,
    Patient,
    PatientLinkStatus,
    PatientOrganizationLink,
    PatientSex,
    PatientStatus,
)

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    genomix_patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    sex: PatientSex
    status: PatientStatus
    organization_id: UUID
    mrn: str
    created_at: datetime
    updated_at: datetime


class PatientPage(BaseModel):
    items: list[PatientResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=PatientPage)
async def list_patients(
    organization_id: UUID,
    request: Request,
    search: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PatientPage:
    filters = _patient_scope(organization_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Patient.first_name.ilike(term),
                Patient.last_name.ilike(term),
                func.concat(Patient.first_name, " ", Patient.last_name).ilike(term),
                PatientOrganizationLink.mrn.ilike(term),
                Patient.genomix_patient_id.ilike(term),
            )
        )

    total = await db.scalar(
        select(func.count(Patient.id))
        .select_from(Patient)
        .join(PatientOrganizationLink)
        .where(*filters)
    )
    rows = (
        await db.execute(
            select(Patient, PatientOrganizationLink)
            .join(PatientOrganizationLink)
            .where(*filters)
            .order_by(Patient.last_name, Patient.first_name, Patient.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    if search and search.strip():
        append_audit_event(
            db,
            action=AuditAction.PATIENT_SEARCHED,
            actor_id=membership.user_id,
            organization_id=membership.organization_id,
            resource_type="PatientSearch",
            request=request,
            metadata={"page": page, "page_size": page_size, "search_provided": True},
        )
        await db.commit()
    return PatientPage(
        items=[_patient_response(patient, link) for patient, link in rows],
        total=int(total or 0),
        page=page,
        page_size=page_size,
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    organization_id: UUID,
    request: Request,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PatientResponse:
    patient_result = await db.execute(
        select(Patient, PatientOrganizationLink)
        .join(PatientOrganizationLink)
        .where(
            Patient.id == patient_id,
            Patient.status == PatientStatus.ACTIVE,
            PatientOrganizationLink.patient_id == Patient.id,
            PatientOrganizationLink.organization_id == membership.organization_id,
            PatientOrganizationLink.status == PatientLinkStatus.ACTIVE,
        )
    )
    patient = patient_result.one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    patient_record, link = patient
    append_audit_event(
        db,
        action=AuditAction.PATIENT_VIEWED,
        actor_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="Patient",
        resource_id=patient_record.id,
        request=request,
    )
    await db.commit()
    return _patient_response(patient_record, link)


def _patient_scope(organization_id: UUID) -> list[object]:
    return [
        Patient.status == PatientStatus.ACTIVE,
        PatientOrganizationLink.patient_id == Patient.id,
        PatientOrganizationLink.organization_id == organization_id,
        PatientOrganizationLink.status == PatientLinkStatus.ACTIVE,
    ]


def _patient_response(patient: Patient, link: PatientOrganizationLink) -> PatientResponse:
    return PatientResponse(
        id=patient.id,
        genomix_patient_id=patient.genomix_patient_id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=patient.date_of_birth,
        sex=patient.sex,
        status=patient.status,
        organization_id=link.organization_id,
        mrn=link.mrn,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


__all__ = ["PatientPage", "PatientResponse", "router"]
