from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin
from app.models.organization import Department, Organization


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MembershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Role(StrEnum):
    PHYSICIAN = "PHYSICIAN"
    CLINICAL_PHARMACIST = "CLINICAL_PHARMACIST"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Nullable for backwards compatibility with users created before Phase 4.
    # Authentication refuses users without a password hash.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name="user_status_enum"),
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
        nullable=False,
    )

    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class OrganizationMembership(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_membership_user_organization"),
        Index("ix_membership_organization_user", "organization_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    role: Mapped[Role] = mapped_column(SQLEnum(Role, name="role_enum"), nullable=False)
    status: Mapped[MembershipStatus] = mapped_column(
        SQLEnum(MembershipStatus, name="membership_status_enum"),
        default=MembershipStatus.ACTIVE,
        server_default=MembershipStatus.ACTIVE.value,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped[Organization] = relationship(back_populates="memberships")
    department: Mapped[Department | None] = relationship(back_populates="memberships")


class RevokedToken(Base):
    """Server-side logout record for an otherwise stateless access token."""

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


__all__ = [
    "MembershipStatus",
    "OrganizationMembership",
    "RevokedToken",
    "Role",
    "User",
    "UserStatus",
]
