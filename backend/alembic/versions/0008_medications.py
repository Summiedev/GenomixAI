"""Add medication reference, orders, and explicit order status history."""

from datetime import date
from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORG_A = UUID("00000000-0000-0000-0000-0000000000a1")
ORG_B = UUID("00000000-0000-0000-0000-0000000000b1")
PATIENT_A = UUID("00000000-0000-0000-0000-00000000c001")
PATIENT_B = UUID("00000000-0000-0000-0000-00000000c002")
MED_ASPIRIN = UUID("00000000-0000-0000-0000-00000000e001")
MED_ATORVASTATIN = UUID("00000000-0000-0000-0000-00000000e002")
MED_CLOPIDOGREL = UUID("00000000-0000-0000-0000-00000000e003")
ORDER_ACTIVE = UUID("00000000-0000-0000-0000-00000000e101")
ORDER_COMPLETED = UUID("00000000-0000-0000-0000-00000000e102")
ORDER_DISCONTINUED = UUID("00000000-0000-0000-0000-00000000e103")


def upgrade() -> None:
    medication_status = postgresql.ENUM(
        "ACTIVE", "INACTIVE", name="medication_status_enum", create_type=False
    )
    order_status = postgresql.ENUM(
        "PROPOSED", "ACTIVE", "COMPLETED", "DISCONTINUED", "CANCELLED",
        name="medication_order_status_enum", create_type=False,
    )
    duration_unit = postgresql.ENUM(
        "DAYS", "WEEKS", "MONTHS", "DOSES", name="duration_unit_enum", create_type=False
    )
    bind = op.get_bind()
    for enum_type in (medication_status, order_status, duration_unit):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("standardized_code", sa.String(length=100), nullable=True),
        sa.Column("generic_name", sa.String(length=200), nullable=False),
        sa.Column("brand_name", sa.String(length=200), nullable=True),
        sa.Column("strength", sa.String(length=100), nullable=True),
        sa.Column("dosage_form", sa.String(length=100), nullable=True),
        sa.Column("status", medication_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("standardized_code"),
    )
    op.create_index("ix_medication_generic_name", "medications", ["generic_name"])

    op.create_table(
        "medication_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("medication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dose", sa.Numeric(12, 4), nullable=False),
        sa.Column("dose_unit", sa.String(length=30), nullable=False),
        sa.Column("route", sa.String(length=50), nullable=False),
        sa.Column("frequency", sa.String(length=100), nullable=False),
        sa.Column("duration_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("duration_unit", duration_unit, nullable=True),
        sa.Column("indication", sa.String(length=500), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("prescriber_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", order_status, server_default="PROPOSED", nullable=False),
        sa.Column("source", sa.String(length=50), server_default="MANUAL", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["encounter_id"], ["encounters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["prescriber_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_med_order_patient_org_start", "medication_orders", ["patient_id", "organization_id", "start_date"])

    op.create_table(
        "medication_order_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", order_status, nullable=True),
        sa.Column("to_status", order_status, nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["medication_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
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
            sa.column("status", medication_status),
        ),
        [
            {"id": MED_ASPIRIN, "standardized_code": "RXNORM:1191", "generic_name": "Aspirin", "brand_name": "Bayer Aspirin", "strength": "81 mg", "dosage_form": "TABLET", "status": "ACTIVE"},
            {"id": MED_ATORVASTATIN, "standardized_code": "RXNORM:83367", "generic_name": "Atorvastatin", "brand_name": "Lipitor", "strength": "20 mg", "dosage_form": "TABLET", "status": "ACTIVE"},
            {"id": MED_CLOPIDOGREL, "standardized_code": "RXNORM:309362", "generic_name": "Clopidogrel", "brand_name": "Plavix", "strength": "75 mg", "dosage_form": "TABLET", "status": "ACTIVE"},
        ],
    )
    op.bulk_insert(
        sa.table(
            "medication_orders",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("patient_id", postgresql.UUID(as_uuid=True)),
            sa.column("organization_id", postgresql.UUID(as_uuid=True)),
            sa.column("medication_id", postgresql.UUID(as_uuid=True)),
            sa.column("dose", sa.Numeric),
            sa.column("dose_unit", sa.String),
            sa.column("route", sa.String),
            sa.column("frequency", sa.String),
            sa.column("duration_value", sa.Numeric),
            sa.column("duration_unit", duration_unit),
            sa.column("indication", sa.String),
            sa.column("start_date", sa.Date),
            sa.column("end_date", sa.Date),
            sa.column("status", order_status),
            sa.column("source", sa.String),
        ),
        [
            {"id": ORDER_ACTIVE, "patient_id": PATIENT_A, "organization_id": ORG_A, "medication_id": MED_ASPIRIN, "dose": 81, "dose_unit": "mg", "route": "ORAL", "frequency": "ONCE_DAILY", "duration_value": None, "duration_unit": None, "indication": "Cardiovascular prevention", "start_date": date(2026, 1, 1), "end_date": None, "status": "ACTIVE", "source": "SYNTHETIC"},
            {"id": ORDER_COMPLETED, "patient_id": PATIENT_A, "organization_id": ORG_A, "medication_id": MED_ATORVASTATIN, "dose": 20, "dose_unit": "mg", "route": "ORAL", "frequency": "ONCE_DAILY", "duration_value": 90, "duration_unit": "DAYS", "indication": "Hyperlipidemia", "start_date": date(2025, 1, 1), "end_date": date(2025, 4, 1), "status": "COMPLETED", "source": "SYNTHETIC"},
            {"id": ORDER_DISCONTINUED, "patient_id": PATIENT_B, "organization_id": ORG_B, "medication_id": MED_CLOPIDOGREL, "dose": 75, "dose_unit": "mg", "route": "ORAL", "frequency": "ONCE_DAILY", "duration_value": None, "duration_unit": None, "indication": "Antiplatelet therapy", "start_date": date(2025, 6, 1), "end_date": date(2025, 7, 1), "status": "DISCONTINUED", "source": "SYNTHETIC"},
        ],
    )


def downgrade() -> None:
    op.drop_table("medication_order_status_history")
    op.drop_index("ix_med_order_patient_org_start", table_name="medication_orders")
    op.drop_table("medication_orders")
    op.drop_index("ix_medication_generic_name", table_name="medications")
    op.drop_table("medications")
    bind = op.get_bind()
    for enum_name in ("duration_unit_enum", "medication_order_status_enum", "medication_status_enum"):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
