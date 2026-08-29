"""SQLAlchemy models imported centrally for Alembic metadata discovery."""

from app.models.clinical import (
    AdverseDrugReaction,
    Allergy,
    ClinicalNote,
    Condition,
    Encounter,
    EncounterType,
    LabResult,
    RecordStatus,
    Vital,
    VitalType,
)
from app.models.genomics import (
    EvidenceReference,
    GenomicDataSource,
    GenomicProfile,
    GenomicRecordStatus,
    GenomicValidationStatus,
    GenomicVariant,
    PharmacogenomicInterpretation,
)
from app.models.identity import (
    MembershipStatus,
    OrganizationMembership,
    RevokedToken,
    Role,
    User,
    UserStatus,
)
from app.models.medication import (
    DurationUnit,
    Medication,
    MedicationOrder,
    MedicationOrderStatus,
    MedicationOrderStatusHistory,
    MedicationStatus,
)
from app.models.migration_probe import MigrationProbe
from app.models.organization import Department, Organization, OrganizationStatus
from app.models.patient import (
    Patient,
    PatientLinkStatus,
    PatientOrganizationLink,
    PatientSex,
    PatientStatus,
)
from app.models.timeline import ClinicalEvent, ClinicalEventType

__all__ = [
    "Department",
    "AdverseDrugReaction",
    "Allergy",
    "ClinicalEvent",
    "ClinicalEventType",
    "ClinicalNote",
    "Condition",
    "Encounter",
    "EncounterType",
    "EvidenceReference",
    "GenomicDataSource",
    "GenomicProfile",
    "GenomicRecordStatus",
    "GenomicValidationStatus",
    "GenomicVariant",
    "DurationUnit",
    "LabResult",
    "MembershipStatus",
    "MigrationProbe",
    "Medication",
    "MedicationOrder",
    "MedicationOrderStatus",
    "MedicationOrderStatusHistory",
    "MedicationStatus",
    "Organization",
    "OrganizationMembership",
    "OrganizationStatus",
    "Patient",
    "PatientLinkStatus",
    "PatientOrganizationLink",
    "PatientSex",
    "PatientStatus",
    "PharmacogenomicInterpretation",
    "RecordStatus",
    "RevokedToken",
    "Role",
    "User",
    "UserStatus",
    "Vital",
    "VitalType",
]
