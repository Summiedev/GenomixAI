"""Add the deduplicated clinical timeline projection."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

event_type = postgresql.ENUM(
    "ENCOUNTER", "DIAGNOSIS", "PROCEDURE", "LAB_RESULT", "VITAL",
    "MEDICATION_PRESCRIBED", "MEDICATION_MODIFIED", "MEDICATION_DISCONTINUED",
    "ALLERGY_RECORDED", "ADVERSE_REACTION", "CLINICAL_NOTE", "GENOMIC_RESULT",
    "MEDICATION_ASSESSMENT", "PHARMACIST_REVIEW", "FINAL_DECISION",
    name="clinical_event_type_enum", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    event_type.create(bind, checkfirst=True)
    op.create_table(
        "clinical_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("linked_resource_type", sa.String(length=100), nullable=False),
        sa.Column("linked_resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dedupe_key", sa.String(length=250), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=50), server_default="MANUAL", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "dedupe_key", name="uq_clinical_event_dedupe"),
    )
    op.create_index(
        "ix_clinical_event_patient_org_time",
        "clinical_events",
        ["patient_id", "organization_id", "event_timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_clinical_event_patient_org_time", table_name="clinical_events")
    op.drop_table("clinical_events")
    event_type.drop(op.get_bind(), checkfirst=True)
