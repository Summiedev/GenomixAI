from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    OrganizationMembership,
    Patient,
    PatientLinkStatus,
    PatientOrganizationLink,
    PatientStatus,
)


async def require_accessible_patient(
    db: AsyncSession, patient_id: UUID, membership: OrganizationMembership
) -> Patient:
    """Return an active patient linked to the caller's organization, or hide it."""

    patient = await db.scalar(
        select(Patient)
        .join(PatientOrganizationLink)
        .where(
            Patient.id == patient_id,
            Patient.status == PatientStatus.ACTIVE,
            PatientOrganizationLink.patient_id == Patient.id,
            PatientOrganizationLink.organization_id == membership.organization_id,
            PatientOrganizationLink.status == PatientLinkStatus.ACTIVE,
        )
    )
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


__all__ = ["require_accessible_patient"]
