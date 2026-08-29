from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func, nullslast, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.patient_access import require_accessible_patient
from app.core.authorization import require_organization_membership
from app.db.session import get_db
from app.models import (
    AdverseDrugReaction,
    Allergy,
    ClinicalNote,
    Condition,
    Encounter,
    EncounterType,
    LabResult,
    OrganizationMembership,
    RecordStatus,
    Vital,
    VitalType,
)
from app.models.timeline import ClinicalEvent, ClinicalEventType

router = APIRouter(prefix="/patients", tags=["clinical records"])


class PageResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


class ClinicalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    organization_id: UUID
    created_by: UUID | None
    source: str
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


class EncounterCreate(BaseModel):
    encounter_type: EncounterType
    started_at: datetime
    ended_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=500)
    source: str = Field(default="MANUAL", min_length=1, max_length=50)
    status: RecordStatus = RecordStatus.ACTIVE

    @model_validator(mode="after")
    def validate_time_range(self) -> "EncounterCreate":
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at must not be before started_at")
        return self


class EncounterRead(ClinicalRead):
    encounter_type: EncounterType
    started_at: datetime
    ended_at: datetime | None
    reason: str | None


class ConditionCreate(BaseModel):
    encounter_id: UUID | None = None
    code: str | None = Field(default=None, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    onset_date: date | None = None
    source: str = Field(default="MANUAL", min_length=1, max_length=50)
    status: RecordStatus = RecordStatus.ACTIVE


class ConditionRead(ClinicalRead):
    encounter_id: UUID | None
    code: str | None
    name: str
    onset_date: date | None


class ClinicalNoteCreate(BaseModel):
    encounter_id: UUID | None = None
    note_type: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    noted_at: datetime
    source: str = Field(default="MANUAL", min_length=1, max_length=50)
    status: RecordStatus = RecordStatus.ACTIVE


class ClinicalNoteRead(ClinicalRead):
    encounter_id: UUID | None
    note_type: str
    content: str
    noted_at: datetime


class VitalCreate(BaseModel):
    encounter_id: UUID | None = None
    vital_type: VitalType
    value: Decimal
    unit: str = Field(min_length=1, max_length=30)
    measured_at: datetime
    source: str = Field(default="MANUAL", min_length=1, max_length=50)
    status: RecordStatus = RecordStatus.ACTIVE

    @model_validator(mode="after")
    def validate_measurement(self) -> "VitalCreate":
        if not self.value.is_finite():
            raise ValueError("value must be finite")
        if self.value < 0:
            raise ValueError("value must not be negative")
        if self.vital_type is VitalType.OXYGEN_SATURATION and self.value > 100:
            raise ValueError("oxygen saturation must be between 0 and 100")
        return self


class VitalRead(ClinicalRead):
    encounter_id: UUID | None
    vital_type: VitalType
    value: Decimal
    unit: str
    measured_at: datetime


class LabResultCreate(BaseModel):
    encounter_id: UUID | None = None
    test_name: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=200)
    numeric_value: Decimal | None = None
    unit: str | None = Field(default=None, max_length=30)
    reference_range: str | None = Field(default=None, max_length=100)
    collected_at: datetime
    source: str = Field(default="MANUAL", min_length=1, max_length=50)
    status: RecordStatus = RecordStatus.ACTIVE

    @field_validator("numeric_value")
    @classmethod
    def validate_numeric_value(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and not value.is_finite():
            raise ValueError("numeric_value must be finite")
        return value


class LabResultRead(ClinicalRead):
    encounter_id: UUID | None
    test_name: str
    value: str
    numeric_value: Decimal | None
    unit: str | None
    reference_range: str | None
    collected_at: datetime


class AllergyCreate(BaseModel):
    encounter_id: UUID | None = None
    allergen: str = Field(min_length=1, max_length=200)
    reaction: str | None = Field(default=None, max_length=500)
    severity: str | None = Field(default=None, max_length=30)
    source: str = Field(default="MANUAL", min_length=1, max_length=50)
    status: RecordStatus = RecordStatus.ACTIVE


class AllergyRead(ClinicalRead):
    encounter_id: UUID | None
    allergen: str
    reaction: str | None
    severity: str | None


class AdverseDrugReactionCreate(BaseModel):
    encounter_id: UUID | None = None
    medication: str = Field(min_length=1, max_length=200)
    reaction: str = Field(min_length=1, max_length=500)
    severity: str | None = Field(default=None, max_length=30)
    occurred_at: datetime
    source: str = Field(default="MANUAL", min_length=1, max_length=50)
    status: RecordStatus = RecordStatus.ACTIVE


class AdverseDrugReactionRead(ClinicalRead):
    encounter_id: UUID | None
    medication: str
    reaction: str
    severity: str | None
    occurred_at: datetime


@router.post(
    "/{patient_id}/encounters", response_model=EncounterRead, status_code=status.HTTP_201_CREATED
)
async def create_encounter(
    patient_id: UUID,
    body: EncounterCreate,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Encounter:
    await require_accessible_patient(db, patient_id, membership)
    record = Encounter(
        patient_id=patient_id,
        organization_id=membership.organization_id,
        created_by=membership.user_id,
        **body.model_dump(),
    )
    db.add(record)
    await db.flush()
    await _add_event(
        db,
        record,
        membership,
        ClinicalEventType.ENCOUNTER,
        body.started_at,
        body.reason or body.encounter_type.value,
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{patient_id}/encounters", response_model=PageResponse)
async def list_encounters(
    patient_id: UUID,
    organization_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    return await _list_records(
        db, patient_id, membership, Encounter, Encounter.started_at, EncounterRead, page, page_size
    )


@router.post(
    "/{patient_id}/conditions", response_model=ConditionRead, status_code=status.HTTP_201_CREATED
)
async def create_condition(
    patient_id: UUID,
    body: ConditionCreate,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Condition:
    await _validate_patient_and_encounter(db, patient_id, membership, body.encounter_id)
    record = Condition(
        patient_id=patient_id,
        organization_id=membership.organization_id,
        created_by=membership.user_id,
        **body.model_dump(),
    )
    db.add(record)
    await db.flush()
    await _add_event(
        db,
        record,
        membership,
        ClinicalEventType.DIAGNOSIS,
        (
            datetime.combine(body.onset_date, datetime.min.time(), tzinfo=UTC)
            if body.onset_date is not None
            else None
        ),
        body.name,
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{patient_id}/conditions", response_model=PageResponse)
async def list_conditions(
    patient_id: UUID,
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _list_records(
        db, patient_id, membership, Condition, Condition.onset_date, ConditionRead, page, page_size
    )


@router.post(
    "/{patient_id}/notes", response_model=ClinicalNoteRead, status_code=status.HTTP_201_CREATED
)
async def create_note(
    patient_id: UUID,
    body: ClinicalNoteCreate,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> ClinicalNote:
    await _validate_patient_and_encounter(db, patient_id, membership, body.encounter_id)
    record = ClinicalNote(
        patient_id=patient_id,
        organization_id=membership.organization_id,
        created_by=membership.user_id,
        **body.model_dump(),
    )
    db.add(record)
    await db.flush()
    await _add_event(
        db, record, membership, ClinicalEventType.CLINICAL_NOTE, body.noted_at, body.note_type
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{patient_id}/notes", response_model=PageResponse)
async def list_notes(
    patient_id: UUID,
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _list_records(
        db,
        patient_id,
        membership,
        ClinicalNote,
        ClinicalNote.noted_at,
        ClinicalNoteRead,
        page,
        page_size,
    )


@router.post("/{patient_id}/vitals", response_model=VitalRead, status_code=status.HTTP_201_CREATED)
async def create_vital(
    patient_id: UUID,
    body: VitalCreate,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> Vital:
    await _validate_patient_and_encounter(db, patient_id, membership, body.encounter_id)
    record = Vital(
        patient_id=patient_id,
        organization_id=membership.organization_id,
        created_by=membership.user_id,
        **body.model_dump(),
    )
    db.add(record)
    await db.flush()
    await _add_event(
        db,
        record,
        membership,
        ClinicalEventType.VITAL,
        body.measured_at,
        f"{body.vital_type.value}: {body.value} {body.unit}",
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{patient_id}/vitals", response_model=PageResponse)
async def list_vitals(
    patient_id: UUID,
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _list_records(
        db, patient_id, membership, Vital, Vital.measured_at, VitalRead, page, page_size
    )


@router.post(
    "/{patient_id}/labs", response_model=LabResultRead, status_code=status.HTTP_201_CREATED
)
async def create_lab(
    patient_id: UUID,
    body: LabResultCreate,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> LabResult:
    await _validate_patient_and_encounter(db, patient_id, membership, body.encounter_id)
    record = LabResult(
        patient_id=patient_id,
        organization_id=membership.organization_id,
        created_by=membership.user_id,
        **body.model_dump(),
    )
    db.add(record)
    await db.flush()
    await _add_event(
        db,
        record,
        membership,
        ClinicalEventType.LAB_RESULT,
        body.collected_at,
        f"{body.test_name}: {body.value}",
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{patient_id}/labs", response_model=PageResponse)
async def list_labs(
    patient_id: UUID,
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _list_records(
        db,
        patient_id,
        membership,
        LabResult,
        LabResult.collected_at,
        LabResultRead,
        page,
        page_size,
    )


@router.post(
    "/{patient_id}/allergies", response_model=AllergyRead, status_code=status.HTTP_201_CREATED
)
async def create_allergy(
    patient_id: UUID,
    body: AllergyCreate,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> Allergy:
    await _validate_patient_and_encounter(db, patient_id, membership, body.encounter_id)
    record = Allergy(
        patient_id=patient_id,
        organization_id=membership.organization_id,
        created_by=membership.user_id,
        **body.model_dump(),
    )
    db.add(record)
    await db.flush()
    await _add_event(
        db,
        record,
        membership,
        ClinicalEventType.ALLERGY_RECORDED,
        datetime.now(UTC),
        body.allergen,
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{patient_id}/allergies", response_model=PageResponse)
async def list_allergies(
    patient_id: UUID,
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _list_records(
        db, patient_id, membership, Allergy, Allergy.created_at, AllergyRead, page, page_size
    )


@router.post(
    "/{patient_id}/adverse-reactions",
    response_model=AdverseDrugReactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_adverse_reaction(
    patient_id: UUID,
    body: AdverseDrugReactionCreate,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> AdverseDrugReaction:
    await _validate_patient_and_encounter(db, patient_id, membership, body.encounter_id)
    record = AdverseDrugReaction(
        patient_id=patient_id,
        organization_id=membership.organization_id,
        created_by=membership.user_id,
        **body.model_dump(),
    )
    db.add(record)
    await db.flush()
    await _add_event(
        db, record, membership, ClinicalEventType.ADVERSE_REACTION, body.occurred_at, body.reaction
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{patient_id}/adverse-reactions", response_model=PageResponse)
async def list_adverse_reactions(
    patient_id: UUID,
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _list_records(
        db,
        patient_id,
        membership,
        AdverseDrugReaction,
        AdverseDrugReaction.occurred_at,
        AdverseDrugReactionRead,
        page,
        page_size,
    )


async def _validate_patient_and_encounter(
    db: AsyncSession,
    patient_id: UUID,
    membership: OrganizationMembership,
    encounter_id: UUID | None,
) -> None:
    await require_accessible_patient(db, patient_id, membership)
    if encounter_id is not None:
        encounter = await db.scalar(
            select(Encounter).where(
                Encounter.id == encounter_id,
                Encounter.patient_id == patient_id,
                Encounter.organization_id == membership.organization_id,
            )
        )
        if encounter is None:
            raise HTTPException(
                status_code=422, detail="Encounter does not belong to this patient and organization"
            )


async def _list_records(
    db: AsyncSession,
    patient_id: UUID,
    membership: OrganizationMembership,
    model: Any,
    timestamp_column: Any,
    read_model: type[BaseModel],
    page: int,
    page_size: int,
) -> dict[str, Any]:
    await require_accessible_patient(db, patient_id, membership)
    filters = (model.patient_id == patient_id, model.organization_id == membership.organization_id)
    total = await db.scalar(select(func.count(model.id)).where(*filters))
    records = (
        await db.scalars(
            select(model)
            .where(*filters)
            .order_by(nullslast(timestamp_column.desc()), model.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "items": [read_model.model_validate(record) for record in records],
        "total": int(total or 0),
        "page": page,
        "page_size": page_size,
    }


async def _add_event(
    db: AsyncSession,
    record: Any,
    membership: OrganizationMembership,
    event_type: ClinicalEventType,
    event_timestamp: datetime | None,
    summary: str,
) -> None:
    timestamp = event_timestamp or datetime.now(UTC)
    resource_type = type(record).__name__
    db.add(
        ClinicalEvent(
            patient_id=record.patient_id,
            organization_id=record.organization_id,
            event_type=event_type,
            event_timestamp=timestamp,
            actor_id=membership.user_id,
            department_id=membership.department_id,
            linked_resource_type=resource_type,
            linked_resource_id=record.id,
            dedupe_key=f"{resource_type}:{record.id}",
            summary=summary,
            source=record.source,
        )
    )


__all__ = ["router"]
