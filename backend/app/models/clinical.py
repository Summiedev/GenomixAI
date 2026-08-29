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
    from app.models.identity import User
    from app.models.organization import Organization
    from app.models.patient import Patient


class RecordStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class EncounterType(StrEnum):
    OUTPATIENT = "OUTPATIENT"
    INPATIENT = "INPATIENT"
    EMERGENCY = "EMERGENCY"
    TELEHEALTH = "TELEHEALTH"
    OTHER = "OTHER"


class VitalType(StrEnum):
    HEART_RATE = "HEART_RATE"
    SYSTOLIC_BLOOD_PRESSURE = "SYSTOLIC_BLOOD_PRESSURE"
    DIASTOLIC_BLOOD_PRESSURE = "DIASTOLIC_BLOOD_PRESSURE"
    RESPIRATORY_RATE = "RESPIRATORY_RATE"
    TEMPERATURE = "TEMPERATURE"
    OXYGEN_SATURATION = "OXYGEN_SATURATION"
    WEIGHT = "WEIGHT"
    HEIGHT = "HEIGHT"
    OTHER = "OTHER"


class Encounter(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "encounters"
    __table_args__ = (
        Index("ix_encounter_patient_org_started", "patient_id", "organization_id", "started_at"),
    )

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    encounter_type: Mapped[EncounterType] = mapped_column(
        SQLEnum(EncounterType, name="encounter_type_enum"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )
    status: Mapped[RecordStatus] = mapped_column(
        SQLEnum(RecordStatus, name="clinical_record_status_enum"),
        default=RecordStatus.ACTIVE,
        server_default=RecordStatus.ACTIVE.value,
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    author: Mapped["User | None"] = relationship()


class Condition(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "conditions"
    __table_args__ = (
        Index("ix_condition_patient_org_onset", "patient_id", "organization_id", "onset_date"),
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
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    onset_date: Mapped[date | None] = mapped_column(nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )
    status: Mapped[RecordStatus] = mapped_column(
        SQLEnum(RecordStatus, name="clinical_record_status_enum"),
        default=RecordStatus.ACTIVE,
        server_default=RecordStatus.ACTIVE.value,
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    encounter: Mapped["Encounter | None"] = relationship()
    author: Mapped["User | None"] = relationship()


class ClinicalNote(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "clinical_notes"
    __table_args__ = (
        Index("ix_note_patient_org_noted", "patient_id", "organization_id", "noted_at"),
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
    note_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    noted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )
    status: Mapped[RecordStatus] = mapped_column(
        SQLEnum(RecordStatus, name="clinical_record_status_enum"),
        default=RecordStatus.ACTIVE,
        server_default=RecordStatus.ACTIVE.value,
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    encounter: Mapped["Encounter | None"] = relationship()
    author: Mapped["User | None"] = relationship()


class Vital(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "vitals"
    __table_args__ = (
        Index("ix_vital_patient_org_measured", "patient_id", "organization_id", "measured_at"),
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
    vital_type: Mapped[VitalType] = mapped_column(
        SQLEnum(VitalType, name="vital_type_enum"), nullable=False
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )
    status: Mapped[RecordStatus] = mapped_column(
        SQLEnum(RecordStatus, name="clinical_record_status_enum"),
        default=RecordStatus.ACTIVE,
        server_default=RecordStatus.ACTIVE.value,
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    encounter: Mapped["Encounter | None"] = relationship()
    author: Mapped["User | None"] = relationship()


class LabResult(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "lab_results"
    __table_args__ = (
        Index("ix_lab_patient_org_collected", "patient_id", "organization_id", "collected_at"),
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
    test_name: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 5), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )
    status: Mapped[RecordStatus] = mapped_column(
        SQLEnum(RecordStatus, name="clinical_record_status_enum"),
        default=RecordStatus.ACTIVE,
        server_default=RecordStatus.ACTIVE.value,
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    encounter: Mapped["Encounter | None"] = relationship()
    author: Mapped["User | None"] = relationship()


class Allergy(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "allergies"
    __table_args__ = (
        Index("ix_allergy_patient_org_created", "patient_id", "organization_id", "created_at"),
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
    allergen: Mapped[str] = mapped_column(String(200), nullable=False)
    reaction: Mapped[str | None] = mapped_column(String(500), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )
    status: Mapped[RecordStatus] = mapped_column(
        SQLEnum(RecordStatus, name="clinical_record_status_enum"),
        default=RecordStatus.ACTIVE,
        server_default=RecordStatus.ACTIVE.value,
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    encounter: Mapped["Encounter | None"] = relationship()
    author: Mapped["User | None"] = relationship()


class AdverseDrugReaction(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "adverse_drug_reactions"
    __table_args__ = (
        Index("ix_adr_patient_org_occurred", "patient_id", "organization_id", "occurred_at"),
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
    medication: Mapped[str] = mapped_column(String(200), nullable=False)
    reaction: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )
    status: Mapped[RecordStatus] = mapped_column(
        SQLEnum(RecordStatus, name="clinical_record_status_enum"),
        default=RecordStatus.ACTIVE,
        server_default=RecordStatus.ACTIVE.value,
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    encounter: Mapped["Encounter | None"] = relationship()
    author: Mapped["User | None"] = relationship()


__all__ = [
    "AdverseDrugReaction",
    "Allergy",
    "ClinicalNote",
    "Condition",
    "Encounter",
    "EncounterType",
    "LabResult",
    "RecordStatus",
    "Vital",
    "VitalType",
]
