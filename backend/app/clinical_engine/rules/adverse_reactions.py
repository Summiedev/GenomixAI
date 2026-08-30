from collections.abc import Iterable

from app.clinical_engine.context_builder import (
    AdverseDrugReactionContext,
    MedicationContext,
    medication_matches,
    normalize_term,
)
from app.clinical_engine.result import AssessmentFinding, FindingCategory, FindingSeverity


def evaluate(
    reactions: Iterable[AdverseDrugReactionContext],
    proposed_medications: Iterable[MedicationContext],
) -> list[AssessmentFinding]:
    findings: list[AssessmentFinding] = []
    for reaction in reactions:
        if reaction.status != "ACTIVE":
            continue
        for medication in proposed_medications:
            if not medication_matches(medication, reaction.medication):
                continue
            findings.append(
                AssessmentFinding(
                    finding_id=f"adr:record:{normalize_term(reaction.medication)}:{normalize_term(medication.name)}",
                    category=FindingCategory.ADVERSE_DRUG_REACTION,
                    severity=FindingSeverity.HIGH,
                    classification="AVOID",
                    summary=f"Previous adverse reaction: {medication.name}",
                    details=(
                        f"The patient has a recorded adverse reaction to {reaction.medication}: "
                        f"{reaction.reaction}."
                    ),
                    medications=(medication.name,),
                    actionable=True,
                    metadata={"reaction": reaction.reaction, "severity": reaction.severity},
                )
            )
    return findings


__all__ = ["evaluate"]
