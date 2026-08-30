from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.clinical_engine.result import FindingCategory, FindingSeverity
from app.clinical_engine.state_machine import AssessmentState
from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin
from app.models.knowledge import AlternativeClassification

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.knowledge import EvidenceSource
    from app.models.medication import Medication
    from app.models.organization import Organization
    from app.models.patient import Patient


class PharmacistReviewStatus(StrEnum):
    REQUESTED = "REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class ReviewPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class MedicationAssessment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "medication_assessments"
    __table_args__ = (
        Index("ix_assessment_patient_org_created", "patient_id", "organization_id", "created_at"),
        Index("ix_assessment_org_status", "organization_id", "status"),
    )

    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    patient_context_version: Mapped[str] = mapped_column(String(100), nullable=False)
    patient_context_reference: Mapped[str] = mapped_column(String(300), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[AssessmentState] = mapped_column(
        SQLEnum(AssessmentState, name="assessment_state_enum"),
        default=AssessmentState.DRAFT,
        server_default=AssessmentState.DRAFT.value,
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship()
    organization: Mapped["Organization"] = relationship()
    creator: Mapped["User"] = relationship()
    medications: Mapped[list["AssessmentMedication"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentMedication.created_at",
    )
    findings: Mapped[list["AssessmentFinding"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentFinding.created_at",
    )
    recommendations: Mapped[list["AssessmentRecommendation"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentRecommendation.created_at",
    )
    reviews: Mapped[list["PharmacistReview"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="PharmacistReview.created_at",
    )


class AssessmentMedication(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "assessment_medications"
    __table_args__ = (Index("ix_assessment_medication_assessment", "assessment_id"),)

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("medication_assessments.id", ondelete="CASCADE"), nullable=False
    )
    medication_id: Mapped[UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="RESTRICT"), nullable=False
    )
    dose: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dose_unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    route: Mapped[str | None] = mapped_column(String(50), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    indication: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL", server_default="MANUAL"
    )

    assessment: Mapped[MedicationAssessment] = relationship(back_populates="medications")
    medication: Mapped["Medication"] = relationship()


class AssessmentFinding(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "assessment_findings"
    __table_args__ = (
        Index("ix_assessment_finding_assessment_category", "assessment_id", "category"),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("medication_assessments.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[FindingCategory] = mapped_column(
        SQLEnum(FindingCategory, name="assessment_finding_category_enum"), nullable=False
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        SQLEnum(FindingSeverity, name="assessment_finding_severity_enum"), nullable=False
    )
    classification: Mapped[str] = mapped_column(String(80), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    rule_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    medication_references: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    actionable: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )

    assessment: Mapped[MedicationAssessment] = relationship(back_populates="findings")
    evidence: Mapped[list["AssessmentEvidence"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )


class AssessmentRecommendation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "assessment_recommendations"
    __table_args__ = (Index("ix_assessment_recommendation_assessment", "assessment_id"),)

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("medication_assessments.id", ondelete="CASCADE"), nullable=False
    )
    assessment_medication_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assessment_medications.id", ondelete="SET NULL"), nullable=True
    )
    medication_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("medications.id", ondelete="SET NULL"), nullable=True
    )
    medication_name: Mapped[str] = mapped_column(String(200), nullable=False)
    classification: Mapped[AlternativeClassification] = mapped_column(
        SQLEnum(AlternativeClassification, name="alternative_classification_enum"), nullable=False
    )
    clinical_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    patient_specific_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    important_limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    contraindications: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    assessment: Mapped[MedicationAssessment] = relationship(back_populates="recommendations")
    assessment_medication: Mapped[AssessmentMedication | None] = relationship()
    medication: Mapped["Medication | None"] = relationship()
    evidence: Mapped[list["AssessmentEvidence"]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )


class AssessmentEvidence(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "assessment_evidence"
    __table_args__ = (
        CheckConstraint(
            "(finding_id IS NOT NULL) OR (recommendation_id IS NOT NULL)",
            name="ck_assessment_evidence_parent",
        ),
    )

    finding_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assessment_findings.id", ondelete="CASCADE"), nullable=True
    )
    recommendation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assessment_recommendations.id", ondelete="CASCADE"), nullable=True
    )
    evidence_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT"), nullable=False
    )
    source_organization: Mapped[str] = mapped_column(String(200), nullable=False)
    source_title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(150), nullable=True)
    evidence_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    reference_identifier: Mapped[str | None] = mapped_column(String(300), nullable=True)

    finding: Mapped["AssessmentFinding | None"] = relationship(back_populates="evidence")
    recommendation: Mapped["AssessmentRecommendation | None"] = relationship(
        back_populates="evidence"
    )
    evidence_source: Mapped["EvidenceSource"] = relationship()


class PharmacistReview(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pharmacist_reviews"
    __table_args__ = (
        Index("ix_pharmacist_review_org_status", "organization_id", "status"),
        Index("ix_pharmacist_review_assessment", "assessment_id"),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("medication_assessments.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    requested_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_pharmacist_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    priority: Mapped[ReviewPriority] = mapped_column(
        SQLEnum(ReviewPriority, name="review_priority_enum"),
        default=ReviewPriority.NORMAL,
        server_default=ReviewPriority.NORMAL.value,
        nullable=False,
    )
    status: Mapped[PharmacistReviewStatus] = mapped_column(
        SQLEnum(PharmacistReviewStatus, name="pharmacist_review_status_enum"),
        default=PharmacistReviewStatus.REQUESTED,
        server_default=PharmacistReviewStatus.REQUESTED.value,
        nullable=False,
    )
    physician_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    pharmacist_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    pharmacist_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    monitoring_recommendations: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    recommended_changes: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assessment: Mapped[MedicationAssessment] = relationship(back_populates="reviews")
    organization: Mapped["Organization"] = relationship()
    requester: Mapped["User"] = relationship(foreign_keys=[requested_by])
    assigned_pharmacist: Mapped["User | None"] = relationship(foreign_keys=[assigned_pharmacist_id])


__all__ = [
    "AssessmentEvidence",
    "AssessmentFinding",
    "AssessmentMedication",
    "AssessmentRecommendation",
    "MedicationAssessment",
    "PharmacistReview",
    "PharmacistReviewStatus",
    "ReviewPriority",
]
