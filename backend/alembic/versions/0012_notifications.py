"""Add persistent organization-scoped workflow notifications."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    notification_type = postgresql.ENUM(
        "PHARMACIST_REVIEW_REQUESTED",
        "PHARMACIST_ASSIGNED",
        "PHARMACIST_REVIEW_STARTED",
        "PHARMACIST_RECOMMENDATION_SUBMITTED",
        "ASSESSMENT_RETURNED_TO_PHYSICIAN",
        "FINAL_DECISION_RECORDED",
        name="notification_type_enum",
        create_type=False,
    )
    notification_type.create(bind, checkfirst=True)
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_type", notification_type, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_recipient_org_created",
        "notifications",
        ["recipient_user_id", "organization_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_recipient_org_created", table_name="notifications")
    op.drop_table("notifications")
    postgresql.ENUM(name="notification_type_enum").drop(op.get_bind(), checkfirst=True)
