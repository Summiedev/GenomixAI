from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDPKMixin

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.organization import Organization


class NotificationType(StrEnum):
    PHARMACIST_REVIEW_REQUESTED = "PHARMACIST_REVIEW_REQUESTED"
    PHARMACIST_ASSIGNED = "PHARMACIST_ASSIGNED"
    PHARMACIST_REVIEW_STARTED = "PHARMACIST_REVIEW_STARTED"
    PHARMACIST_RECOMMENDATION_SUBMITTED = "PHARMACIST_RECOMMENDATION_SUBMITTED"
    ASSESSMENT_RETURNED_TO_PHYSICIAN = "ASSESSMENT_RETURNED_TO_PHYSICIAN"
    FINAL_DECISION_RECORDED = "FINAL_DECISION_RECORDED"


class Notification(UUIDPKMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index(
            "ix_notification_recipient_org_created",
            "recipient_user_id",
            "organization_id",
            "created_at",
        ),
    )

    recipient_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, name="notification_type_enum"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    recipient: Mapped["User"] = relationship()
    organization: Mapped["Organization"] = relationship()


__all__ = ["Notification", "NotificationType"]
