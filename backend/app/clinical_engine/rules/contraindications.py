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
            target_type = _value(getattr(rule, "target_type", ""))
            target_value = normalize_term(getattr(rule, "target_value", ""))
            matches = _matches_target(context, target_type, target_value, rule)
            if matches:
                findings.append(
                    finding(
                        category=FindingCategory.CONTRAINDICATION,
                        rule=rule,
                        summary=f"Contraindication check: {medication.name}",
                        details=(
                            f"{rule.clinical_implication} "
                            f"Recommendation: {rule.recommendation_text}"
                        ),
                        medications=(medication.name,),
                        metadata={"target_type": target_type, "target_value": target_value},
                    )
                )
    return findings


def _matches_target(
    context: PatientClinicalContext, target_type: str, target_value: str, rule: Any
) -> bool:
    operator = _value(getattr(rule, "operator", "EQUALS"))
    values: list[str] = []
    if target_type == "CONDITION":
        values = [
            condition.name for condition in context.conditions if condition.status == "ACTIVE"
        ]
    elif target_type == "ALLERGY":
        values = [allergy.allergen for allergy in context.allergies if allergy.status == "ACTIVE"]
    elif target_type == "DEMOGRAPHIC":
        key, _, expected = target_value.partition(":")
        return _compare(context.demographics.get(key), expected, operator)
    elif target_type == "MEDICATION":
        values = [
            medication.name for medication in context.medications if medication.status == "ACTIVE"
        ]
    elif target_type == "LAB":
        return _matches_numeric(context.labs, target_value, rule)
    elif target_type == "VITAL":
        return _matches_numeric(context.vitals, target_value, rule)
    return any(_compare(value, target_value, operator) for value in values)


def _matches_numeric(records: Iterable[Any], target_value: str, rule: Any) -> bool:
    operator = _value(getattr(rule, "operator", "EQUALS"))
    threshold = getattr(rule, "threshold", None)
    for record in records:
        name = normalize_term(getattr(record, "test_name", getattr(record, "vital_type", "")))
        if name != target_value or threshold is None:
            continue
        return _compare(
            getattr(record, "numeric_value", getattr(record, "value", None)), threshold, operator
        )
    return False


def _compare(actual: Any, expected: Any, operator: str) -> bool:
    if actual is None:
        return False
    if operator == "CONTAINS":
        return normalize_term(expected) in normalize_term(actual)
    try:
        left, right = float(actual), float(expected)
    except (TypeError, ValueError):
        return normalize_term(actual) == normalize_term(expected)
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
