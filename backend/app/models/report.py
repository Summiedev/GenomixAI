from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.assessment import MedicationAssessment
    from app.models.identity import User
    from app.models.organization import Organization


class AssessmentReport(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "assessment_reports"
    __table_args__ = (
        Index("ix_assessment_report_assessment_created", "assessment_id", "created_at"),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("medication_assessments.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    generated_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="application/pdf", server_default="application/pdf"
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    synthetic_data_marker: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false"
    )
    report_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    pdf_content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    assessment: Mapped["MedicationAssessment"] = relationship()
    organization: Mapped["Organization"] = relationship()
    generator: Mapped["User"] = relationship()


__all__ = ["AssessmentReport"]
