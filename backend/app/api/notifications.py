"""Persistent in-app workflow notifications (not push delivery)."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_organization_membership
from app.db.session import get_db
from app.models import Notification, NotificationType, OrganizationMembership

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    notification_type: NotificationType
    title: str
    message: str
    resource_type: str
    resource_id: UUID
    created_at: datetime
    is_read: bool
    read_at: datetime | None


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    organization_id: UUID,
    unread_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[NotificationResponse]:
    filters = [
        Notification.recipient_user_id == membership.user_id,
        Notification.organization_id == membership.organization_id,
    ]
    if unread_only:
        filters.append(Notification.is_read.is_(False))
    notifications = (
        await db.scalars(
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc(), Notification.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return [_notification_response(notification) for notification in notifications]


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    organization_id: UUID,
    membership: OrganizationMembership = Depends(require_organization_membership),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> NotificationResponse:
    notification = await db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_user_id == membership.user_id,
            Notification.organization_id == membership.organization_id,
        )
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        await db.commit()
    return _notification_response(notification)


def _notification_response(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        organization_id=notification.organization_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        resource_type=notification.resource_type,
        resource_id=notification.resource_id,
        created_at=notification.created_at,
        is_read=notification.is_read,
        read_at=notification.read_at,
    )


__all__ = ["router"]
