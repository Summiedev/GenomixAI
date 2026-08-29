"""Add organizations, departments, users, and memberships."""

from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORG_A = UUID("00000000-0000-0000-0000-0000000000a1")
ORG_B = UUID("00000000-0000-0000-0000-0000000000b1")
CARDIOLOGY_A = UUID("00000000-0000-0000-0000-00000000a101")
PHARMACY_A = UUID("00000000-0000-0000-0000-00000000a102")
CARDIOLOGY_B = UUID("00000000-0000-0000-0000-00000000b101")
PHARMACY_B = UUID("00000000-0000-0000-0000-00000000b102")
PHYSICIAN_A = UUID("00000000-0000-0000-0000-0000000a0101")
PHARMACIST_A = UUID("00000000-0000-0000-0000-0000000a0102")
PHYSICIAN_B = UUID("00000000-0000-0000-0000-0000000b0101")
PHARMACIST_B = UUID("00000000-0000-0000-0000-0000000b0102")
MEMBERSHIP_IDS = [
    UUID("00000000-0000-0000-0000-00000a010101"),
    UUID("00000000-0000-0000-0000-00000a010102"),
    UUID("00000000-0000-0000-0000-00000b010101"),
    UUID("00000000-0000-0000-0000-00000b010102"),
]


def upgrade() -> None:
    organization_status = postgresql.ENUM(
        "ACTIVE", "INACTIVE", name="organization_status_enum", create_type=False
    )
    department_status = postgresql.ENUM(
        "ACTIVE", "INACTIVE", name="department_status_enum", create_type=False
    )
    user_status = postgresql.ENUM("ACTIVE", "INACTIVE", name="user_status_enum", create_type=False)
    membership_status = postgresql.ENUM(
        "ACTIVE", "INACTIVE", name="membership_status_enum", create_type=False
    )
    role = postgresql.ENUM(
        "PHYSICIAN",
        "CLINICAL_PHARMACIST",
        "HOSPITAL_ADMIN",
        "PLATFORM_ADMIN",
        name="role_enum",
        create_type=False,
    )
    bind = op.get_bind()
    for enum_type in (organization_status, department_status, user_status, membership_status, role):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("status", organization_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("status", department_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug", name="uq_department_org_slug"),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("status", user_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", role, nullable=False),
        sa.Column("status", membership_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_membership_user_organization"),
    )
    op.create_index(
        "ix_membership_organization_user",
        "organization_memberships",
        ["organization_id", "user_id"],
    )

    op.bulk_insert(
        sa.table(
            "organizations",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("name", sa.String),
            sa.column("slug", sa.String),
            sa.column("status", organization_status),
        ),
        [
            {"id": ORG_A, "name": "Hospital A", "slug": "hospital-a", "status": "ACTIVE"},
            {"id": ORG_B, "name": "Hospital B", "slug": "hospital-b", "status": "ACTIVE"},
        ],
    )
    op.bulk_insert(
        sa.table(
            "departments",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("organization_id", postgresql.UUID(as_uuid=True)),
            sa.column("name", sa.String),
            sa.column("slug", sa.String),
            sa.column("status", department_status),
        ),
        [
            {"id": CARDIOLOGY_A, "organization_id": ORG_A, "name": "Cardiology", "slug": "cardiology", "status": "ACTIVE"},
            {"id": PHARMACY_A, "organization_id": ORG_A, "name": "Pharmacy", "slug": "pharmacy", "status": "ACTIVE"},
            {"id": CARDIOLOGY_B, "organization_id": ORG_B, "name": "Cardiology", "slug": "cardiology", "status": "ACTIVE"},
            {"id": PHARMACY_B, "organization_id": ORG_B, "name": "Pharmacy", "slug": "pharmacy", "status": "ACTIVE"},
        ],
    )
    op.bulk_insert(
        sa.table(
            "users",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("email", sa.String),
            sa.column("full_name", sa.String),
            sa.column("status", user_status),
        ),
        [
            {"id": PHYSICIAN_A, "email": "physician.a@genomixai.demo", "full_name": "Dr. Ada Adebayo", "status": "ACTIVE"},
            {"id": PHARMACIST_A, "email": "pharmacist.a@genomixai.demo", "full_name": "PharmD Bola Okafor", "status": "ACTIVE"},
            {"id": PHYSICIAN_B, "email": "physician.b@genomixai.demo", "full_name": "Dr. Chidi Nwosu", "status": "ACTIVE"},
            {"id": PHARMACIST_B, "email": "pharmacist.b@genomixai.demo", "full_name": "PharmD Dami Bello", "status": "ACTIVE"},
        ],
    )
    op.bulk_insert(
        sa.table(
            "organization_memberships",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("user_id", postgresql.UUID(as_uuid=True)),
            sa.column("organization_id", postgresql.UUID(as_uuid=True)),
            sa.column("department_id", postgresql.UUID(as_uuid=True)),
            sa.column("role", role),
            sa.column("status", membership_status),
        ),
        [
            {"id": MEMBERSHIP_IDS[0], "user_id": PHYSICIAN_A, "organization_id": ORG_A, "department_id": CARDIOLOGY_A, "role": "PHYSICIAN", "status": "ACTIVE"},
            {"id": MEMBERSHIP_IDS[1], "user_id": PHARMACIST_A, "organization_id": ORG_A, "department_id": PHARMACY_A, "role": "CLINICAL_PHARMACIST", "status": "ACTIVE"},
            {"id": MEMBERSHIP_IDS[2], "user_id": PHYSICIAN_B, "organization_id": ORG_B, "department_id": CARDIOLOGY_B, "role": "PHYSICIAN", "status": "ACTIVE"},
            {"id": MEMBERSHIP_IDS[3], "user_id": PHARMACIST_B, "organization_id": ORG_B, "department_id": PHARMACY_B, "role": "CLINICAL_PHARMACIST", "status": "ACTIVE"},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_membership_organization_user", table_name="organization_memberships")
    op.drop_table("organization_memberships")
    op.drop_table("users")
    op.drop_table("departments")
    op.drop_table("organizations")
    bind = op.get_bind()
    for enum_name in (
        "role_enum",
        "membership_status_enum",
        "user_status_enum",
        "department_status_enum",
        "organization_status_enum",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
