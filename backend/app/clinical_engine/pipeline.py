"""The deterministic assessment pipeline. It has no FastAPI dependency."""

import logging
from collections.abc import Iterable, Sequence
from typing import Any

from app.clinical_engine.context_builder import (
    MedicationContext,
    PatientClinicalContext,
    normalize_context,
)
from app.clinical_engine.ml.predictor import NullPredictor, Predictor
from app.clinical_engine.result import (
    AssessmentFinding,
    AssessmentResult,
    FindingCategory,
    FindingSeverity,
)
from app.clinical_engine.rules import (
    adverse_reactions,
    allergies,
    clinical_factors,
    contraindications,
    dosing,
    interactions,
    pharmacogenomics,
)

logger = logging.getLogger(__name__)


class ClinicalAssessmentPipeline:
    """Evaluate a patient context against explicit, provenance-backed rules."""

    def __init__(
        self,
        *,
        pharmacogenomic_rules: Sequence[Any] = (),
        interaction_rules: Sequence[Any] = (),
        contraindication_rules: Sequence[Any] = (),
        dose_rules: Sequence[Any] = (),
        monitoring_rules: Sequence[Any] = (),
        predictor: Predictor | None = None,
    ) -> None:
        self.pharmacogenomic_rules = tuple(pharmacogenomic_rules)
        self.interaction_rules = tuple(interaction_rules)
        self.contraindication_rules = tuple(contraindication_rules)
        self.dose_rules = tuple(dose_rules)
        self.monitoring_rules = tuple(monitoring_rules)
        self.predictor = predictor or NullPredictor()

    def assess(
        self,
        context: PatientClinicalContext,
        proposed_medications: Iterable[MedicationContext],
    ) -> AssessmentResult:
        normalized_context = normalize_context(context)
        proposed = tuple(proposed_medications)
        findings: list[AssessmentFinding] = []
        findings.extend(
            pharmacogenomics.evaluate(
                normalized_context.genomic_findings, proposed, self.pharmacogenomic_rules
            )
        )
        recommendations = pharmacogenomics.evaluate_alternatives(
            normalized_context,
            normalized_context.genomic_findings,
            proposed,
            self.pharmacogenomic_rules,
            self.contraindication_rules,
        )
        findings.extend(
            interactions.evaluate(normalized_context.medications, proposed, self.interaction_rules)
        )
        findings.extend(allergies.evaluate(normalized_context.allergies, proposed))
        findings.extend(
            adverse_reactions.evaluate(normalized_context.adverse_drug_reactions, proposed)
        )
        findings.extend(
            contraindications.evaluate(normalized_context, proposed, self.contraindication_rules)
        )
        findings.extend(
            clinical_factors.evaluate(normalized_context, proposed, self.monitoring_rules)
        )
        findings.extend(dosing.evaluate(normalized_context.medications, proposed, self.dose_rules))
        try:
            prediction = self.predictor.predict(normalized_context, proposed)
        except Exception as exc:  # ML is optional; deterministic rules must still complete.
            logger.warning("Optional ML predictor failed: %s", type(exc).__name__)
            prediction = None
        if prediction is not None:
            prediction_metadata = dict(prediction.metadata or {})
            for key in (
                "model_name",
                "model_version",
                "feature_schema_version",
                "probability",
                "calibration_metadata",
                "explanation_metadata",
            ):
                value = getattr(prediction, key)
                if value is not None:
                    prediction_metadata[key] = value
            prediction_metadata["timestamp"] = prediction.timestamp.isoformat()
            findings.append(
                AssessmentFinding(
                    finding_id=f"ml:{prediction.label}",
                    category=FindingCategory.ML,
                    severity=FindingSeverity.UNKNOWN,
                    classification="INFORMATIONAL",
                    summary=prediction.label,
                    details=prediction.explanation or "An optional model returned a prediction.",
                    actionable=False,
                    metadata=prediction_metadata,
                )
            )
        findings = list({finding.finding_id: finding for finding in findings}.values())
        findings.sort(key=_finding_sort_key)
        return AssessmentResult(
            findings=tuple(findings),
            recommendations=tuple(recommendations),
            overall_classification=_overall_classification(findings),
        )


def _finding_sort_key(finding: AssessmentFinding) -> tuple[str, str, str]:
    return (finding.category.value, finding.severity.value, finding.finding_id)


def _overall_classification(findings: Iterable[AssessmentFinding]) -> str:
    findings = tuple(findings)
    if any(finding.severity is FindingSeverity.CRITICAL for finding in findings):
        return "CRITICAL"
    if any(finding.severity is FindingSeverity.HIGH for finding in findings):
        return "HIGH"
    if any(finding.actionable for finding in findings):
        return "REVIEW"
    return "NO_ACTION"


AssessmentPipeline = ClinicalAssessmentPipeline
AssessmentEngine = ClinicalAssessmentPipeline

__all__ = ["AssessmentEngine", "AssessmentPipeline", "ClinicalAssessmentPipeline"]
