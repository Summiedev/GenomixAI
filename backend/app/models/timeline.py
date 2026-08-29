from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.organization import Department, Organization
    from app.models.patient import Patient


class ClinicalEventType(StrEnum):
    ENCOUNTER = "ENCOUNTER"
    DIAGNOSIS = "DIAGNOSIS"
    PROCEDURE = "PROCEDURE"
    LAB_RESULT = "LAB_RESULT"
    VITAL = "VITAL"
    MEDICATION_PRESCRIBED = "MEDICATION_PRESCRIBED"
    MEDICATION_MODIFIED = "MEDICATION_MODIFIED"
    MEDICATION_DISCONTINUED = "MEDICATION_DISCONTINUED"
    ALLERGY_RECORDED = "ALLERGY_RECORDED"
    ADVERSE_REACTION = "ADVERSE_REACTION"
    CLINICAL_NOTE = "CLINICAL_NOTE"
    GENOMIC_RESULT = "GENOMIC_RESULT"
    MEDICATION_ASSESSMENT = "MEDICATION_ASSESSMENT"
    PHARMACIST_REVIEW = "PHARMACIST_REVIEW"
    FINAL_DECISION = "FINAL_DECISION"


class ClinicalEvent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "clinical_events"
    __table_args__ = (
        UniqueConstraint("organization_id", "dedupe_key", name="uq_clinical_event_dedupe"),
        Index(
            "ix_clinical_event_patient_org_time", "patient_id", "organization_id", "event_timestamp"
        ),
    )

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[ClinicalEventType] = mapped_column(
        SQLEnum(ClinicalEventType, name="clinical_event_type_enum"), nullable=False
    )
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    linked_resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    linked_resource_id: Mapped[UUID] = mapped_column(nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(250), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    actor: Mapped["User | None"] = relationship()
    department: Mapped["Department | None"] = relationship()


__all__ = ["ClinicalEvent", "ClinicalEventType"]
