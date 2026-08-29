from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.patient_access import require_accessible_patient
from app.core.authorization import require_authenticated_user, require_organization_membership
from app.db.session import get_db
from app.models import (
    DurationUnit,
    Encounter,
    Medication,
    MedicationOrder,
    MedicationOrderStatus,
    MedicationOrderStatusHistory,
    MedicationStatus,
    OrganizationMembership,
    User,
)
from app.models.timeline import ClinicalEvent, ClinicalEventType

router = APIRouter(tags=["medications"])


class MedicationCreate(BaseModel):
    standardized_code: str | None = Field(default=None, max_length=100)
    generic_name: str = Field(min_length=1, max_length=200)
    brand_name: str | None = Field(default=None, max_length=200)
    strength: str | None = Field(default=None, max_length=100)
    dosage_form: str | None = Field(default=None, max_length=100)
    status: MedicationStatus = MedicationStatus.ACTIVE


class MedicationRead(MedicationCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


class MedicationOrderCreate(BaseModel):
    medication_id: UUID
    encounter_id: UUID | None = None
    dose: Decimal
    dose_unit: str = Field(min_length=1, max_length=30)
    route: str = Field(min_length=1, max_length=50)
    frequency: str = Field(min_length=1, max_length=100)
    duration_value: Decimal | None = None
    duration_unit: DurationUnit | None = None
    indication: str | None = Field(default=None, max_length=500)
    start_date: date
    end_date: date | None = None
    status: MedicationOrderStatus = MedicationOrderStatus.PROPOSED
    source: str = Field(default="MANUAL", min_length=1, max_length=50)

    @field_validator("dose", "duration_value")
    @classmethod
    def validate_positive_numbers(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and (not value.is_finite() or value <= 0):
            raise ValueError("dose and duration values must be finite and greater than zero")
        return value

    @model_validator(mode="after")
    def validate_duration_and_dates(self) -> "MedicationOrderCreate":
        if (self.duration_value is None) != (self.duration_unit is None):
            raise ValueError("duration_value and duration_unit must be supplied together")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class MedicationOrderRead(BaseModel):
    id: UUID
    patient_id: UUID
    organization_id: UUID
    encounter_id: UUID | None
    medication: MedicationRead
    dose: Decimal
    dose_unit: str
    route: str
    frequency: str
    duration_value: Decimal | None
    duration_unit: DurationUnit | None
    indication: str | None
    start_date: date
    end_date: date | None
    prescriber_id: UUID | None
    status: MedicationOrderStatus
    source: str
    created_at: datetime
    updated_at: datetime
    status_history: list["MedicationOrderStatusHistoryRead"]


class MedicationOrderStatusHistoryRead(BaseModel):
    id: UUID
    from_status: MedicationOrderStatus | None
    to_status: MedicationOrderStatus
    changed_by: UUID | None
    changed_at: datetime
    reason: str | None


class MedicationOrderPage(BaseModel):
    items: list[MedicationOrderRead]
    total: int
    page: int
    page_size: int


class MedicationStatusUpdate(BaseModel):
    status: MedicationOrderStatus
    reason: str | None = Field(default=None, max_length=500)


@router.post("/medications", response_model=MedicationRead, status_code=status.HTTP_201_CREATED)
async def create_medication(
    body: MedicationCreate,
    user: User = Depends(require_authenticated_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Medication:
    del user
    medication = Medication(**body.model_dump())
    db.add(medication)
    await db.commit()
    await db.refresh(medication)
    return medication


@router.get("/medications", response_model=list[MedicationRead])
async def list_medications(
    search: str | None = Query(default=None, max_length=200),
    user: User = Depends(require_authenticated_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[Medication]:
    del user
    query = select(Medication).where(Medication.status == MedicationStatus.ACTIVE)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            Medication.generic_name.ilike(term)
            | Medication.brand_name.ilike(term)
            | Medication.standardized_code.ilike(term)
        )
    return list((await db.scalars(query.order_by(Medication.generic_name))).all())


@router.post(
    "/patients/{patient_id}/medication-orders",
    response_model=MedicationOrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_medication_order(
    patient_id: UUID,
    body: MedicationOrderCreate,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MedicationOrder:
    await require_accessible_patient(db, patient_id, membership)
    medication = await db.scalar(
        select(Medication).where(
            Medication.id == body.medication_id,
            Medication.status == MedicationStatus.ACTIVE,
        )
    )
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Active medication not found"
        )
    if body.encounter_id is not None:
        encounter = await db.scalar(
            select(Encounter).where(
                Encounter.id == body.encounter_id,
                Encounter.patient_id == patient_id,
                Encounter.organization_id == membership.organization_id,
            )
        )
        if encounter is None:
            raise HTTPException(
                status_code=422, detail="Encounter does not belong to this patient and organization"
            )

    order = MedicationOrder(
        patient_id=patient_id,
        organization_id=membership.organization_id,
        prescriber_id=membership.user_id,
        medication=medication,
        **body.model_dump(),
    )
    db.add(order)
    await db.flush()
    history = MedicationOrderStatusHistory(
        order=order,
        from_status=None,
        to_status=order.status,
        changed_by=membership.user_id,
        changed_at=datetime.now(UTC),
        reason="Initial order status",
    )
    db.add(history)
    await db.flush()
    await _add_medication_event(
        db,
        order,
        membership,
        ClinicalEventType.MEDICATION_PRESCRIBED,
        history.id,
        f"{medication.generic_name} order: {order.status.value}",
    )
    await db.commit()
    await db.refresh(order)
    return _order_response(order, [history])


@router.get("/patients/{patient_id}/medication-orders", response_model=MedicationOrderPage)
async def list_medication_orders(
    patient_id: UUID,
    organization_id: UUID,
    order_status: MedicationOrderStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MedicationOrderPage:
    await require_accessible_patient(db, patient_id, membership)
    filters = [
        MedicationOrder.patient_id == patient_id,
        MedicationOrder.organization_id == membership.organization_id,
    ]
    if order_status is not None:
        filters.append(MedicationOrder.status == order_status)
    total = await db.scalar(select(func.count(MedicationOrder.id)).where(*filters))
    orders = (
        await db.scalars(
            select(MedicationOrder)
            .options(
                joinedload(MedicationOrder.medication),
                selectinload(MedicationOrder.status_history),
            )
            .where(*filters)
            .order_by(MedicationOrder.start_date.desc(), MedicationOrder.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return MedicationOrderPage(
        items=[_order_response(order) for order in orders],
        total=int(total or 0),
        page=page,
        page_size=page_size,
    )


@router.get("/patients/{patient_id}/medications", response_model=MedicationOrderPage)
async def list_patient_medications(
    patient_id: UUID,
    organization_id: UUID,
    order_status: MedicationOrderStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MedicationOrderPage:
    return await list_medication_orders(
        patient_id, organization_id, order_status, page, page_size, membership, db
    )


@router.patch(
    "/patients/{patient_id}/medication-orders/{order_id}/status",
    response_model=MedicationOrderRead,
)
async def update_medication_order_status(
    patient_id: UUID,
    order_id: UUID,
    body: MedicationStatusUpdate,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MedicationOrder:
    await require_accessible_patient(db, patient_id, membership)
    order = await db.scalar(
        select(MedicationOrder)
        .options(
            joinedload(MedicationOrder.medication), selectinload(MedicationOrder.status_history)
        )
        .where(
            MedicationOrder.id == order_id,
            MedicationOrder.patient_id == patient_id,
            MedicationOrder.organization_id == membership.organization_id,
        )
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Medication order not found")
    if not _valid_transition(order.status, body.status):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid medication status transition: {order.status} -> {body.status}",
        )
    if body.status is order.status:
        return order

    previous = order.status
    order.status = body.status
    history = MedicationOrderStatusHistory(
        order=order,
        from_status=previous,
        to_status=body.status,
        changed_by=membership.user_id,
        changed_at=datetime.now(UTC),
        reason=body.reason,
    )
    order.status_history.append(history)
    db.add(history)
    await db.flush()
    event_type = (
        ClinicalEventType.MEDICATION_DISCONTINUED
        if body.status is MedicationOrderStatus.DISCONTINUED
        else ClinicalEventType.MEDICATION_MODIFIED
    )
    await _add_medication_event(
        db,
        order,
        membership,
        event_type,
        history.id,
        f"{order.medication.generic_name} order changed to {body.status.value}",
    )
    await db.commit()
    await db.refresh(order)
    return order


def _valid_transition(current: MedicationOrderStatus, target: MedicationOrderStatus) -> bool:
    allowed = {
        MedicationOrderStatus.PROPOSED: {
            MedicationOrderStatus.PROPOSED,
            MedicationOrderStatus.ACTIVE,
            MedicationOrderStatus.CANCELLED,
        },
        MedicationOrderStatus.ACTIVE: {
            MedicationOrderStatus.ACTIVE,
            MedicationOrderStatus.COMPLETED,
            MedicationOrderStatus.DISCONTINUED,
        },
        MedicationOrderStatus.COMPLETED: {MedicationOrderStatus.COMPLETED},
        MedicationOrderStatus.DISCONTINUED: {MedicationOrderStatus.DISCONTINUED},
        MedicationOrderStatus.CANCELLED: {MedicationOrderStatus.CANCELLED},
    }
    return target in allowed[current]


def _order_response(
    order: MedicationOrder,
    history_entries: list[MedicationOrderStatusHistory] | None = None,
) -> MedicationOrderRead:
    return MedicationOrderRead(
        id=order.id,
        patient_id=order.patient_id,
        organization_id=order.organization_id,
        encounter_id=order.encounter_id,
        medication=MedicationRead.model_validate(order.medication, from_attributes=True),
        dose=order.dose,
        dose_unit=order.dose_unit,
        route=order.route,
        frequency=order.frequency,
        duration_value=order.duration_value,
        duration_unit=order.duration_unit,
        indication=order.indication,
        start_date=order.start_date,
        end_date=order.end_date,
        prescriber_id=order.prescriber_id,
        status=order.status,
        source=order.source,
        created_at=order.created_at,
        updated_at=order.updated_at,
        status_history=[
            MedicationOrderStatusHistoryRead.model_validate(history, from_attributes=True)
            for history in (
                history_entries if history_entries is not None else order.status_history
            )
        ],
    )


async def _add_medication_event(
    db: AsyncSession,
    order: MedicationOrder,
    membership: OrganizationMembership,
    event_type: ClinicalEventType,
    history_id: UUID,
    summary: str,
) -> None:
    db.add(
        ClinicalEvent(
            patient_id=order.patient_id,
            organization_id=order.organization_id,
            event_type=event_type,
            event_timestamp=datetime.combine(order.start_date, datetime.min.time(), tzinfo=UTC),
            actor_id=membership.user_id,
            department_id=membership.department_id,
            linked_resource_type="MedicationOrder",
            linked_resource_id=order.id,
            dedupe_key=f"MedicationOrder:{order.id}:{history_id}",
            summary=summary,
            source=order.source,
        )
    )


__all__ = ["router"]
