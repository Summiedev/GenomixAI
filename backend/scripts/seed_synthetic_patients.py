"""Seed 50-200 deterministic cardiovascular test patients.

Run from ``backend`` after migrations and the base seed:

    uv run python scripts/seed_data.py
    uv run python scripts/seed_synthetic_patients.py --count 100

The script is additive and idempotent. All records are visibly synthetic, and all
genomic profiles are marked NOT_CLINICALLY_VALIDATED. No genomic interpretations
or medical recommendations are generated from the synthetic source results.
"""

import argparse
import asyncio
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.db.session import create_engine  # noqa: E402
from app.models import (  # noqa: E402
    Condition,
    Encounter,
    EncounterType,
    GenomicDataSource,
    GenomicProfile,
    GenomicRecordStatus,
    GenomicValidationStatus,
    GenomicVariant,
    LabResult,
    Organization,
    Patient,
    PatientLinkStatus,
    PatientOrganizationLink,
    PatientSex,
    PatientStatus,
    RecordStatus,
    User,
    Vital,
    VitalType,
)

MIN_PATIENTS = 50
MAX_PATIENTS = 200
DEFAULT_PATIENTS = 100
SYNTHETIC = "SYNTHETIC"
FIXTURE_VERSION = "cardiovascular-fixtures-v1"
FIXTURE_NAMESPACE = UUID("61f00e0a-929a-4ea0-a7da-b93ec881ef22")


def stable_id(label: str) -> UUID:
    return uuid5(FIXTURE_NAMESPACE, label)


def validate_count(value: int) -> int:
    if not MIN_PATIENTS <= value <= MAX_PATIENTS:
        raise ValueError(f"count must be between {MIN_PATIENTS} and {MAX_PATIENTS}")
    return value


def genotype_fixture(index: int) -> tuple[dict[str, str], ...]:
    """Return synthetic source calls only; these are not clinical interpretations."""

    tier = index % 3
    calls = (
        (
            {
                "variant": "star allele call",
                "allele": "*1/*1",
                "genotype": "*1/*1",
                "phenotype": "NORMAL_METABOLIZER",
            },
            {
                "variant": "star allele call",
                "allele": "*1/*2",
                "genotype": "*1/*2",
                "phenotype": "INTERMEDIATE_METABOLIZER",
            },
            {
                "variant": "star allele call",
                "allele": "*2/*2",
                "genotype": "*2/*2",
                "phenotype": "POOR_METABOLIZER",
            },
        )[tier],
        (
            {
                "variant": "star allele call",
                "allele": "*1/*1",
                "genotype": "*1/*1",
                "phenotype": "NORMAL_METABOLIZER",
            },
            {
                "variant": "star allele call",
                "allele": "*1/*3",
                "genotype": "*1/*3",
                "phenotype": "INTERMEDIATE_METABOLIZER",
            },
            {
                "variant": "star allele call",
                "allele": "*3/*3",
                "genotype": "*3/*3",
                "phenotype": "POOR_METABOLIZER",
            },
        )[tier],
        (
            {
                "variant": "rs9923231",
                "allele": "G/G",
                "genotype": "G/G",
                "phenotype": "SYNTHETIC_SOURCE_CALL_ONLY",
            },
            {
                "variant": "rs9923231",
                "allele": "G/A",
                "genotype": "G/A",
                "phenotype": "SYNTHETIC_SOURCE_CALL_ONLY",
            },
            {
                "variant": "rs9923231",
                "allele": "A/A",
                "genotype": "A/A",
                "phenotype": "SYNTHETIC_SOURCE_CALL_ONLY",
            },
        )[tier],
        (
            {
                "variant": "rs2108622",
                "allele": "C/C",
                "genotype": "C/C",
                "phenotype": "SYNTHETIC_SOURCE_CALL_ONLY",
            },
            {
                "variant": "rs2108622",
                "allele": "C/T",
                "genotype": "C/T",
                "phenotype": "SYNTHETIC_SOURCE_CALL_ONLY",
            },
            {
                "variant": "rs2108622",
                "allele": "T/T",
                "genotype": "T/T",
                "phenotype": "SYNTHETIC_SOURCE_CALL_ONLY",
            },
        )[tier],
        (
            {
                "variant": "rs4149056",
                "allele": "T/T",
                "genotype": "T/T",
                "phenotype": "NORMAL_FUNCTION",
            },
            {
                "variant": "rs4149056",
                "allele": "T/C",
                "genotype": "T/C",
                "phenotype": "DECREASED_FUNCTION",
            },
            {
                "variant": "rs4149056",
                "allele": "C/C",
                "genotype": "C/C",
                "phenotype": "POOR_FUNCTION",
            },
        )[tier],
        (
            {
                "variant": "star allele call",
                "allele": "*1/*1",
                "genotype": "*1/*1",
                "phenotype": "NORMAL_METABOLIZER",
            },
            {
                "variant": "star allele call",
                "allele": "*1/*4",
                "genotype": "*1/*4",
                "phenotype": "INTERMEDIATE_METABOLIZER",
            },
            {
                "variant": "star allele call",
                "allele": "*4/*4",
                "genotype": "*4/*4",
                "phenotype": "POOR_METABOLIZER",
            },
        )[tier],
    )
    genes = ("CYP2C19", "CYP2C9", "VKORC1", "CYP4F2", "SLCO1B1", "CYP2D6")
    return tuple({"gene": gene, **call} for gene, call in zip(genes, calls, strict=True))


async def _get_required_base_records(
    db: AsyncSession,
) -> tuple[dict[str, Organization], dict[str, User]]:
    organizations: dict[str, Organization] = {}
    physicians: dict[str, User] = {}
    for hospital_slug in ("hospital-a", "hospital-b"):
        organization = await db.scalar(
            select(Organization).where(Organization.slug == hospital_slug)
        )
        physician = await db.scalar(
            select(User).where(User.email == f"seed.physician.{hospital_slug[-1]}@genomixai.demo")
        )
        if organization is None or physician is None:
            raise RuntimeError(
                "Base synthetic organizations and physicians are missing. "
                "Run `uv run python scripts/seed_data.py` first."
            )
        organizations[hospital_slug] = organization
        physicians[hospital_slug] = physician
    return organizations, physicians


async def _get_or_add(db: AsyncSession, model, record_id: UUID, **values):
    record = await db.get(model, record_id)
    if record is None:
        record = model(id=record_id, **values)
        db.add(record)
        await db.flush()
    return record


async def seed_patients(count: int = DEFAULT_PATIENTS) -> int:
    count = validate_count(count)
    settings = get_settings()
    engine = create_engine(settings)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as db:
            organizations, physicians = await _get_required_base_records(db)
            for index in range(1, count + 1):
                hospital_slug = "hospital-a" if index <= (count + 1) // 2 else "hospital-b"
                hospital_code = hospital_slug[-1].upper()
                organization = organizations[hospital_slug]
                physician = physicians[hospital_slug]
                patient_code = f"SYN-CV-{index:04d}"
                patient = await _get_or_add(
                    db,
                    Patient,
                    stable_id(f"patient:{patient_code}"),
                    genomix_patient_id=patient_code,
                    first_name="Synthetic",
                    last_name=f"Cardio-{index:04d}",
                    date_of_birth=date(1940 + (index % 55), (index % 12) + 1, (index % 27) + 1),
                    sex=(PatientSex.FEMALE, PatientSex.MALE, PatientSex.UNKNOWN)[index % 3],
                    status=PatientStatus.ACTIVE,
                )
                await _get_or_add(
                    db,
                    PatientOrganizationLink,
                    stable_id(f"patient-link:{patient_code}:{hospital_slug}"),
                    patient_id=patient.id,
                    organization_id=organization.id,
                    mrn=f"{hospital_code}-SYN-CV-{index:04d}",
                    status=PatientLinkStatus.ACTIVE,
                )
                encounter = await _get_or_add(
                    db,
                    Encounter,
                    stable_id(f"encounter:{patient_code}"),
                    patient_id=patient.id,
                    organization_id=organization.id,
                    encounter_type=EncounterType.OUTPATIENT,
                    started_at=datetime(2026, (index % 8) + 1, (index % 27) + 1, 9, tzinfo=UTC),
                    reason="Synthetic cardiovascular pharmacogenomics fixture",
                    created_by=physician.id,
                    source=SYNTHETIC,
                    status=RecordStatus.ACTIVE,
                )
                condition_name, condition_code = (
                    ("Atrial fibrillation", "I48.91"),
                    ("Coronary artery disease", "I25.10"),
                    ("Hypertension", "I10"),
                )[index % 3]
                await _get_or_add(
                    db,
                    Condition,
                    stable_id(f"condition:{patient_code}"),
                    patient_id=patient.id,
                    organization_id=organization.id,
                    encounter_id=encounter.id,
                    code=condition_code,
                    name=condition_name,
                    onset_date=date(2024, (index % 12) + 1, 1),
                    created_by=physician.id,
                    source=SYNTHETIC,
                    status=RecordStatus.ACTIVE,
                )
                measured_at = datetime(2026, (index % 8) + 1, (index % 27) + 1, 9, 15, tzinfo=UTC)
                await _get_or_add(
                    db,
                    Vital,
                    stable_id(f"vital-heart-rate:{patient_code}"),
                    patient_id=patient.id,
                    organization_id=organization.id,
                    encounter_id=encounter.id,
                    vital_type=VitalType.HEART_RATE,
                    value=58 + (index % 35),
                    unit="bpm",
                    measured_at=measured_at,
                    created_by=physician.id,
                    source=SYNTHETIC,
                    status=RecordStatus.ACTIVE,
                )
                ldl_value = 70 + (index % 91)
                await _get_or_add(
                    db,
                    LabResult,
                    stable_id(f"lab-ldl:{patient_code}"),
                    patient_id=patient.id,
                    organization_id=organization.id,
                    encounter_id=encounter.id,
                    test_name="LDL cholesterol",
                    value=str(ldl_value),
                    numeric_value=ldl_value,
                    unit="mg/dL",
                    reference_range="0-100",
                    collected_at=measured_at,
                    created_by=physician.id,
                    source=SYNTHETIC,
                    status=RecordStatus.ACTIVE,
                )
                profile = await _get_or_add(
                    db,
                    GenomicProfile,
                    stable_id(f"genomic-profile:{patient_code}"),
                    patient_id=patient.id,
                    organization_id=organization.id,
                    test_date=date(2026, 1, (index % 27) + 1),
                    source=GenomicDataSource.SYNTHETIC,
                    source_version=FIXTURE_VERSION,
                    validation_status=GenomicValidationStatus.NOT_CLINICALLY_VALIDATED,
                    status=GenomicRecordStatus.ACTIVE,
                    notes=(
                        "SYNTHETIC TEST DATA ONLY. Genotypes are deterministic fixtures, "
                        "not laboratory results and not clinically validated."
                    ),
                )
                for call in genotype_fixture(index):
                    gene = call["gene"]
                    await _get_or_add(
                        db,
                        GenomicVariant,
                        stable_id(f"genomic-variant:{patient_code}:{gene}"),
                        profile_id=profile.id,
                        gene=gene,
                        variant=call["variant"],
                        allele=call["allele"],
                        genotype=call["genotype"],
                        phenotype=call["phenotype"],
                        raw_result={
                            "data_source": SYNTHETIC,
                            "clinical_validation": "NOT_CLINICALLY_VALIDATED",
                            "fixture_version": FIXTURE_VERSION,
                            "call": call["genotype"],
                        },
                        source=GenomicDataSource.SYNTHETIC,
                        source_version=FIXTURE_VERSION,
                        status=GenomicRecordStatus.ACTIVE,
                    )
            await db.commit()
    finally:
        await engine.dispose()
    return count


async def synthetic_patient_summary() -> dict[str, int | dict[str, int]]:
    """Return a read-only summary of this fixture set in the configured database."""

    settings = get_settings()
    engine = create_engine(settings)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as db:
            patient_filter = Patient.genomix_patient_id.like("SYN-CV-%")
            patient_count = await db.scalar(
                select(func.count()).select_from(Patient).where(patient_filter)
            )
            organization_rows = (
                await db.execute(
                    select(Organization.slug, func.count(Patient.id))
                    .select_from(PatientOrganizationLink)
                    .join(Patient, Patient.id == PatientOrganizationLink.patient_id)
                    .join(
                        Organization,
                        Organization.id == PatientOrganizationLink.organization_id,
                    )
                    .where(patient_filter)
                    .group_by(Organization.slug)
                    .order_by(Organization.slug)
                )
            ).all()
            profile_count = await db.scalar(
                select(func.count())
                .select_from(GenomicProfile)
                .join(Patient, Patient.id == GenomicProfile.patient_id)
                .where(
                    patient_filter,
                    GenomicProfile.source == GenomicDataSource.SYNTHETIC,
                    GenomicProfile.validation_status
                    == GenomicValidationStatus.NOT_CLINICALLY_VALIDATED,
                )
            )
    finally:
        await engine.dispose()
    return {
        "patients": patient_count or 0,
        "organizations": dict(organization_rows),
        "synthetic_unvalidated_profiles": profile_count or 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_PATIENTS,
        help=f"number of patients ({MIN_PATIENTS}-{MAX_PATIENTS}; default {DEFAULT_PATIENTS})",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="do not insert records; print the persisted synthetic-fixture summary",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    try:
        if arguments.verify_only:
            summary = asyncio.run(synthetic_patient_summary())
        else:
            created_count = asyncio.run(seed_patients(arguments.count))
            summary = asyncio.run(synthetic_patient_summary())
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error
    if not arguments.verify_only:
        print(f"{created_count} deterministic synthetic cardiovascular patients are ready.")
    print(summary)
