"""Add persisted medication assessments and pharmacist review workflow."""

from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MED_CLOPIDOGREL = UUID("00000000-0000-0000-0000-00000000e003")
MED_SIMVASTATIN = UUID("00000000-0000-0000-0000-00000000e002")
MED_TICAGRELOR = UUID("00000000-0000-0000-0000-00000000f004")
SRC_CPIC_CLOPIDOGREL = UUID("00000000-0000-0000-0000-00000000f101")
RULE_PGX_INTERMEDIATE = UUID("00000000-0000-0000-0000-00000000f201")
RULE_PGX_POOR = UUID("00000000-0000-0000-0000-00000000f202")
ALT_PGX_INTERMEDIATE = UUID("00000000-0000-0000-0000-00000000f501")
ALT_PGX_POOR = UUID("00000000-0000-0000-0000-00000000f502")


def _enum(*values: str, name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    assessment_state = _enum(
        "DRAFT", "ANALYZED", "PENDING_PHARMACIST_REVIEW", "IN_PHARMACIST_REVIEW",
        "PHARMACIST_RECOMMENDED", "RETURNED_TO_PHYSICIAN", "FINALIZED", "CANCELLED",
        name="assessment_state_enum",
    )
    finding_category = _enum(
        "PHARMACOGENOMICS", "DRUG_INTERACTION", "ALLERGY", "ADVERSE_DRUG_REACTION",
        "CONTRAINDICATION", "CLINICAL_FACTOR", "DOSE", "MONITORING", "ML",
        name="assessment_finding_category_enum",
    )
    finding_severity = _enum(
        "INFO", "LOW", "MODERATE", "HIGH", "CRITICAL", "UNKNOWN",
        name="assessment_finding_severity_enum",
    )
    alternative_classification = _enum(
        "GUIDELINE_SUPPORTED_ALTERNATIVE", "POTENTIAL_ALTERNATIVE",
        "SPECIALIST_REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE",
        name="alternative_classification_enum",
    )
    review_status = _enum(
        "REQUESTED", "IN_PROGRESS", "SUBMITTED", "RETURNED", "CANCELLED",
        name="pharmacist_review_status_enum",
    )
    review_priority = _enum("LOW", "NORMAL", "HIGH", "URGENT", name="review_priority_enum")
    for enum_type in (
        assessment_state,
        finding_category,
        finding_severity,
        alternative_classification,
        review_status,
        review_priority,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "pharmacogenomic_rule_alternatives",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alternative_medication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("classification", alternative_classification, nullable=False),
        sa.Column("clinical_rationale", sa.Text(), nullable=False),
        sa.Column("patient_specific_rationale", sa.Text(), nullable=True),
        sa.Column("important_limitations", sa.Text(), nullable=True),
        sa.Column("evidence_source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["pharmacogenomic_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alternative_medication_id"], ["medications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_id", "alternative_medication_id", name="uq_pgx_rule_alternative"),
    )

    op.create_table(
        "medication_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_context_version", sa.String(length=100), nullable=False),
        sa.Column("patient_context_reference", sa.String(length=300), nullable=False),
        sa.Column("engine_version", sa.String(length=100), nullable=False),
        sa.Column("status", assessment_state, server_default="DRAFT", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_patient_org_created", "medication_assessments",
        ["patient_id", "organization_id", "created_at"],
    )
    op.create_index(
        "ix_assessment_org_status", "medication_assessments", ["organization_id", "status"]
    )

    op.create_table(
        "assessment_medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("medication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dose", sa.String(length=50), nullable=True),
        sa.Column("dose_unit", sa.String(length=30), nullable=True),
        sa.Column("route", sa.String(length=50), nullable=True),
        sa.Column("frequency", sa.String(length=100), nullable=True),
        sa.Column("indication", sa.String(length=500), nullable=True),
        sa.Column("source", sa.String(length=50), server_default="MANUAL", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["medication_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_medication_assessment", "assessment_medications", ["assessment_id"]
    )

    json_list = sa.text("'[]'::jsonb")
    json_object = sa.text("'{}'::jsonb")
    op.create_table(
        "assessment_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", finding_category, nullable=False),
        sa.Column("severity", finding_severity, nullable=False),
        sa.Column("classification", sa.String(length=80), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("rule_type", sa.String(length=100), nullable=True),
        sa.Column("rule_id", sa.String(length=100), nullable=True),
        sa.Column("medication_references", postgresql.JSONB(), server_default=json_list, nullable=False),
        sa.Column("actionable", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default=json_object, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["medication_assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_finding_assessment_category", "assessment_findings", ["assessment_id", "category"]
    )

    op.create_table(
        "assessment_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_medication_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("medication_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("medication_name", sa.String(length=200), nullable=False),
        sa.Column("classification", alternative_classification, nullable=False),
        sa.Column("clinical_rationale", sa.Text(), nullable=False),
        sa.Column("patient_specific_rationale", sa.Text(), nullable=True),
        sa.Column("important_limitations", sa.Text(), nullable=True),
        sa.Column("contraindications", postgresql.JSONB(), server_default=json_list, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["medication_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assessment_medication_id"], ["assessment_medications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_recommendation_assessment", "assessment_recommendations", ["assessment_id"]
    )

    op.create_table(
        "assessment_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evidence_source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_organization", sa.String(length=200), nullable=False),
        sa.Column("source_title", sa.String(length=500), nullable=False),
        sa.Column("source_version", sa.String(length=150), nullable=True),
        sa.Column("evidence_level", sa.String(length=50), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("reference_identifier", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(finding_id IS NOT NULL) OR (recommendation_id IS NOT NULL)",
            name="ck_assessment_evidence_parent",
        ),
        sa.ForeignKeyConstraint(["finding_id"], ["assessment_findings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recommendation_id"], ["assessment_recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pharmacist_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_pharmacist_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("priority", review_priority, server_default="NORMAL", nullable=False),
        sa.Column("status", review_status, server_default="REQUESTED", nullable=False),
        sa.Column("physician_message", sa.Text(), nullable=True),
        sa.Column("pharmacist_recommendation", sa.Text(), nullable=True),
        sa.Column("pharmacist_rationale", sa.Text(), nullable=True),
        sa.Column("monitoring_recommendations", postgresql.JSONB(), server_default=json_list, nullable=False),
        sa.Column("recommended_changes", postgresql.JSONB(), server_default=json_list, nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["medication_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_pharmacist_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_pharmacist_review_org_status", "pharmacist_reviews", ["organization_id", "status"]
    )
    op.create_index(
        "ix_pharmacist_review_assessment", "pharmacist_reviews", ["assessment_id"]
    )

    op.bulk_insert(
        sa.table(
            "medications",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("standardized_code", sa.String),
            sa.column("generic_name", sa.String),
            sa.column("brand_name", sa.String),
            sa.column("strength", sa.String),
            sa.column("dosage_form", sa.String),
            sa.column("status", postgresql.ENUM("ACTIVE", "INACTIVE", name="medication_status_enum", create_type=False)),
        ),
        [{"id": MED_TICAGRELOR, "standardized_code": None, "generic_name": "Ticagrelor", "brand_name": "Brilinta", "strength": None, "dosage_form": "TABLET", "status": "ACTIVE"}],
    )
    op.bulk_insert(
        sa.table(
            "pharmacogenomic_rule_alternatives",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("rule_id", postgresql.UUID(as_uuid=True)),
            sa.column("alternative_medication_id", postgresql.UUID(as_uuid=True)),
            sa.column("classification", alternative_classification),
            sa.column("clinical_rationale", sa.Text),
            sa.column("patient_specific_rationale", sa.Text),
            sa.column("important_limitations", sa.Text),
            sa.column("evidence_source_id", postgresql.UUID(as_uuid=True)),
        ),
        [
            {"id": ALT_PGX_INTERMEDIATE, "rule_id": RULE_PGX_INTERMEDIATE, "alternative_medication_id": MED_TICAGRELOR, "classification": "GUIDELINE_SUPPORTED_ALTERNATIVE", "clinical_rationale": "Ticagrelor is identified by the CPIC guideline as a P2Y12 alternative not impacted by CYP2C19 genetic variation.", "patient_specific_rationale": "The patient phenotype matches the CYP2C19 clopidogrel rule; consider this alternative only if clinically indicated.", "important_limitations": "Selection requires clinician review of indication, bleeding risk, contraindications, and the current product labeling.", "evidence_source_id": SRC_CPIC_CLOPIDOGREL},
            {"id": ALT_PGX_POOR, "rule_id": RULE_PGX_POOR, "alternative_medication_id": MED_TICAGRELOR, "classification": "GUIDELINE_SUPPORTED_ALTERNATIVE", "clinical_rationale": "Ticagrelor is identified by the CPIC guideline as a P2Y12 alternative not impacted by CYP2C19 genetic variation.", "patient_specific_rationale": "The patient phenotype matches the CYP2C19 clopidogrel rule; consider this alternative only if clinically indicated.", "important_limitations": "Selection requires clinician review of indication, bleeding risk, contraindications, and the current product labeling.", "evidence_source_id": SRC_CPIC_CLOPIDOGREL},
        ],
    )


def downgrade() -> None:
    for table_name in (
        "pharmacist_reviews", "assessment_evidence", "assessment_recommendations",
        "assessment_findings", "assessment_medications", "medication_assessments",
        "pharmacogenomic_rule_alternatives",
    ):
        op.drop_table(table_name)
    bind = op.get_bind()
    for enum_name in (
        "review_priority_enum", "pharmacist_review_status_enum", "alternative_classification_enum",
        "assessment_finding_severity_enum", "assessment_finding_category_enum", "assessment_state_enum",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
