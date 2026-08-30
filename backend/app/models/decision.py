from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.assessment import MedicationAssessment, PharmacistReview
    from app.models.identity import User
    from app.models.medication import Medication, MedicationOrder
    from app.models.organization import Organization


class PhysicianDecisionType(StrEnum):
    ACCEPT = "ACCEPT"
    MODIFY = "MODIFY"
    DECLINE = "DECLINE"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"


class PhysicianDecision(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "physician_decisions"
    __table_args__ = (
        Index("ix_physician_decision_assessment_created", "assessment_id", "created_at"),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("medication_assessments.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    physician_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    pharmacist_review_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("pharmacist_reviews.id", ondelete="SET NULL"), nullable=True
    )
    decision: Mapped[PhysicianDecisionType] = mapped_column(
        SQLEnum(PhysicianDecisionType, name="physician_decision_type_enum"), nullable=False
    )
    decision_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    assessment_version: Mapped[str] = mapped_column(String(100), nullable=False)
    finalized: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )

    assessment: Mapped["MedicationAssessment"] = relationship()
    organization: Mapped["Organization"] = relationship()
    physician: Mapped["User"] = relationship()
    pharmacist_review: Mapped["PharmacistReview | None"] = relationship()
    medications: Mapped[list["PhysicianDecisionMedication"]] = relationship(
        back_populates="decision",
        cascade="all, delete-orphan",
        order_by="PhysicianDecisionMedication.created_at",
    )


class PhysicianDecisionMedication(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "physician_decision_medications"
    __table_args__ = (Index("ix_decision_medication_decision", "decision_id"),)

    decision_id: Mapped[UUID] = mapped_column(
        ForeignKey("physician_decisions.id", ondelete="CASCADE"), nullable=False
    )
    medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="RESTRICT"), nullable=False
    )
    medication_order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("medication_orders.id", ondelete="SET NULL"), nullable=True
    )
    dose: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    dose_unit: Mapped[str] = mapped_column(String(30), nullable=False)
    route: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    duration_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    indication: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None] = mapped_column(nullable=True)

    decision: Mapped[PhysicianDecision] = relationship(back_populates="medications")
    medication: Mapped["Medication"] = relationship()
    medication_order: Mapped["MedicationOrder | None"] = relationship()


__all__ = ["PhysicianDecision", "PhysicianDecisionMedication", "PhysicianDecisionType"]
