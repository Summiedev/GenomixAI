"""Add normalized patient clinical domains."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.String(length=50), server_default="MANUAL", nullable=False),
        sa.Column("status", _record_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
    ]


record_status = postgresql.ENUM(
    "ACTIVE", "INACTIVE", name="clinical_record_status_enum", create_type=False
)
_record_status = record_status
encounter_type = postgresql.ENUM(
    "OUTPATIENT", "INPATIENT", "EMERGENCY", "TELEHEALTH", "OTHER",
    name="encounter_type_enum", create_type=False,
)
vital_type = postgresql.ENUM(
    "HEART_RATE", "SYSTOLIC_BLOOD_PRESSURE", "DIASTOLIC_BLOOD_PRESSURE",
    "RESPIRATORY_RATE", "TEMPERATURE", "OXYGEN_SATURATION", "WEIGHT", "HEIGHT", "OTHER",
    name="vital_type_enum", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in (record_status, encounter_type, vital_type):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "encounters",
        *_base_columns(),
        sa.Column("encounter_type", encounter_type, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_encounter_patient_org_started", "encounters", ["patient_id", "organization_id", "started_at"])

    for table_name, extra_columns, indexes in (
        (
            "conditions",
            [
                sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=True),
                sa.Column("code", sa.String(length=50), nullable=True),
                sa.Column("name", sa.String(length=200), nullable=False),
                sa.Column("onset_date", sa.Date(), nullable=True),
            ],
            [("ix_condition_patient_org_onset", ["patient_id", "organization_id", "onset_date"])],
        ),
        (
            "clinical_notes",
            [
                sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=True),
                sa.Column("note_type", sa.String(length=100), nullable=False),
                sa.Column("content", sa.Text(), nullable=False),
                sa.Column("noted_at", sa.DateTime(timezone=True), nullable=False),
            ],
            [("ix_note_patient_org_noted", ["patient_id", "organization_id", "noted_at"])],
        ),
        (
            "vitals",
            [
                sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=True),
                sa.Column("vital_type", vital_type, nullable=False),
                sa.Column("value", sa.Numeric(12, 4), nullable=False),
                sa.Column("unit", sa.String(length=30), nullable=False),
                sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
            ],
            [("ix_vital_patient_org_measured", ["patient_id", "organization_id", "measured_at"])],
        ),
        (
            "lab_results",
            [
                sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=True),
                sa.Column("test_name", sa.String(length=200), nullable=False),
                sa.Column("value", sa.String(length=200), nullable=False),
                sa.Column("numeric_value", sa.Numeric(14, 5), nullable=True),
                sa.Column("unit", sa.String(length=30), nullable=True),
                sa.Column("reference_range", sa.String(length=100), nullable=True),
                sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
            ],
            [("ix_lab_patient_org_collected", ["patient_id", "organization_id", "collected_at"])],
        ),
        (
            "allergies",
            [
                sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=True),
                sa.Column("allergen", sa.String(length=200), nullable=False),
                sa.Column("reaction", sa.String(length=500), nullable=True),
                sa.Column("severity", sa.String(length=30), nullable=True),
            ],
            [("ix_allergy_patient_org_created", ["patient_id", "organization_id", "created_at"])],
        ),
        (
            "adverse_drug_reactions",
            [
                sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=True),
                sa.Column("medication", sa.String(length=200), nullable=False),
                sa.Column("reaction", sa.String(length=500), nullable=False),
                sa.Column("severity", sa.String(length=30), nullable=True),
                sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            ],
            [("ix_adr_patient_org_occurred", ["patient_id", "organization_id", "occurred_at"])],
        ),
    ):
        op.create_table(
            table_name,
            *_base_columns(),
            *extra_columns,
            *_audit_columns(),
            sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["encounter_id"], ["encounters.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        for index_name, columns in indexes:
            op.create_index(index_name, table_name, columns)


def downgrade() -> None:
    for index_name, table_name in (
        ("ix_adr_patient_org_occurred", "adverse_drug_reactions"),
        ("ix_allergy_patient_org_created", "allergies"),
        ("ix_lab_patient_org_collected", "lab_results"),
        ("ix_vital_patient_org_measured", "vitals"),
        ("ix_note_patient_org_noted", "clinical_notes"),
        ("ix_condition_patient_org_onset", "conditions"),
        ("ix_encounter_patient_org_started", "encounters"),
    ):
        op.drop_index(index_name, table_name=table_name)
    for table_name in (
        "adverse_drug_reactions", "allergies", "lab_results", "vitals",
        "clinical_notes", "conditions", "encounters",
    ):
        op.drop_table(table_name)
    bind = op.get_bind()
    for enum_name in ("vital_type_enum", "encounter_type_enum", "clinical_record_status_enum"):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
