from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.clinical import Encounter
    from app.models.identity import User
    from app.models.organization import Organization
    from app.models.patient import Patient


class MedicationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MedicationOrderStatus(StrEnum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    DISCONTINUED = "DISCONTINUED"
    CANCELLED = "CANCELLED"


class DurationUnit(StrEnum):
    DAYS = "DAYS"
    WEEKS = "WEEKS"
    MONTHS = "MONTHS"
    DOSES = "DOSES"


class Medication(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "medications"
    __table_args__ = (Index("ix_medication_generic_name", "generic_name"),)

    standardized_code: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    generic_name: Mapped[str] = mapped_column(String(200), nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dosage_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[MedicationStatus] = mapped_column(
        SQLEnum(MedicationStatus, name="medication_status_enum"),
        default=MedicationStatus.ACTIVE,
        server_default=MedicationStatus.ACTIVE.value,
        nullable=False,
    )


class MedicationOrder(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "medication_orders"
    __table_args__ = (
        Index("ix_med_order_patient_org_start", "patient_id", "organization_id", "start_date"),
    )

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    encounter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True
    )
    medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="RESTRICT"), nullable=False
    )
    dose: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    dose_unit: Mapped[str] = mapped_column(String(30), nullable=False)
    route: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    duration_unit: Mapped[DurationUnit | None] = mapped_column(
        SQLEnum(DurationUnit, name="duration_unit_enum"), nullable=True
    )
    indication: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None] = mapped_column(nullable=True)
    prescriber_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[MedicationOrderStatus] = mapped_column(
        SQLEnum(MedicationOrderStatus, name="medication_order_status_enum"),
        default=MedicationOrderStatus.PROPOSED,
        server_default=MedicationOrderStatus.PROPOSED.value,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    encounter: Mapped["Encounter | None"] = relationship()
    medication: Mapped[Medication] = relationship()
    prescriber: Mapped["User | None"] = relationship()
    status_history: Mapped[list["MedicationOrderStatusHistory"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="MedicationOrderStatusHistory.changed_at",
    )


class MedicationOrderStatusHistory(UUIDPKMixin, Base):
    __tablename__ = "medication_order_status_history"

    order_id: Mapped[UUID] = mapped_column(
        ForeignKey("medication_orders.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[MedicationOrderStatus | None] = mapped_column(
        SQLEnum(MedicationOrderStatus, name="medication_order_status_enum"), nullable=True
    )
    to_status: Mapped[MedicationOrderStatus] = mapped_column(
        SQLEnum(MedicationOrderStatus, name="medication_order_status_enum"), nullable=False
    )
    changed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped[MedicationOrder] = relationship(back_populates="status_history")
    actor: Mapped["User | None"] = relationship()


__all__ = [
    "DurationUnit",
    "Medication",
    "MedicationOrder",
    "MedicationOrderStatus",
    "MedicationOrderStatusHistory",
    "MedicationStatus",
]
