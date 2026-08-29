from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin


class MigrationProbe(UUIDPKMixin, TimestampMixin, Base):
    """Minimal table proving Alembic metadata and migrations are wired correctly."""

    __tablename__ = "migration_probes"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"MigrationProbe(id={self.id!r}, name={self.name!r})"


__all__ = ["MigrationProbe"]
