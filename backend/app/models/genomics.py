from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class GenomicDataSource(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    RESEARCH_DATASET = "RESEARCH_DATASET"
    CLINICAL_LAB = "CLINICAL_LAB"
    UNKNOWN = "UNKNOWN"


class GenomicValidationStatus(StrEnum):
    NOT_CLINICALLY_VALIDATED = "NOT_CLINICALLY_VALIDATED"
    CLINICALLY_VALIDATED = "CLINICALLY_VALIDATED"


class GenomicRecordStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class GenomicProfile(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "genomic_profiles"
    __table_args__ = (
        Index("ix_genomic_profile_patient_org_test", "patient_id", "organization_id", "test_date"),
    )

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    test_date: Mapped[date] = mapped_column(nullable=False)
    source: Mapped[GenomicDataSource] = mapped_column(
        SQLEnum(GenomicDataSource, name="genomic_data_source_enum"), nullable=False
    )
    source_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    validation_status: Mapped[GenomicValidationStatus] = mapped_column(
        SQLEnum(GenomicValidationStatus, name="genomic_validation_status_enum"),
        default=GenomicValidationStatus.NOT_CLINICALLY_VALIDATED,
        server_default=GenomicValidationStatus.NOT_CLINICALLY_VALIDATED.value,
        nullable=False,
    )
    status: Mapped[GenomicRecordStatus] = mapped_column(
        SQLEnum(GenomicRecordStatus, name="genomic_record_status_enum"),
        default=GenomicRecordStatus.ACTIVE,
        server_default=GenomicRecordStatus.ACTIVE.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped["Patient"] = relationship()
    variants: Mapped[list["GenomicVariant"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    interpretations: Mapped[list["PharmacogenomicInterpretation"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class GenomicVariant(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "genomic_variants"
    __table_args__ = (Index("ix_genomic_variant_profile_gene", "profile_id", "gene"),)

    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("genomic_profiles.id", ondelete="CASCADE"), nullable=False
    )
    gene: Mapped[str] = mapped_column(String(50), nullable=False)
    variant: Mapped[str] = mapped_column(String(200), nullable=False)
    allele: Mapped[str | None] = mapped_column(String(100), nullable=True)
    genotype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phenotype: Mapped[str | None] = mapped_column(String(200), nullable=True)
    raw_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source: Mapped[GenomicDataSource] = mapped_column(
        SQLEnum(GenomicDataSource, name="genomic_data_source_enum"), nullable=False
    )
    source_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[GenomicRecordStatus] = mapped_column(
        SQLEnum(GenomicRecordStatus, name="genomic_record_status_enum"),
        default=GenomicRecordStatus.ACTIVE,
        server_default=GenomicRecordStatus.ACTIVE.value,
        nullable=False,
    )

    profile: Mapped[GenomicProfile] = relationship(back_populates="variants")
    interpretations: Mapped[list["PharmacogenomicInterpretation"]] = relationship(
        back_populates="variant"
    )


class PharmacogenomicInterpretation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pharmacogenomic_interpretations"
    __table_args__ = (Index("ix_pg_interpretation_profile_gene", "profile_id", "gene"),)

    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("genomic_profiles.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("genomic_variants.id", ondelete="SET NULL"), nullable=True
    )
    gene: Mapped[str] = mapped_column(String(50), nullable=False)
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    clinical_significance: Mapped[str | None] = mapped_column(String(200), nullable=True)
    evidence_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    interpretation_date: Mapped[date] = mapped_column(nullable=False)
    source: Mapped[GenomicDataSource] = mapped_column(
        SQLEnum(GenomicDataSource, name="genomic_data_source_enum"), nullable=False
    )
    source_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[GenomicRecordStatus] = mapped_column(
        SQLEnum(GenomicRecordStatus, name="genomic_record_status_enum"),
        default=GenomicRecordStatus.ACTIVE,
        server_default=GenomicRecordStatus.ACTIVE.value,
        nullable=False,
    )

    profile: Mapped[GenomicProfile] = relationship(back_populates="interpretations")
    variant: Mapped[GenomicVariant | None] = relationship(back_populates="interpretations")
    evidence_references: Mapped[list["EvidenceReference"]] = relationship(
        back_populates="interpretation", cascade="all, delete-orphan"
    )


class EvidenceReference(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "evidence_references"

    interpretation_id: Mapped[UUID] = mapped_column(
        ForeignKey("pharmacogenomic_interpretations.id", ondelete="CASCADE"), nullable=False
    )
    citation: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source: Mapped[GenomicDataSource] = mapped_column(
        SQLEnum(GenomicDataSource, name="genomic_data_source_enum"), nullable=False
    )
    source_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    interpretation: Mapped[PharmacogenomicInterpretation] = relationship(
        back_populates="evidence_references"
    )


__all__ = [
    "EvidenceReference",
    "GenomicDataSource",
    "GenomicProfile",
    "GenomicRecordStatus",
    "GenomicValidationStatus",
    "GenomicVariant",
    "PharmacogenomicInterpretation",
]
