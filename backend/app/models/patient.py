from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class PatientStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class PatientSex(StrEnum):
    FEMALE = "FEMALE"
    MALE = "MALE"
    INTERSEX = "INTERSEX"
    UNKNOWN = "UNKNOWN"


class PatientLinkStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Patient(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "patients"

    genomix_patient_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(nullable=False)
    sex: Mapped[PatientSex] = mapped_column(
        SQLEnum(PatientSex, name="patient_sex_enum"), nullable=False
    )
    status: Mapped[PatientStatus] = mapped_column(
        SQLEnum(PatientStatus, name="patient_status_enum"),
        default=PatientStatus.ACTIVE,
        server_default=PatientStatus.ACTIVE.value,
        nullable=False,
    )

    organization_links: Mapped[list["PatientOrganizationLink"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class PatientOrganizationLink(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "patient_organization_links"
    __table_args__ = (
        UniqueConstraint("patient_id", "organization_id", name="uq_patient_organization_link"),
        UniqueConstraint("organization_id", "mrn", name="uq_patient_organization_mrn"),
        Index("ix_patient_link_organization_patient", "organization_id", "patient_id"),
    )

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    mrn: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[PatientLinkStatus] = mapped_column(
        SQLEnum(PatientLinkStatus, name="patient_link_status_enum"),
        default=PatientLinkStatus.ACTIVE,
        server_default=PatientLinkStatus.ACTIVE.value,
        nullable=False,
    )

    patient: Mapped[Patient] = relationship(back_populates="organization_links")
    organization: Mapped["Organization"] = relationship()


__all__ = [
    "Patient",
    "PatientLinkStatus",
    "PatientOrganizationLink",
    "PatientSex",
    "PatientStatus",
]
