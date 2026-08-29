"""Add source-labelled pharmacogenomic profiles and separate interpretations."""

from datetime import date
from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PATIENT_A = UUID("00000000-0000-0000-0000-00000000c001")
PATIENT_B = UUID("00000000-0000-0000-0000-00000000c002")
ORG_A = UUID("00000000-0000-0000-0000-0000000000a1")
ORG_B = UUID("00000000-0000-0000-0000-0000000000b1")
PROFILE_A = UUID("00000000-0000-0000-0000-00000000d001")
PROFILE_A_RAW = UUID("00000000-0000-0000-0000-00000000d002")
PROFILE_B = UUID("00000000-0000-0000-0000-00000000d003")
VARIANT_CYP = UUID("00000000-0000-0000-0000-00000000d101")
VARIANT_DPY = UUID("00000000-0000-0000-0000-00000000d102")
INTERPRETATION_CYP = UUID("00000000-0000-0000-0000-00000000d201")
EVIDENCE_CYP = UUID("00000000-0000-0000-0000-00000000d301")


def upgrade() -> None:
    data_source = postgresql.ENUM(
        "SYNTHETIC", "RESEARCH_DATASET", "CLINICAL_LAB", "UNKNOWN",
        name="genomic_data_source_enum", create_type=False,
    )
    validation_status = postgresql.ENUM(
        "NOT_CLINICALLY_VALIDATED", "CLINICALLY_VALIDATED",
        name="genomic_validation_status_enum", create_type=False,
    )
    record_status = postgresql.ENUM(
        "ACTIVE", "INACTIVE", name="genomic_record_status_enum", create_type=False
    )
    bind = op.get_bind()
    for enum_type in (data_source, validation_status, record_status):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "genomic_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("source", data_source, nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=True),
        sa.Column("validation_status", validation_status, server_default="NOT_CLINICALLY_VALIDATED", nullable=False),
        sa.Column("status", record_status, server_default="ACTIVE", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_genomic_profile_patient_org_test", "genomic_profiles", ["patient_id", "organization_id", "test_date"])

    op.create_table(
        "genomic_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gene", sa.String(length=50), nullable=False),
        sa.Column("variant", sa.String(length=200), nullable=False),
        sa.Column("allele", sa.String(length=100), nullable=True),
        sa.Column("genotype", sa.String(length=100), nullable=True),
        sa.Column("phenotype", sa.String(length=200), nullable=True),
        sa.Column("raw_result", postgresql.JSONB(), nullable=True),
        sa.Column("source", data_source, nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=True),
        sa.Column("status", record_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["genomic_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_genomic_variant_profile_gene", "genomic_variants", ["profile_id", "gene"])

    op.create_table(
        "pharmacogenomic_interpretations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gene", sa.String(length=50), nullable=False),
        sa.Column("interpretation", sa.Text(), nullable=False),
        sa.Column("clinical_significance", sa.String(length=200), nullable=True),
        sa.Column("evidence_level", sa.String(length=50), nullable=True),
        sa.Column("interpretation_date", sa.Date(), nullable=False),
        sa.Column("source", data_source, nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=True),
        sa.Column("status", record_status, server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["genomic_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["genomic_variants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pg_interpretation_profile_gene", "pharmacogenomic_interpretations", ["profile_id", "gene"])

    op.create_table(
        "evidence_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interpretation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("citation", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("source", data_source, nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["interpretation_id"], ["pharmacogenomic_interpretations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.bulk_insert(
        sa.table(
            "genomic_profiles",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("patient_id", postgresql.UUID(as_uuid=True)),
            sa.column("organization_id", postgresql.UUID(as_uuid=True)),
            sa.column("test_date", sa.Date()),
            sa.column("source", data_source),
            sa.column("source_version", sa.String),
            sa.column("validation_status", validation_status),
            sa.column("status", record_status),
            sa.column("notes", sa.Text),
        ),
        [
            {"id": PROFILE_A, "patient_id": PATIENT_A, "organization_id": ORG_A, "test_date": date(2026, 1, 10), "source": "SYNTHETIC", "source_version": "demo-1", "validation_status": "NOT_CLINICALLY_VALIDATED", "status": "ACTIVE", "notes": "Synthetic pharmacogenomic demonstration data."},
            {"id": PROFILE_A_RAW, "patient_id": PATIENT_A, "organization_id": ORG_A, "test_date": date(2026, 2, 1), "source": "RESEARCH_DATASET", "source_version": "research-demo-1", "validation_status": "NOT_CLINICALLY_VALIDATED", "status": "ACTIVE", "notes": "Research dataset result; not a clinical report."},
            {"id": PROFILE_B, "patient_id": PATIENT_B, "organization_id": ORG_B, "test_date": date(2026, 1, 12), "source": "SYNTHETIC", "source_version": "demo-1", "validation_status": "NOT_CLINICALLY_VALIDATED", "status": "ACTIVE", "notes": "Synthetic pharmacogenomic demonstration data."},
        ],
    )
    op.bulk_insert(
        sa.table(
            "genomic_variants",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("profile_id", postgresql.UUID(as_uuid=True)),
            sa.column("gene", sa.String),
            sa.column("variant", sa.String),
            sa.column("allele", sa.String),
            sa.column("genotype", sa.String),
            sa.column("phenotype", sa.String),
            sa.column("raw_result", postgresql.JSONB),
            sa.column("source", data_source),
            sa.column("source_version", sa.String),
            sa.column("status", record_status),
        ),
        [
            {"id": VARIANT_CYP, "profile_id": PROFILE_A, "gene": "CYP2C19", "variant": "*2", "allele": "*2", "genotype": "*1/*2", "phenotype": "INTERMEDIATE_METABOLIZER", "raw_result": {"call": "*1/*2", "assay": "synthetic"}, "source": "SYNTHETIC", "source_version": "demo-1", "status": "ACTIVE"},
            {"id": VARIANT_DPY, "profile_id": PROFILE_A, "gene": "DPYD", "variant": "c.1905+1G>A", "allele": "A", "genotype": "G/A", "phenotype": None, "raw_result": {"call": "G/A", "assay": "synthetic"}, "source": "SYNTHETIC", "source_version": "demo-1", "status": "ACTIVE"},
        ],
    )
    op.bulk_insert(
        sa.table(
            "pharmacogenomic_interpretations",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("profile_id", postgresql.UUID(as_uuid=True)),
            sa.column("variant_id", postgresql.UUID(as_uuid=True)),
            sa.column("gene", sa.String),
            sa.column("interpretation", sa.Text),
            sa.column("clinical_significance", sa.String),
            sa.column("evidence_level", sa.String),
            sa.column("interpretation_date", sa.Date),
            sa.column("source", data_source),
            sa.column("source_version", sa.String),
            sa.column("status", record_status),
        ),
        [{"id": INTERPRETATION_CYP, "profile_id": PROFILE_A, "variant_id": VARIANT_CYP, "gene": "CYP2C19", "interpretation": "Synthetic phenotype interpretation for demonstration only.", "clinical_significance": "DEMONSTRATION", "evidence_level": "DEMO", "interpretation_date": date(2026, 1, 11), "source": "SYNTHETIC", "source_version": "demo-interpretation-1", "status": "ACTIVE"}],
    )
    op.bulk_insert(
        sa.table(
            "evidence_references",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("interpretation_id", postgresql.UUID(as_uuid=True)),
            sa.column("citation", sa.Text),
            sa.column("title", sa.String),
            sa.column("url", sa.String),
            sa.column("source", data_source),
            sa.column("source_version", sa.String),
        ),
        [{"id": EVIDENCE_CYP, "interpretation_id": INTERPRETATION_CYP, "citation": "Synthetic evidence reference; not for clinical use.", "title": "GenomixAI synthetic evidence fixture", "url": None, "source": "SYNTHETIC", "source_version": "demo-evidence-1"}],
    )


def downgrade() -> None:
    for table_name in ("evidence_references", "pharmacogenomic_interpretations", "genomic_variants", "genomic_profiles"):
        op.drop_table(table_name)
    bind = op.get_bind()
    for enum_name in ("genomic_record_status_enum", "genomic_validation_status_enum", "genomic_data_source_enum"):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
