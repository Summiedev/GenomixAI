"""Restricted, organization-scoped audit event access."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_organization_membership
from app.db.session import get_db
from app.models import AuditAction, AuditEvent, OrganizationMembership

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEventResponse(BaseModel):
    id: UUID
    actor_id: UUID | None
    organization_id: UUID | None
    action: AuditAction
    resource_type: str
    resource_id: UUID | None
    timestamp: datetime
    request_id: str | None
    correlation_id: str | None
    metadata: dict


@router.get("/events", response_model=list[AuditEventResponse])
async def list_audit_events(
    organization_id: UUID,
    resource_type: str | None = Query(default=None, max_length=100),
    resource_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[AuditEventResponse]:
    filters = [AuditEvent.organization_id == membership.organization_id]
    if resource_type:
        filters.append(AuditEvent.resource_type == resource_type)
    if resource_id:
        filters.append(AuditEvent.resource_id == resource_id)
    events = (
        await db.scalars(
            select(AuditEvent)
            .where(*filters)
            .order_by(AuditEvent.timestamp.desc(), AuditEvent.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return [_audit_response(event) for event in events]


def _audit_response(event: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        id=event.id,
        actor_id=event.actor_id,
        organization_id=event.organization_id,
        action=event.action,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        timestamp=event.timestamp,
        request_id=event.request_id,
        correlation_id=event.correlation_id,
        metadata=event.metadata_json,
    )


__all__ = ["router"]
