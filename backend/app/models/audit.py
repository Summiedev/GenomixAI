from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDPKMixin

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.organization import Organization


class AuditAction(StrEnum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PATIENT_VIEWED = "PATIENT_VIEWED"
    PATIENT_SEARCHED = "PATIENT_SEARCHED"
    ASSESSMENT_CREATED = "ASSESSMENT_CREATED"
    ASSESSMENT_ANALYZED = "ASSESSMENT_ANALYZED"
    ASSESSMENT_MODIFIED = "ASSESSMENT_MODIFIED"
    PHARMACIST_REVIEW_REQUESTED = "PHARMACIST_REVIEW_REQUESTED"
    PHARMACIST_REVIEW_OPENED = "PHARMACIST_REVIEW_OPENED"
    PHARMACIST_RECOMMENDATION_SUBMITTED = "PHARMACIST_RECOMMENDATION_SUBMITTED"
    PHYSICIAN_REVIEWED_RECOMMENDATION = "PHYSICIAN_REVIEWED_RECOMMENDATION"
    FINAL_DECISION_RECORDED = "FINAL_DECISION_RECORDED"
    REPORT_GENERATED = "REPORT_GENERATED"


class AuditEvent(UUIDPKMixin, Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_event_org_timestamp", "organization_id", "timestamp"),
        Index("ix_audit_event_resource", "resource_type", "resource_id"),
    )

    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, name="audit_action_enum"), nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )

    actor: Mapped["User | None"] = relationship()
    organization: Mapped["Organization | None"] = relationship()


__all__ = ["AuditAction", "AuditEvent"]
