from collections.abc import Iterable
from typing import Any

from app.clinical_engine.context_builder import (
    MedicationContext,
    PatientClinicalContext,
    normalize_term,
)
from app.clinical_engine.result import AssessmentFinding, FindingCategory
from app.clinical_engine.rules.common import finding, is_active, rule_matches_medication


def evaluate(
    context: PatientClinicalContext,
    proposed_medications: Iterable[MedicationContext],
    rules: Iterable[Any],
) -> list[AssessmentFinding]:
    findings: list[AssessmentFinding] = []
    for medication in proposed_medications:
        for rule in rules:
            if not is_active(rule) or not rule_matches_medication(rule, medication):
                continue
            factor_type = _value(getattr(rule, "factor_type", ""))
            factor_value = normalize_term(getattr(rule, "factor_value", ""))
            records = {
                "CONDITION": context.conditions,
                "LAB": context.labs,
                "VITAL": context.vitals,
                "DEMOGRAPHIC": (),
            }.get(factor_type, ())
            for record in records:
                if getattr(record, "status", "ACTIVE") != "ACTIVE":
                    continue
                record_name = normalize_term(
                    getattr(
                        record,
                        "name",
                        getattr(record, "test_name", getattr(record, "vital_type", "")),
                    )
                )
                if record_name != factor_value or not _matches(record, rule):
                    continue
                findings.append(
                    finding(
                        category=FindingCategory.MONITORING,
                        rule=rule,
                        summary=f"Clinical factor relevant to {medication.name}",
                        details=(
                            f"{rule.clinical_implication} "
                            f"Recommendation: {rule.recommendation_text}"
                        ),
                        medications=(medication.name,),
                        metadata={"factor_type": factor_type, "factor_value": factor_value},
                    )
                )
    return findings


def _matches(record: Any, rule: Any) -> bool:
    actual = getattr(record, "numeric_value", getattr(record, "value", None))
    threshold = getattr(rule, "threshold", None)
    if threshold is None:
        return bool(getattr(record, "abnormal", False))
    try:
        left, right = float(actual), float(threshold)
    except (TypeError, ValueError):
        return False
    operator = _value(getattr(rule, "operator", "EQUALS"))
    return {
        "EQUALS": left == right,
        "GREATER_THAN": left > right,
        "GREATER_THAN_OR_EQUAL": left >= right,
        "LESS_THAN": left < right,
        "LESS_THAN_OR_EQUAL": left <= right,
    }.get(operator, False)


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


__all__ = ["evaluate"]
