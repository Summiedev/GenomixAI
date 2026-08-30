from collections.abc import Iterable
from typing import Any

from app.clinical_engine.context_builder import (
    GenomicFindingContext,
    MedicationContext,
    PatientClinicalContext,
    normalize_term,
)
from app.clinical_engine.result import (
    AlternativeRecommendation,
    AssessmentFinding,
    FindingCategory,
    FindingSeverity,
    evidence_from_rule,
)
from app.clinical_engine.rules import contraindications
from app.clinical_engine.rules.common import (
    finding,
    is_active,
    medication_from_rule,
    rule_matches_medication,
)


def evaluate(
    genomic_findings: Iterable[GenomicFindingContext],
    proposed_medications: Iterable[MedicationContext],
    rules: Iterable[Any],
) -> list[AssessmentFinding]:
    findings: list[AssessmentFinding] = []
    genomic = tuple(genomic_findings)
    for medication in proposed_medications:
        for rule in rules:
            if not is_active(rule) or not rule_matches_medication(rule, medication):
                continue
            matching_gene = [
                result
                for result in genomic
                if normalize_term(result.gene) == normalize_term(rule.gene)
            ]
            if not matching_gene:
                continue
            for result in matching_gene:
                phenotype_condition = normalize_term(getattr(rule, "phenotype_condition", ""))
                genotype_condition = normalize_term(getattr(rule, "genotype_condition", ""))
                phenotype = normalize_term(result.phenotype)
                genotype = normalize_term(result.genotype)
                if not phenotype and not genotype:
                    findings.append(
                        finding(
                            category=FindingCategory.PHARMACOGENOMICS,
                            rule=rule,
                            summary=f"{medication.name}: phenotype is not interpretable",
                            details=(
                                "A relevant gene was reported, but the finding has no "
                                "phenotype or genotype that matches this rule. No "
                                "recommendation was inferred."
                            ),
                            medications=(medication.name,),
                            actionable=False,
                            severity=FindingSeverity.UNKNOWN,
                            metadata={"gene": result.gene, "reason": "UNKNOWN_PHENOTYPE"},
                        )
                    )
                    continue
                if phenotype_condition and phenotype != phenotype_condition:
                    continue
                if genotype_condition and genotype != genotype_condition:
                    continue
                findings.append(
                    finding(
                        category=FindingCategory.PHARMACOGENOMICS,
                        rule=rule,
                        summary=f"{medication.name}: {result.gene} finding matches",
                        details=(
                            f"{rule.clinical_implication} "
                            f"Recommendation: {rule.recommendation_text}"
                        ),
                        medications=(medication.name,),
                        metadata={
                            "gene": result.gene,
                            "phenotype": result.phenotype,
                            "genotype": result.genotype,
                            "profile_id": result.profile_id,
                        },
                    )
                )
    return findings


def evaluate_alternatives(
    context: PatientClinicalContext,
    genomic_findings: Iterable[GenomicFindingContext],
    proposed_medications: Iterable[MedicationContext],
    rules: Iterable[Any],
    contraindication_rules: Iterable[Any] = (),
) -> list[AlternativeRecommendation]:
    recommendations: list[AlternativeRecommendation] = []
    genomic = tuple(genomic_findings)
    for medication in proposed_medications:
        for rule in rules:
            if not is_active(rule) or not rule_matches_medication(rule, medication):
                continue
            if not any(
                normalize_term(result.gene) == normalize_term(rule.gene)
                and (
                    not getattr(rule, "phenotype_condition", None)
                    or normalize_term(result.phenotype) == normalize_term(rule.phenotype_condition)
                )
                and (
                    not getattr(rule, "genotype_condition", None)
                    or normalize_term(result.genotype) == normalize_term(rule.genotype_condition)
                )
                for result in genomic
            ):
                continue
            for alternative in getattr(rule, "alternatives", ()):
                evidence = evidence_from_rule(alternative)
                if not evidence:
                    continue
                alternative_medication = medication_from_rule(alternative, "alternative_medication")
                contraindication_findings = contraindications.evaluate(
                    context, [alternative_medication], contraindication_rules
                )
                classification_value = _value(getattr(alternative, "classification", ""))
                limitations = getattr(alternative, "important_limitations", None)
                contraindication_text = tuple(
                    finding.summary for finding in contraindication_findings
                )
                if contraindication_findings:
                    classification_value = "SPECIALIST_REVIEW_REQUIRED"
                    limitations = _append_limitation(
                        limitations,
                        "A patient-specific contraindication or caution was detected; "
                        "specialist review is required.",
                    )
                recommendations.append(
                    AlternativeRecommendation(
                        medication_id=alternative_medication.medication_id,
                        medication=alternative_medication.name,
                        classification=classification_value,
                        clinical_rationale=alternative.clinical_rationale,
                        patient_specific_rationale=getattr(
                            alternative, "patient_specific_rationale", None
                        ),
                        important_limitations=limitations,
                        contraindications=contraindication_text,
                        evidence=evidence,
                        trigger_medication_id=medication.medication_id,
                        trigger_medication=medication.name,
                    )
                )
    return recommendations


def _append_limitation(current: str | None, addition: str) -> str:
    return f"{current} {addition}".strip() if current else addition


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


__all__ = ["evaluate", "evaluate_alternatives"]
