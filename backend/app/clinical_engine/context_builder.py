"""Immutable, normalized inputs for the clinical assessment pipeline."""

from dataclasses import dataclass, field, replace
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class MedicationContext:
    name: str
    medication_id: str | None = None
    standardized_code: str | None = None
    brand_name: str | None = None
    dose: Decimal | float | int | None = None
    dose_unit: str | None = None
    status: str = "ACTIVE"
    aliases: tuple[str, ...] = ()


ProposedMedication = MedicationContext


@dataclass(frozen=True)
class GenomicFindingContext:
    gene: str
    phenotype: str | None = None
    genotype: str | None = None
    variant: str | None = None
    source: str | None = None
    validation_status: str | None = None
    profile_id: str | None = None


@dataclass(frozen=True)
class ConditionContext:
    name: str
    code: str | None = None
    status: str = "ACTIVE"


@dataclass(frozen=True)
class AllergyContext:
    allergen: str
    reaction: str | None = None
    severity: str | None = None
    status: str = "ACTIVE"


@dataclass(frozen=True)
class AdverseDrugReactionContext:
    medication: str
    reaction: str
    severity: str | None = None
    status: str = "ACTIVE"


@dataclass(frozen=True)
class LabContext:
    test_name: str
    numeric_value: Decimal | float | int | None = None
    unit: str | None = None
    value: str | None = None
    reference_range: str | None = None
    abnormal: bool | None = None
    status: str = "ACTIVE"


@dataclass(frozen=True)
class VitalContext:
    vital_type: str
    value: Decimal | float | int
    unit: str | None = None
    status: str = "ACTIVE"


@dataclass(frozen=True)
class PatientClinicalContext:
    patient_id: str | None = None
    demographics: dict[str, Any] = field(default_factory=dict)
    conditions: tuple[ConditionContext, ...] = ()
    medications: tuple[MedicationContext, ...] = ()
    allergies: tuple[AllergyContext, ...] = ()
    adverse_drug_reactions: tuple[AdverseDrugReactionContext, ...] = ()
    labs: tuple[LabContext, ...] = ()
    vitals: tuple[VitalContext, ...] = ()
    genomic_findings: tuple[GenomicFindingContext, ...] = ()
    history: tuple[Any, ...] = ()


PatientContext = PatientClinicalContext


def normalize_term(value: Any) -> str:
    """Normalize names and coded values for deterministic comparisons."""

    return " ".join(str(value or "").strip().casefold().replace("_", " ").split())


def medication_identifiers(medication: MedicationContext) -> frozenset[str]:
    values = [
        medication.name,
        medication.medication_id,
        medication.standardized_code,
        medication.brand_name,
        *medication.aliases,
    ]
    return frozenset(normalize_term(value) for value in values if value)


def medication_matches(left: MedicationContext, right: MedicationContext | Any) -> bool:
    """Match by stable code/id first, then by normalized name or alias."""

    if isinstance(right, MedicationContext):
        right_identifiers = medication_identifiers(right)
    else:
        right_identifiers = medication_identifiers(
            MedicationContext(
                name=getattr(right, "generic_name", getattr(right, "name", str(right))),
                medication_id=str(getattr(right, "id", "")) or None,
                standardized_code=getattr(right, "standardized_code", None),
                brand_name=getattr(right, "brand_name", None),
            )
        )
    return bool(medication_identifiers(left) & right_identifiers)


def normalize_context(context: PatientClinicalContext) -> PatientClinicalContext:
    """Copy list-like caller inputs into stable tuples before evaluation."""

    return replace(
        context,
        conditions=tuple(context.conditions),
        medications=tuple(context.medications),
        allergies=tuple(context.allergies),
        adverse_drug_reactions=tuple(context.adverse_drug_reactions),
        labs=tuple(context.labs),
        vitals=tuple(context.vitals),
        genomic_findings=tuple(context.genomic_findings),
        history=tuple(context.history),
    )


__all__ = [
    "AdverseDrugReactionContext",
    "AllergyContext",
    "ConditionContext",
    "GenomicFindingContext",
    "LabContext",
    "MedicationContext",
    "PatientClinicalContext",
    "PatientContext",
    "ProposedMedication",
    "VitalContext",
    "medication_identifiers",
    "medication_matches",
    "normalize_context",
    "normalize_term",
]
