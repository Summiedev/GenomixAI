from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.medication import Medication


class KnowledgeStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class EvidenceLevel(StrEnum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    LIMITED = "LIMITED"
    INSUFFICIENT = "INSUFFICIENT"


class RecommendationClassification(StrEnum):
    AVOID = "AVOID"
    ALTERNATIVE = "ALTERNATIVE"
    CONSIDER = "CONSIDER"
    MONITOR = "MONITOR"
    INFORMATIONAL = "INFORMATIONAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class AlternativeClassification(StrEnum):
    GUIDELINE_SUPPORTED_ALTERNATIVE = "GUIDELINE_SUPPORTED_ALTERNATIVE"
    POTENTIAL_ALTERNATIVE = "POTENTIAL_ALTERNATIVE"
    SPECIALIST_REVIEW_REQUIRED = "SPECIALIST_REVIEW_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceSourceType(StrEnum):
    CLINICAL_GUIDELINE = "CLINICAL_GUIDELINE"
    REGULATORY_LABEL = "REGULATORY_LABEL"
    PEER_REVIEWED = "PEER_REVIEWED"
    RESEARCH_DATASET = "RESEARCH_DATASET"


class RuleConditionType(StrEnum):
    CONDITION = "CONDITION"
    MEDICATION = "MEDICATION"
    ALLERGY = "ALLERGY"
    LAB = "LAB"
    VITAL = "VITAL"
    DEMOGRAPHIC = "DEMOGRAPHIC"


class ComparisonOperator(StrEnum):
    EQUALS = "EQUALS"
    CONTAINS = "CONTAINS"
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"


class EvidenceSource(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "evidence_sources"
    __table_args__ = (Index("ix_evidence_source_organization_title", "organization", "title"),)

    organization: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[EvidenceSourceType] = mapped_column(
        SQLEnum(EvidenceSourceType, name="evidence_source_type_enum"), nullable=False
    )
    source_version: Mapped[str | None] = mapped_column(String(150), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    reference_identifier: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[KnowledgeStatus] = mapped_column(
        SQLEnum(KnowledgeStatus, name="knowledge_status_enum"),
        default=KnowledgeStatus.ACTIVE,
        server_default=KnowledgeStatus.ACTIVE.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PharmacogenomicRule(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pharmacogenomic_rules"
    __table_args__ = (
        Index("ix_pgx_rule_medication_gene_status", "medication_id", "gene", "status"),
    )

    medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    gene: Mapped[str] = mapped_column(String(50), nullable=False)
    phenotype_condition: Mapped[str | None] = mapped_column(String(150), nullable=True)
    genotype_condition: Mapped[str | None] = mapped_column(String(150), nullable=True)
    clinical_implication: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_classification: Mapped[RecommendationClassification] = mapped_column(
        SQLEnum(RecommendationClassification, name="recommendation_classification_enum"),
        nullable=False,
    )
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_level: Mapped[EvidenceLevel] = mapped_column(
        SQLEnum(EvidenceLevel, name="evidence_level_enum"), nullable=False
    )
    evidence_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT"), nullable=False
    )
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[KnowledgeStatus] = mapped_column(
        SQLEnum(KnowledgeStatus, name="knowledge_status_enum"),
        default=KnowledgeStatus.ACTIVE,
        server_default=KnowledgeStatus.ACTIVE.value,
        nullable=False,
    )

    medication: Mapped["Medication"] = relationship()
    evidence_source: Mapped[EvidenceSource] = relationship()
    alternatives: Mapped[list["PharmacogenomicRuleAlternative"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )


class PharmacogenomicRuleAlternative(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pharmacogenomic_rule_alternatives"

    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("pharmacogenomic_rules.id", ondelete="CASCADE"), nullable=False
    )
    alternative_medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    classification: Mapped[AlternativeClassification] = mapped_column(
        SQLEnum(AlternativeClassification, name="alternative_classification_enum"),
        nullable=False,
    )
    clinical_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    patient_specific_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    important_limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT"), nullable=False
    )

    rule: Mapped[PharmacogenomicRule] = relationship(back_populates="alternatives")
    alternative_medication: Mapped["Medication"] = relationship()
    evidence_source: Mapped[EvidenceSource] = relationship()


class DrugDrugInteraction(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "drug_drug_interactions"
    __table_args__ = (
        Index(
            "ix_ddi_medication_pair_status", "medication_id", "interacting_medication_id", "status"
        ),
    )

    medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    interacting_medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    clinical_effect: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_classification: Mapped[RecommendationClassification] = mapped_column(
        SQLEnum(RecommendationClassification, name="recommendation_classification_enum"),
        nullable=False,
    )
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_level: Mapped[EvidenceLevel] = mapped_column(
        SQLEnum(EvidenceLevel, name="evidence_level_enum"), nullable=False
    )
    evidence_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT"), nullable=False
    )
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[KnowledgeStatus] = mapped_column(
        SQLEnum(KnowledgeStatus, name="knowledge_status_enum"),
        default=KnowledgeStatus.ACTIVE,
        server_default=KnowledgeStatus.ACTIVE.value,
        nullable=False,
    )

    medication: Mapped["Medication"] = relationship(foreign_keys=[medication_id])
    interacting_medication: Mapped["Medication"] = relationship(
        foreign_keys=[interacting_medication_id]
    )
    evidence_source: Mapped[EvidenceSource] = relationship()


class ContraindicationRule(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "contraindication_rules"
    __table_args__ = (
        Index(
            "ix_contraindication_rule_medication_target", "medication_id", "target_type", "status"
        ),
    )

    medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    target_type: Mapped[RuleConditionType] = mapped_column(
        SQLEnum(RuleConditionType, name="rule_condition_type_enum"), nullable=False
    )
    target_value: Mapped[str] = mapped_column(String(200), nullable=False)
    operator: Mapped[ComparisonOperator] = mapped_column(
        SQLEnum(ComparisonOperator, name="comparison_operator_enum"),
        default=ComparisonOperator.EQUALS,
        server_default=ComparisonOperator.EQUALS.value,
        nullable=False,
    )
    clinical_implication: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_classification: Mapped[RecommendationClassification] = mapped_column(
        SQLEnum(RecommendationClassification, name="recommendation_classification_enum"),
        nullable=False,
    )
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_level: Mapped[EvidenceLevel] = mapped_column(
        SQLEnum(EvidenceLevel, name="evidence_level_enum"), nullable=False
    )
    evidence_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT"), nullable=False
    )
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[KnowledgeStatus] = mapped_column(
        SQLEnum(KnowledgeStatus, name="knowledge_status_enum"),
        default=KnowledgeStatus.ACTIVE,
        server_default=KnowledgeStatus.ACTIVE.value,
        nullable=False,
    )

    medication: Mapped["Medication"] = relationship()
    evidence_source: Mapped[EvidenceSource] = relationship()


class DoseRule(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "dose_rules"
    __table_args__ = (
        Index("ix_dose_rule_medication_factor", "medication_id", "factor_value", "status"),
    )

    medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    factor_type: Mapped[RuleConditionType] = mapped_column(
        SQLEnum(RuleConditionType, name="rule_condition_type_enum"), nullable=False
    )
    factor_value: Mapped[str] = mapped_column(String(200), nullable=False)
    operator: Mapped[ComparisonOperator] = mapped_column(
        SQLEnum(ComparisonOperator, name="comparison_operator_enum"), nullable=False
    )
    maximum_dose: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    minimum_dose: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    dose_unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    clinical_implication: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_classification: Mapped[RecommendationClassification] = mapped_column(
        SQLEnum(RecommendationClassification, name="recommendation_classification_enum"),
        nullable=False,
    )
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_level: Mapped[EvidenceLevel] = mapped_column(
        SQLEnum(EvidenceLevel, name="evidence_level_enum"), nullable=False
    )
    evidence_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT"), nullable=False
    )
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[KnowledgeStatus] = mapped_column(
        SQLEnum(KnowledgeStatus, name="knowledge_status_enum"),
        default=KnowledgeStatus.ACTIVE,
        server_default=KnowledgeStatus.ACTIVE.value,
        nullable=False,
    )

    medication: Mapped["Medication"] = relationship()
    evidence_source: Mapped[EvidenceSource] = relationship()


class MonitoringRule(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "monitoring_rules"
    __table_args__ = (
        Index("ix_monitoring_rule_medication_factor", "medication_id", "factor_value", "status"),
    )

    medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    factor_type: Mapped[RuleConditionType] = mapped_column(
        SQLEnum(RuleConditionType, name="rule_condition_type_enum"), nullable=False
    )
    factor_value: Mapped[str] = mapped_column(String(200), nullable=False)
    operator: Mapped[ComparisonOperator] = mapped_column(
        SQLEnum(ComparisonOperator, name="comparison_operator_enum"), nullable=False
    )
    threshold: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    clinical_implication: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_classification: Mapped[RecommendationClassification] = mapped_column(
        SQLEnum(RecommendationClassification, name="recommendation_classification_enum"),
        nullable=False,
    )
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_level: Mapped[EvidenceLevel] = mapped_column(
        SQLEnum(EvidenceLevel, name="evidence_level_enum"), nullable=False
    )
    evidence_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT"), nullable=False
    )
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[KnowledgeStatus] = mapped_column(
        SQLEnum(KnowledgeStatus, name="knowledge_status_enum"),
        default=KnowledgeStatus.ACTIVE,
        server_default=KnowledgeStatus.ACTIVE.value,
        nullable=False,
    )

    medication: Mapped["Medication"] = relationship()
    evidence_source: Mapped[EvidenceSource] = relationship()


__all__ = [
    "ComparisonOperator",
    "AlternativeClassification",
    "ContraindicationRule",
    "DoseRule",
    "DrugDrugInteraction",
    "EvidenceLevel",
    "EvidenceSource",
    "EvidenceSourceType",
    "KnowledgeStatus",
    "MonitoringRule",
    "PharmacogenomicRule",
    "PharmacogenomicRuleAlternative",
    "RecommendationClassification",
    "RuleConditionType",
]
