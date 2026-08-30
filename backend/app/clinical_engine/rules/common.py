from enum import StrEnum
from typing import Any

from app.clinical_engine.context_builder import (
    MedicationContext,
    medication_matches,
    normalize_term,
)
from app.clinical_engine.result import (
    AssessmentFinding,
    FindingCategory,
    FindingSeverity,
    evidence_from_rule,
)


def is_active(rule: Any) -> bool:
    status = getattr(rule, "status", None)
    return status is None or _value(status) == "ACTIVE"


def _value(value: Any) -> str:
    return value.value if isinstance(value, StrEnum) else str(value)


def classification(rule: Any) -> str:
    return _value(getattr(rule, "recommendation_classification", "INFORMATIONAL"))


def severity_for(classification_value: str) -> FindingSeverity:
    return {
        "AVOID": FindingSeverity.HIGH,
        "ALTERNATIVE": FindingSeverity.HIGH,
        "CONSIDER": FindingSeverity.MODERATE,
        "MONITOR": FindingSeverity.MODERATE,
        "INSUFFICIENT_EVIDENCE": FindingSeverity.UNKNOWN,
    }.get(classification_value, FindingSeverity.INFO)


def medication_from_rule(rule: Any, attribute: str = "medication") -> MedicationContext:
    medication = getattr(rule, attribute, None)
    if medication is not None:
        return MedicationContext(
            name=getattr(medication, "generic_name", getattr(medication, "name", "")),
            medication_id=str(getattr(medication, "id", "")) or None,
            standardized_code=getattr(medication, "standardized_code", None),
            brand_name=getattr(medication, "brand_name", None),
        )
    return MedicationContext(
        name=getattr(rule, f"{attribute}_name", ""),
        medication_id=str(getattr(rule, f"{attribute}_id", "")) or None,
    )


def rule_matches_medication(
    rule: Any, medication: MedicationContext, attribute: str = "medication"
) -> bool:
    return medication_matches(medication, medication_from_rule(rule, attribute))


def finding(
    *,
    category: FindingCategory,
    rule: Any,
    summary: str,
    details: str,
    medications: tuple[str, ...] = (),
    actionable: bool = True,
    metadata: dict[str, Any] | None = None,
    severity: FindingSeverity | None = None,
) -> AssessmentFinding:
    rule_id = str(getattr(rule, "id", "")) or None
    evidence = evidence_from_rule(rule)
    has_rule_fields = hasattr(rule, "recommendation_text") or hasattr(rule, "evidence_level")
    no_provenance = has_rule_fields and not evidence
    resolved_classification = "INSUFFICIENT_EVIDENCE" if no_provenance else classification(rule)
    return AssessmentFinding(
        finding_id=f"{category.value.lower()}:{rule_id or 'record'}:{normalize_term(summary)}",
        category=category,
        severity=severity
        or (FindingSeverity.UNKNOWN if no_provenance else severity_for(resolved_classification)),
        classification=resolved_classification,
        summary=summary,
        details=details,
        medications=medications,
        rule_id=rule_id,
        evidence=evidence,
        actionable=actionable and not no_provenance,
        metadata=metadata or {},
    )


__all__ = [
    "classification",
    "finding",
    "is_active",
    "medication_from_rule",
    "rule_matches_medication",
    "severity_for",
]
