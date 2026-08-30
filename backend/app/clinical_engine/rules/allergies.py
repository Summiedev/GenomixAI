from collections.abc import Iterable

from app.clinical_engine.context_builder import (
    AllergyContext,
    MedicationContext,
    normalize_term,
)
from app.clinical_engine.result import AssessmentFinding, FindingCategory, FindingSeverity


def evaluate(
    allergies: Iterable[AllergyContext], proposed_medications: Iterable[MedicationContext]
) -> list[AssessmentFinding]:
    findings: list[AssessmentFinding] = []
    for allergy in allergies:
        if allergy.status != "ACTIVE":
            continue
        for medication in proposed_medications:
            allergen = normalize_term(allergy.allergen)
            if allergen not in {
                normalize_term(value)
                for value in medication.aliases + (medication.name, medication.brand_name or "")
            }:
                continue
            findings.append(
                AssessmentFinding(
                    finding_id=f"allergy:record:{allergen}:{normalize_term(medication.name)}",
                    category=FindingCategory.ALLERGY,
                    severity=FindingSeverity.CRITICAL
                    if normalize_term(allergy.severity) in {"severe", "life threatening"}
                    else FindingSeverity.HIGH,
                    classification="AVOID",
                    summary=f"Allergy conflict: {medication.name}",
                    details=(
                        f"The patient has a recorded allergy to {allergy.allergen}. "
                        f"Recorded reaction: {allergy.reaction or 'not specified'}."
                    ),
                    medications=(medication.name,),
                    actionable=True,
                    metadata={"allergen": allergy.allergen, "severity": allergy.severity},
                )
            )
    return findings


__all__ = ["evaluate"]
