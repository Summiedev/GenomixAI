from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.patient_access import require_accessible_patient
from app.core.authorization import require_organization_membership
from app.db.session import get_db
from app.models import ClinicalEvent, ClinicalEventType, OrganizationMembership

router = APIRouter(prefix="/patients", tags=["clinical timeline"])


class ActorResponse(BaseModel):
    id: UUID
    full_name: str


class DepartmentResponse(BaseModel):
    id: UUID
    name: str


class TimelineItem(BaseModel):
    id: UUID
    patient_id: UUID
    organization_id: UUID
    event_type: ClinicalEventType
    timestamp: datetime
    actor: ActorResponse | None
    department: DepartmentResponse | None
    linked_resource_type: str
    linked_resource_id: UUID
    summary: str
    source: str


class TimelinePage(BaseModel):
    items: list[TimelineItem]
    total: int
    page: int
    page_size: int


@router.get("/{patient_id}/timeline", response_model=TimelinePage)
async def list_timeline(
    patient_id: UUID,
    organization_id: UUID,
    event_type: ClinicalEventType | None = None,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    from_timestamp: datetime | None = Query(default=None),
    to_timestamp: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> TimelinePage:
    await require_accessible_patient(db, patient_id, membership)
    filters = [
        ClinicalEvent.patient_id == patient_id,
        ClinicalEvent.organization_id == membership.organization_id,
    ]
    if event_type is not None:
        filters.append(ClinicalEvent.event_type == event_type)
    start = (
        datetime.combine(from_date, time.min, tzinfo=UTC)
        if from_date is not None
        else from_timestamp
    )
    end = (
        datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=UTC)
        if to_date is not None
        else to_timestamp
    )
    if start is not None:
        filters.append(ClinicalEvent.event_timestamp >= start)
    if to_date is not None:
        filters.append(ClinicalEvent.event_timestamp < end)
    elif to_timestamp is not None:
        filters.append(ClinicalEvent.event_timestamp <= end)

    total = await db.scalar(select(func.count(ClinicalEvent.id)).where(*filters))
    events = (
        await db.scalars(
            select(ClinicalEvent)
            .options(
                joinedload(ClinicalEvent.actor),
                joinedload(ClinicalEvent.department),
            )
            .where(*filters)
            .order_by(ClinicalEvent.event_timestamp.desc(), ClinicalEvent.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return TimelinePage(
        items=[_timeline_item(event) for event in events],
        total=int(total or 0),
        page=page,
        page_size=page_size,
    )


def _timeline_item(event: ClinicalEvent) -> TimelineItem:
    return TimelineItem(
        id=event.id,
        patient_id=event.patient_id,
        organization_id=event.organization_id,
        event_type=event.event_type,
        timestamp=event.event_timestamp,
        actor=(
            ActorResponse(id=event.actor.id, full_name=event.actor.full_name)
            if event.actor is not None
            else None
        ),
        department=(
            DepartmentResponse(id=event.department.id, name=event.department.name)
            if event.department is not None
            else None
        ),
        linked_resource_type=event.linked_resource_type,
        linked_resource_id=event.linked_resource_id,
        summary=event.summary,
        source=event.source,
    )


__all__ = ["TimelinePage", "TimelineItem", "router"]
