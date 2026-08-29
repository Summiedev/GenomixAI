"""Add global patient identities and organization-specific patient links."""

from datetime import date
from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PATIENT_A = UUID("00000000-0000-0000-0000-00000000c001")
PATIENT_B = UUID("00000000-0000-0000-0000-00000000c002")


def upgrade() -> None:
    patient_status = postgresql.ENUM(
        "ACTIVE", "INACTIVE", name="patient_status_enum", create_type=False
    )
    patient_sex = postgresql.ENUM(
        "FEMALE", "MALE", "INTERSEX", "UNKNOWN", name="patient_sex_enum", create_type=False
    )
    patient_link_status = postgresql.ENUM(
        "ACTIVE", "INACTIVE", name="patient_link_status_enum", create_type=False
    )
    bind = op.get_bind()
    for enum_type in (patient_status, patient_sex, patient_link_status):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("genomix_patient_id", sa.String(length=64), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("sex", patient_sex, nullable=False),
        sa.Column("status", patient_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("genomix_patient_id"),
    )
    op.create_table(
        "patient_organization_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mrn", sa.String(length=100), nullable=False),
        sa.Column("status", patient_link_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id", "organization_id", name="uq_patient_organization_link"),
        sa.UniqueConstraint("organization_id", "mrn", name="uq_patient_organization_mrn"),
    )
    op.create_index(
        "ix_patient_link_organization_patient",
        "patient_organization_links",
        ["organization_id", "patient_id"],
    )

    op.bulk_insert(
        sa.table(
            "patients",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("genomix_patient_id", sa.String),
            sa.column("first_name", sa.String),
            sa.column("last_name", sa.String),
            sa.column("date_of_birth", sa.Date),
            sa.column("sex", patient_sex),
            sa.column("status", patient_status),
        ),
        [
            {
                "id": PATIENT_A,
                "genomix_patient_id": "GX-000001",
                "first_name": "Amara",
                "last_name": "Okafor",
                "date_of_birth": date(1984, 5, 17),
                "sex": "FEMALE",
                "status": "ACTIVE",
            },
            {
                "id": PATIENT_B,
                "genomix_patient_id": "GX-000002",
                "first_name": "Bayo",
                "last_name": "Adeyemi",
                "date_of_birth": date(1978, 11, 2),
                "sex": "MALE",
                "status": "ACTIVE",
            },
        ],
    )
    op.bulk_insert(
        sa.table(
            "patient_organization_links",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("patient_id", postgresql.UUID(as_uuid=True)),
            sa.column("organization_id", postgresql.UUID(as_uuid=True)),
            sa.column("mrn", sa.String),
            sa.column("status", patient_link_status),
        ),
        [
            {
                "id": UUID("00000000-0000-0000-0000-00000000c101"),
                "patient_id": PATIENT_A,
                "organization_id": UUID("00000000-0000-0000-0000-0000000000a1"),
                "mrn": "HA-0001",
                "status": "ACTIVE",
            },
            {
                "id": UUID("00000000-0000-0000-0000-00000000c102"),
                "patient_id": PATIENT_B,
                "organization_id": UUID("00000000-0000-0000-0000-0000000000b1"),
                "mrn": "HB-0001",
                "status": "ACTIVE",
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_patient_link_organization_patient", table_name="patient_organization_links")
    op.drop_table("patient_organization_links")
    op.drop_table("patients")
    bind = op.get_bind()
    for enum_name in ("patient_link_status_enum", "patient_sex_enum", "patient_status_enum"):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
