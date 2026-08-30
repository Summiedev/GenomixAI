"""Create repeatable, clearly synthetic development fixtures.

Run from ``backend`` after applying migrations:
    python scripts/seed_data.py

The script is additive and safe to run repeatedly. It never uses real patient data.
"""

import asyncio
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.clinical_engine.state_machine import AssessmentState  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import create_engine  # noqa: E402
from app.models import (  # noqa: E402
    AdverseDrugReaction,
    Allergy,
    AssessmentMedication,
    ClinicalNote,
    Condition,
    Department,
    Encounter,
    EncounterType,
    GenomicDataSource,
    GenomicProfile,
    GenomicRecordStatus,
    GenomicValidationStatus,
    GenomicVariant,
    LabResult,
    Medication,
    MedicationAssessment,
    MedicationOrder,
    MedicationOrderStatus,
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
    Patient,
    PatientLinkStatus,
    PatientOrganizationLink,
    PatientSex,
    PatientStatus,
    PharmacistReview,
    PharmacistReviewStatus,
    RecordStatus,
    ReviewPriority,
    Role,
    User,
    UserStatus,
    Vital,
    VitalType,
)
from app.models.medication import DurationUnit  # noqa: E402

SEED_NAMESPACE = UUID("77a5d2f1-8e1d-4ccf-82ee-26ea7b421019")
SYNTHETIC = "SYNTHETIC"
SEED_PASSWORD = "ChangeMe123!"


def stable_id(label: str) -> UUID:
    return uuid5(SEED_NAMESPACE, label)


async def seed() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        organizations = {}
        departments = {}
        for hospital_name, hospital_slug in (
            ("Hospital A", "hospital-a"),
            ("Hospital B", "hospital-b"),
        ):
            organization = await db.scalar(
                select(Organization).where(Organization.slug == hospital_slug)
            )
            if organization is None:
                organization = Organization(
                    id=stable_id(f"organization:{hospital_slug}"),
                    name=hospital_name,
                    slug=hospital_slug,
                    status=OrganizationStatus.ACTIVE,
                )
                db.add(organization)
                await db.flush()
            organizations[hospital_slug] = organization
            for department_name, department_slug in (
                ("Cardiology", "cardiology"),
                ("Pharmacy", "pharmacy"),
                ("Internal Medicine", "internal-medicine"),
            ):
                department = await db.scalar(
                    select(Department).where(
                        Department.organization_id == organization.id,
                        Department.slug == department_slug,
                    )
                )
                if department is None:
                    department = Department(
                        id=stable_id(f"department:{hospital_slug}:{department_slug}"),
                        organization_id=organization.id,
                        name=department_name,
                        slug=department_slug,
                        status=OrganizationStatus.ACTIVE,
                    )
                    db.add(department)
                    await db.flush()
                departments[(hospital_slug, department_slug)] = department

        users = {}
        for hospital_slug, role, local_name, department_slug in (
            ("hospital-a", Role.PHYSICIAN, "Synthetic Physician A", "cardiology"),
            ("hospital-a", Role.CLINICAL_PHARMACIST, "Synthetic Pharmacist A", "pharmacy"),
            ("hospital-b", Role.PHYSICIAN, "Synthetic Physician B", "cardiology"),
            ("hospital-b", Role.CLINICAL_PHARMACIST, "Synthetic Pharmacist B", "pharmacy"),
        ):
            email = f"seed.{role.value.lower()}.{hospital_slug[-1]}@genomixai.demo"
            user = await db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    id=stable_id(f"user:{email}"),
                    email=email,
                    full_name=local_name,
                    password_hash=hash_password(SEED_PASSWORD),
                    status=UserStatus.ACTIVE,
                )
                db.add(user)
                await db.flush()
            users[(hospital_slug, role)] = user
            membership = await db.scalar(
                select(OrganizationMembership).where(
                    OrganizationMembership.user_id == user.id,
                    OrganizationMembership.organization_id == organizations[hospital_slug].id,
                )
            )
            if membership is None:
                db.add(
                    OrganizationMembership(
                        id=stable_id(f"membership:{email}:{hospital_slug}"),
                        user_id=user.id,
                        organization_id=organizations[hospital_slug].id,
                        department_id=departments[(hospital_slug, department_slug)].id,
                        role=role,
                        status=MembershipStatus.ACTIVE,
                    )
                )

        medications = {}
        for generic_name, strength, form in (
            ("Aspirin", "81 mg", "TABLET"),
            ("Clopidogrel", "75 mg", "TABLET"),
            ("Atorvastatin", "20 mg", "TABLET"),
        ):
            medication = await db.scalar(
                select(Medication).where(Medication.generic_name == generic_name)
            )
            if medication is None:
                medication = Medication(
                    id=stable_id(f"medication:{generic_name.lower()}"),
                    generic_name=generic_name,
                    strength=strength,
                    dosage_form=form,
                )
                db.add(medication)
                await db.flush()
            medications[generic_name] = medication

        for hospital_slug, patient_code, first_name, last_name, sex in (
            ("hospital-a", "SEED-A-001", "Synthetic", "Patient A", PatientSex.FEMALE),
            ("hospital-b", "SEED-B-001", "Synthetic", "Patient B", PatientSex.MALE),
        ):
            organization = organizations[hospital_slug]
            patient = await db.scalar(
                select(Patient).where(Patient.genomix_patient_id == patient_code)
            )
            if patient is None:
                patient = Patient(
                    id=stable_id(f"patient:{patient_code}"),
                    genomix_patient_id=patient_code,
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=date(1984, 4, 12),
                    sex=sex,
                    status=PatientStatus.ACTIVE,
                )
                db.add(patient)
                await db.flush()
            link = await db.scalar(
                select(PatientOrganizationLink).where(
                    PatientOrganizationLink.patient_id == patient.id,
                    PatientOrganizationLink.organization_id == organization.id,
                )
            )
            if link is None:
                db.add(
                    PatientOrganizationLink(
                        id=stable_id(f"patient-link:{patient_code}:{hospital_slug}"),
                        patient_id=patient.id,
                        organization_id=organization.id,
                        mrn=f"{hospital_slug[-1].upper()}-SEED-001",
                        status=PatientLinkStatus.ACTIVE,
                    )
                )
            physician = users[(hospital_slug, Role.PHYSICIAN)]
            encounter = await db.scalar(
                select(Encounter).where(
                    Encounter.patient_id == patient.id,
                    Encounter.organization_id == organization.id,
                    Encounter.source == SYNTHETIC,
                    Encounter.reason == "Synthetic cardiovascular follow-up",
                )
            )
            if encounter is None:
                encounter = Encounter(
                    id=stable_id(f"encounter:{patient_code}"),
                    patient_id=patient.id,
                    organization_id=organization.id,
                    encounter_type=EncounterType.OUTPATIENT,
                    started_at=datetime(2026, 7, 15, 9, tzinfo=UTC),
                    reason="Synthetic cardiovascular follow-up",
                    created_by=physician.id,
                    source=SYNTHETIC,
                    status=RecordStatus.ACTIVE,
                )
                db.add(encounter)
                await db.flush()
            await _add_once(
                db,
                Condition,
                patient_id=patient.id,
                organization_id=organization.id,
                name="Atrial fibrillation",
                code="I48.91",
                onset_date=date(2025, 11, 1),
                encounter_id=encounter.id,
                created_by=physician.id,
                source=SYNTHETIC,
                status=RecordStatus.ACTIVE,
            )
            await _add_once(
                db,
                Vital,
                patient_id=patient.id,
                organization_id=organization.id,
                vital_type=VitalType.HEART_RATE,
                value=72,
                unit="bpm",
                measured_at=datetime(2026, 7, 15, 9, 10, tzinfo=UTC),
                encounter_id=encounter.id,
                created_by=physician.id,
                source=SYNTHETIC,
                status=RecordStatus.ACTIVE,
            )
            await _add_once(
                db,
                LabResult,
                patient_id=patient.id,
                organization_id=organization.id,
                test_name="LDL cholesterol",
                value="118",
                numeric_value=118,
                unit="mg/dL",
                reference_range="0-100",
                collected_at=datetime(2026, 7, 15, 8, 30, tzinfo=UTC),
                encounter_id=encounter.id,
                created_by=physician.id,
                source=SYNTHETIC,
                status=RecordStatus.ACTIVE,
            )
            await _add_once(
                db,
                Allergy,
                patient_id=patient.id,
                organization_id=organization.id,
                allergen="Penicillin",
                reaction="Rash",
                severity="MODERATE",
                encounter_id=encounter.id,
                created_by=physician.id,
                source=SYNTHETIC,
                status=RecordStatus.ACTIVE,
            )
            await _add_once(
                db,
                AdverseDrugReaction,
                patient_id=patient.id,
                organization_id=organization.id,
                medication="Atorvastatin",
                reaction="Muscle pain",
                severity="MODERATE",
                occurred_at=datetime(2025, 8, 1, tzinfo=UTC),
                encounter_id=encounter.id,
                created_by=physician.id,
                source=SYNTHETIC,
                status=RecordStatus.ACTIVE,
            )
            await _add_once(
                db,
                ClinicalNote,
                patient_id=patient.id,
                organization_id=organization.id,
                encounter_id=encounter.id,
                note_type="SYNTHETIC_FOLLOW_UP",
                content="Synthetic development note: cardiovascular follow-up completed.",
                noted_at=datetime(2026, 7, 15, 9, 30, tzinfo=UTC),
                created_by=physician.id,
                source=SYNTHETIC,
                status=RecordStatus.ACTIVE,
            )
            for medication_name, order_status, start_date, end_date in (
                ("Aspirin", MedicationOrderStatus.ACTIVE, date(2026, 1, 1), None),
                (
                    "Atorvastatin",
                    MedicationOrderStatus.COMPLETED,
                    date(2025, 1, 1),
                    date(2025, 4, 1),
                ),
            ):
                await _add_once(
                    db,
                    MedicationOrder,
                    patient_id=patient.id,
                    organization_id=organization.id,
                    medication_id=medications[medication_name].id,
                    encounter_id=encounter.id,
                    dose=20 if medication_name == "Atorvastatin" else 81,
                    dose_unit="mg",
                    route="ORAL",
                    frequency="ONCE_DAILY",
                    duration_value=90 if end_date else None,
                    duration_unit=DurationUnit.DAYS if end_date else None,
                    indication="Synthetic cardiovascular therapy",
                    start_date=start_date,
                    end_date=end_date,
                    prescriber_id=physician.id,
                    status=order_status,
                    source=SYNTHETIC,
                )
            if hospital_slug == "hospital-a":
                assessment = await db.scalar(
                    select(MedicationAssessment).where(
                        MedicationAssessment.patient_id == patient.id,
                        MedicationAssessment.organization_id == organization.id,
                        MedicationAssessment.patient_context_reference
                        == f"seed:{patient_code}:assessment",
                    )
                )
                if assessment is None:
                    assessment = MedicationAssessment(
                        id=stable_id(f"assessment:{patient_code}"),
                        patient_id=patient.id,
                        organization_id=organization.id,
                        created_by=physician.id,
                        patient_context_version="clinical-context-v1",
                        patient_context_reference=f"seed:{patient_code}:assessment",
                        engine_version="clinical-engine-1.0.0",
                        status=AssessmentState.PENDING_PHARMACIST_REVIEW,
                    )
                    db.add(assessment)
                    await db.flush()
                    db.add(
                        AssessmentMedication(
                            id=stable_id(f"assessment-medication:{patient_code}"),
                            assessment_id=assessment.id,
                            medication_id=medications["Clopidogrel"].id,
                            dose="75",
                            dose_unit="mg",
                            route="ORAL",
                            frequency="ONCE_DAILY",
                            indication="Synthetic antiplatelet example",
                            source=SYNTHETIC,
                        )
                    )
                    db.add(
                        PharmacistReview(
                            id=stable_id(f"review:{patient_code}"),
                            assessment_id=assessment.id,
                            organization_id=organization.id,
                            requested_by=physician.id,
                            priority=ReviewPriority.NORMAL,
                            status=PharmacistReviewStatus.REQUESTED,
                            physician_message="Synthetic example awaiting pharmacist review.",
                        )
                    )
            profile = await db.scalar(
                select(GenomicProfile).where(
                    GenomicProfile.patient_id == patient.id,
                    GenomicProfile.organization_id == organization.id,
                    GenomicProfile.source == GenomicDataSource.SYNTHETIC,
                )
            )
            if profile is None:
                profile = GenomicProfile(
                    id=stable_id(f"genomic-profile:{patient_code}"),
                    patient_id=patient.id,
                    organization_id=organization.id,
                    test_date=date(2026, 7, 10),
                    source=GenomicDataSource.SYNTHETIC,
                    source_version="seed-v1",
                    validation_status=GenomicValidationStatus.NOT_CLINICALLY_VALIDATED,
                    status=GenomicRecordStatus.ACTIVE,
                    notes="Synthetic development fixture; not clinical data.",
                )
                db.add(profile)
                await db.flush()
            variant = await db.scalar(
                select(GenomicVariant).where(
                    GenomicVariant.profile_id == profile.id,
                    GenomicVariant.gene == "CYP2C19",
                )
            )
            if variant is None:
                db.add(
                    GenomicVariant(
                        id=stable_id(f"genomic-variant:{patient_code}:CYP2C19"),
                        profile_id=profile.id,
                        gene="CYP2C19",
                        variant="*2",
                        allele="*2",
                        genotype="*1/*2",
                        phenotype="INTERMEDIATE_METABOLIZER",
                        raw_result={"call": "*1/*2", "source": SYNTHETIC},
                        source=GenomicDataSource.SYNTHETIC,
                        source_version="seed-v1",
                        status=GenomicRecordStatus.ACTIVE,
                    )
                )

        await db.commit()
    await engine.dispose()
    print("Synthetic seed data is ready for Hospital A and Hospital B.")


async def _add_once(db, model, **values):
    filters = [
        getattr(model, key) == value
        for key, value in values.items()
        if key
        in {
            "patient_id",
            "organization_id",
            "name",
            "test_name",
            "allergen",
            "medication",
            "medication_id",
            "start_date",
            "source",
        }
    ]
    if filters and await db.scalar(select(model).where(*filters)) is not None:
        return
    db.add(model(**values))


if __name__ == "__main__":
    asyncio.run(seed())
