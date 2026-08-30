"""Structured assessment findings and provenance attachments."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class FindingCategory(StrEnum):
    PHARMACOGENOMICS = "PHARMACOGENOMICS"
    DRUG_INTERACTION = "DRUG_INTERACTION"
    ALLERGY = "ALLERGY"
    ADVERSE_DRUG_REACTION = "ADVERSE_DRUG_REACTION"
    CONTRAINDICATION = "CONTRAINDICATION"
    CLINICAL_FACTOR = "CLINICAL_FACTOR"
    DOSE = "DOSE"
    MONITORING = "MONITORING"
    ML = "ML"


class FindingSeverity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EvidenceAttachment:
    source_id: str | None
    organization: str
    title: str
    source_type: str | None = None
    source_version: str | None = None
    effective_date: date | None = None
    review_date: date | None = None
    source_url: str | None = None
    reference_identifier: str | None = None
    evidence_level: str | None = None


@dataclass(frozen=True)
class AssessmentFinding:
    finding_id: str
    category: FindingCategory
    severity: FindingSeverity
    classification: str
    summary: str
    details: str
    medications: tuple[str, ...] = ()
    rule_id: str | None = None
    evidence: tuple[EvidenceAttachment, ...] = ()
    actionable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AlternativeRecommendation:
    medication_id: str | None
    medication: str
    classification: str
    clinical_rationale: str
    patient_specific_rationale: str | None
    important_limitations: str | None
    contraindications: tuple[str, ...] = ()
    evidence: tuple[EvidenceAttachment, ...] = ()
    trigger_medication_id: str | None = None
    trigger_medication: str | None = None


@dataclass(frozen=True)
class AssessmentResult:
    findings: tuple[AssessmentFinding, ...] = ()
    recommendations: tuple[AlternativeRecommendation, ...] = ()
    overall_classification: str = "NO_ACTION"

    @property
    def has_actionable_findings(self) -> bool:
        return any(finding.actionable for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_classification": self.overall_classification,
            "has_actionable_findings": self.has_actionable_findings,
            "recommendations": [
                {
                    "medication_id": recommendation.medication_id,
                    "medication": recommendation.medication,
                    "classification": recommendation.classification,
                    "clinical_rationale": recommendation.clinical_rationale,
                    "patient_specific_rationale": recommendation.patient_specific_rationale,
                    "important_limitations": recommendation.important_limitations,
                    "contraindications": list(recommendation.contraindications),
                    "trigger_medication_id": recommendation.trigger_medication_id,
                    "trigger_medication": recommendation.trigger_medication,
                    "evidence": [
                        {
                            **attachment.__dict__,
                            "effective_date": _date_value(attachment.effective_date),
                            "review_date": _date_value(attachment.review_date),
                        }
                        for attachment in recommendation.evidence
                    ],
                }
                for recommendation in self.recommendations
            ],
            "findings": [
                {
                    "finding_id": finding.finding_id,
                    "category": finding.category.value,
                    "severity": finding.severity.value,
                    "classification": finding.classification,
                    "summary": finding.summary,
                    "details": finding.details,
                    "medications": list(finding.medications),
                    "rule_id": finding.rule_id,
                    "actionable": finding.actionable,
                    "metadata": finding.metadata,
                    "evidence": [
                        {
                            **attachment.__dict__,
                            "source_id": attachment.source_id,
                            "effective_date": _date_value(attachment.effective_date),
                            "review_date": _date_value(attachment.review_date),
                        }
                        for attachment in finding.evidence
                    ],
                }
                for finding in self.findings
            ],
        }


def _date_value(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def evidence_from_rule(rule: Any) -> tuple[EvidenceAttachment, ...]:
    source = getattr(rule, "evidence_source", None)
    if source is None:
        return ()
    return (
        EvidenceAttachment(
            source_id=str(getattr(source, "id", "")) or None,
            organization=source.organization,
            title=source.title,
            source_type=_value(getattr(source, "source_type", None)),
            source_version=source.source_version,
            effective_date=source.effective_date,
            review_date=source.review_date,
            source_url=source.source_url,
            reference_identifier=source.reference_identifier,
            evidence_level=_value(getattr(rule, "evidence_level", None)),
        ),
    )


def _value(value: Any) -> str | None:
    return value.value if isinstance(value, StrEnum) else (str(value) if value else None)


__all__ = [
    "AssessmentFinding",
    "AlternativeRecommendation",
    "AssessmentResult",
    "EvidenceAttachment",
    "FindingCategory",
    "FindingSeverity",
    "evidence_from_rule",
]
