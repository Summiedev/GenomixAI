"""Synchronous PostgreSQL workflow notification helpers."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    MembershipStatus,
    Notification,
    NotificationType,
    OrganizationMembership,
    Role,
    User,
    UserStatus,
)


async def notify_user(
    db: AsyncSession,
    *,
    recipient_user_id: UUID,
    organization_id: UUID,
    notification_type: NotificationType,
    title: str,
    message: str,
    resource_type: str,
    resource_id: UUID,
) -> Notification:
    notification = Notification(
        recipient_user_id=recipient_user_id,
        organization_id=organization_id,
        notification_type=notification_type,
        title=title,
        message=message,
        resource_type=resource_type,
        resource_id=resource_id,
        created_at=datetime.now(UTC),
    )
    db.add(notification)
    return notification


async def notify_active_role(
    db: AsyncSession,
    *,
    organization_id: UUID,
    role: Role,
    notification_type: NotificationType,
    title: str,
    message: str,
    resource_type: str,
    resource_id: UUID,
    exclude_user_id: UUID | None = None,
) -> None:
    recipient_ids = (
        await db.scalars(
            select(OrganizationMembership.user_id)
            .join(OrganizationMembership.user)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.role == role,
                OrganizationMembership.status == MembershipStatus.ACTIVE,
                OrganizationMembership.user_id != exclude_user_id
                if exclude_user_id is not None
                else True,
                User.status == UserStatus.ACTIVE,
            )
        )
    ).all()
    for recipient_id in recipient_ids:
        await notify_user(
            db,
            recipient_user_id=recipient_id,
            organization_id=organization_id,
            notification_type=notification_type,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
        )


__all__ = ["notify_active_role", "notify_user"]
