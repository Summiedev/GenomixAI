from collections.abc import Iterable
from typing import Any

from app.clinical_engine.context_builder import MedicationContext
from app.clinical_engine.result import AssessmentFinding, FindingCategory
from app.clinical_engine.rules.common import (
    finding,
    is_active,
    medication_matches,
    rule_matches_medication,
)


def evaluate(
    context_medications: Iterable[MedicationContext],
    proposed_medications: Iterable[MedicationContext],
    rules: Iterable[Any],
) -> list[AssessmentFinding]:
    existing = tuple(context_medications)
    proposed = tuple(proposed_medications)
    findings: list[AssessmentFinding] = []
    for medication in proposed:
        for rule in rules:
            if not is_active(rule) or not rule_matches_medication(rule, medication):
                continue
            if not _factor_matches(rule, existing):
                continue
            if not _dose_outside_rule(medication, rule):
                continue
            findings.append(
                finding(
                    category=FindingCategory.DOSE,
                    rule=rule,
                    summary=f"Dose consideration: {medication.name}",
                    details=(
                        f"{rule.clinical_implication} Recommendation: {rule.recommendation_text}"
                    ),
                    medications=(medication.name,),
                    metadata={"dose": medication.dose, "dose_unit": medication.dose_unit},
                )
            )
    return findings


def _factor_matches(rule: Any, existing: tuple[MedicationContext, ...]) -> bool:
    factor_type = _value(getattr(rule, "factor_type", ""))
    if factor_type != "MEDICATION":
        return True
    factor_value = getattr(rule, "factor_value", "")
    return any(medication_matches(medication, factor_value) for medication in existing)


def _dose_outside_rule(medication: MedicationContext, rule: Any) -> bool:
    if medication.dose is None:
        return False
    if (
        getattr(rule, "dose_unit", None)
        and medication.dose_unit
        and rule.dose_unit.casefold() != medication.dose_unit.casefold()
    ):
        return False
    dose = float(medication.dose)
    maximum = getattr(rule, "maximum_dose", None)
    minimum = getattr(rule, "minimum_dose", None)
    return (maximum is not None and dose > float(maximum)) or (
        minimum is not None and dose < float(minimum)
    )


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


__all__ = ["evaluate"]
