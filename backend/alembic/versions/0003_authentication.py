"""Add password hashes and server-side access-token revocation."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )

    # Development seed accounts use this documented password. It is hashed here
    # and the plaintext is never persisted in the database.
    from app.core.security import hash_password

    password_hash = hash_password("ChangeMe123!")
    op.execute(
        sa.text(
            "UPDATE users SET password_hash = :password_hash "
            "WHERE email LIKE '%@genomixai.demo'"
        ).bindparams(password_hash=password_hash)
    )


def downgrade() -> None:
    op.drop_table("revoked_tokens")
    op.drop_column("users", "password_hash")
