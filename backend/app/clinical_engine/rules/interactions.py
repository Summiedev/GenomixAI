from collections.abc import Iterable
from typing import Any

from app.clinical_engine.context_builder import MedicationContext
from app.clinical_engine.result import AssessmentFinding, FindingCategory
from app.clinical_engine.rules.common import finding, is_active, rule_matches_medication


def evaluate(
    existing_medications: Iterable[MedicationContext],
    proposed_medications: Iterable[MedicationContext],
    rules: Iterable[Any],
) -> list[AssessmentFinding]:
    findings: list[AssessmentFinding] = []
    existing = tuple(existing_medications)
    proposed = tuple(proposed_medications)
    pairs = [
        (medication, candidate, "EXISTING_VS_PROPOSED")
        for medication in existing
        for candidate in proposed
    ]
    pairs.extend(
        (left, right, "PROPOSED_VS_PROPOSED")
        for index, left in enumerate(proposed)
        for right in proposed[index + 1 :]
    )
    seen: set[tuple[str, str, str]] = set()
    for left, right, pair_type in pairs:
        pair_key = (
            min(left.name.casefold(), right.name.casefold()),
            max(left.name.casefold(), right.name.casefold()),
            pair_type,
        )
        if pair_key in seen:
            continue
        seen.add(pair_key)
        for rule in rules:
            if not is_active(rule):
                continue
            matches = (
                rule_matches_medication(rule, left)
                and rule_matches_medication(rule, right, "interacting_medication")
            ) or (
                rule_matches_medication(rule, right)
                and rule_matches_medication(rule, left, "interacting_medication")
            )
            if not matches:
                continue
            findings.append(
                finding(
                    category=FindingCategory.DRUG_INTERACTION,
                    rule=rule,
                    summary=f"Interaction: {left.name} + {right.name}",
                    details=f"{rule.clinical_effect} Recommendation: {rule.recommendation_text}",
                    medications=(left.name, right.name),
                    metadata={"pair_type": pair_type},
                )
            )
    return findings


__all__ = ["evaluate"]
