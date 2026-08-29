from datetime import date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.patient_access import require_accessible_patient
from app.core.authorization import require_organization_membership
from app.db.session import get_db
from app.models import (
    GenomicDataSource,
    GenomicProfile,
    GenomicRecordStatus,
    GenomicValidationStatus,
    OrganizationMembership,
    PharmacogenomicInterpretation,
)

router = APIRouter(prefix="/patients", tags=["pharmacogenomics"])


class EvidenceReferenceResponse(BaseModel):
    id: UUID
    citation: str
    title: str | None
    url: str | None
    source: GenomicDataSource
    source_version: str | None


class GenomicVariantResponse(BaseModel):
    id: UUID
    profile_id: UUID
    gene: str
    variant: str
    allele: str | None
    genotype: str | None
    phenotype: str | None
    raw_result: dict | None
    source: GenomicDataSource
    source_version: str | None
    status: GenomicRecordStatus


class PharmacogenomicInterpretationResponse(BaseModel):
    id: UUID
    profile_id: UUID
    variant_id: UUID | None
    gene: str
    interpretation: str
    clinical_significance: str | None
    evidence_level: str | None
    interpretation_date: date
    source: GenomicDataSource
    source_version: str | None
    status: GenomicRecordStatus
    evidence_references: list[EvidenceReferenceResponse]


class GenomicProfileResponse(BaseModel):
    id: UUID
    patient_id: UUID
    organization_id: UUID
    test_date: date
    source: GenomicDataSource
    source_version: str | None
    validation_status: GenomicValidationStatus
    status: GenomicRecordStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime
    variants: list[GenomicVariantResponse]
    interpretations: list[PharmacogenomicInterpretationResponse]


class GenomicProfilePage(BaseModel):
    items: list[GenomicProfileResponse]
    total: int
    page: int
    page_size: int


@router.get("/{patient_id}/genomics", response_model=GenomicProfilePage)
async def list_genomic_profiles(
    patient_id: UUID,
    organization_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> GenomicProfilePage:
    await require_accessible_patient(db, patient_id, membership)
    filters = _profile_filters(patient_id, membership.organization_id)
    total = await db.scalar(select(func.count(GenomicProfile.id)).where(*filters))
    profiles = (
        await db.scalars(
            _profile_query()
            .where(*filters)
            .order_by(GenomicProfile.test_date.desc(), GenomicProfile.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return GenomicProfilePage(
        items=[_profile_response(profile) for profile in profiles],
        total=int(total or 0),
        page=page,
        page_size=page_size,
    )


@router.get("/{patient_id}/genomics/{profile_id}", response_model=GenomicProfileResponse)
async def get_genomic_profile(
    patient_id: UUID,
    profile_id: UUID,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> GenomicProfileResponse:
    await require_accessible_patient(db, patient_id, membership)
    profile = await db.scalar(
        _profile_query().where(
            GenomicProfile.id == profile_id,
            *_profile_filters(patient_id, membership.organization_id),
        )
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Genomic profile not found"
        )
    return _profile_response(profile)


def _profile_query():
    return select(GenomicProfile).options(
        selectinload(GenomicProfile.variants),
        selectinload(GenomicProfile.interpretations).selectinload(
            PharmacogenomicInterpretation.evidence_references
        ),
    )


def _profile_filters(patient_id: UUID, organization_id: UUID) -> tuple[Any, ...]:
    return (
        GenomicProfile.patient_id == patient_id,
        GenomicProfile.organization_id == organization_id,
        GenomicProfile.status == GenomicRecordStatus.ACTIVE,
    )


def _profile_response(profile: GenomicProfile) -> GenomicProfileResponse:
    return GenomicProfileResponse(
        id=profile.id,
        patient_id=profile.patient_id,
        organization_id=profile.organization_id,
        test_date=profile.test_date,
        source=profile.source,
        source_version=profile.source_version,
        validation_status=profile.validation_status,
        status=profile.status,
        notes=profile.notes,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        variants=[
            GenomicVariantResponse.model_validate(variant, from_attributes=True)
            for variant in profile.variants
        ],
        interpretations=[
            PharmacogenomicInterpretationResponse(
                id=interpretation.id,
                profile_id=interpretation.profile_id,
                variant_id=interpretation.variant_id,
                gene=interpretation.gene,
                interpretation=interpretation.interpretation,
                clinical_significance=interpretation.clinical_significance,
                evidence_level=interpretation.evidence_level,
                interpretation_date=interpretation.interpretation_date,
                source=interpretation.source,
                source_version=interpretation.source_version,
                status=interpretation.status,
                evidence_references=[
                    EvidenceReferenceResponse.model_validate(reference, from_attributes=True)
                    for reference in interpretation.evidence_references
                ],
            )
            for interpretation in profile.interpretations
        ],
    )


__all__ = ["GenomicProfilePage", "GenomicProfileResponse", "router"]
