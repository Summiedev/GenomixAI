"""Add physician decisions, clinical audit events, and assessment reports."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(*values: str, name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    decision_type = _enum(
        "ACCEPT", "MODIFY", "DECLINE", "REQUEST_CLARIFICATION",
        name="physician_decision_type_enum",
    )
    audit_action = _enum(
        "LOGIN", "LOGOUT", "PATIENT_VIEWED", "PATIENT_SEARCHED", "ASSESSMENT_CREATED",
        "ASSESSMENT_ANALYZED", "ASSESSMENT_MODIFIED", "PHARMACIST_REVIEW_REQUESTED",
        "PHARMACIST_REVIEW_OPENED", "PHARMACIST_RECOMMENDATION_SUBMITTED",
        "PHYSICIAN_REVIEWED_RECOMMENDATION", "FINAL_DECISION_RECORDED", "REPORT_GENERATED",
        name="audit_action_enum",
    )
    for enum_type in (decision_type, audit_action):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "physician_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("physician_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pharmacist_review_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision", decision_type, nullable=False),
        sa.Column("decision_rationale", sa.Text(), nullable=False),
        sa.Column("assessment_version", sa.String(length=100), nullable=False),
        sa.Column("finalized", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["medication_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["physician_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["pharmacist_review_id"], ["pharmacist_reviews.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_physician_decision_assessment_created",
        "physician_decisions",
        ["assessment_id", "created_at"],
    )

    op.create_table(
        "physician_decision_medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("medication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("medication_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dose", sa.Numeric(12, 4), nullable=False),
        sa.Column("dose_unit", sa.String(length=30), nullable=False),
        sa.Column("route", sa.String(length=50), nullable=False),
        sa.Column("frequency", sa.String(length=100), nullable=False),
        sa.Column("duration_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("duration_unit", sa.String(length=20), nullable=True),
        sa.Column("indication", sa.String(length=500), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["physician_decisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["medication_order_id"], ["medication_orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_medication_decision",
        "physician_decision_medications",
        ["decision_id"],
    )

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_id", sa.String(length=150), nullable=True),
        sa.Column("correlation_id", sa.String(length=150), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_event_org_timestamp", "audit_events", ["organization_id", "timestamp"])
    op.create_index("ix_audit_event_resource", "audit_events", ["resource_type", "resource_id"])

    op.create_table(
        "assessment_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_type", sa.String(length=100), server_default="application/pdf", nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("synthetic_data_marker", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("report_data", postgresql.JSONB(), nullable=False),
        sa.Column("pdf_content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["medication_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_report_assessment_created",
        "assessment_reports",
        ["assessment_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_assessment_report_assessment_created", table_name="assessment_reports")
    op.drop_table("assessment_reports")
    op.drop_index("ix_audit_event_resource", table_name="audit_events")
    op.drop_index("ix_audit_event_org_timestamp", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_decision_medication_decision", table_name="physician_decision_medications")
    op.drop_table("physician_decision_medications")
    op.drop_index("ix_physician_decision_assessment_created", table_name="physician_decisions")
    op.drop_table("physician_decisions")
    bind = op.get_bind()
    for enum_name in ("audit_action_enum", "physician_decision_type_enum"):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
