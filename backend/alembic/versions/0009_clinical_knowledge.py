"""Add provenance-backed clinical knowledge rules."""

from datetime import date
from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MED_CLOPIDOGREL = UUID("00000000-0000-0000-0000-00000000e003")
MED_OMEPRAZOLE = UUID("00000000-0000-0000-0000-00000000f001")
MED_GEMFIBROZIL = UUID("00000000-0000-0000-0000-00000000f002")
MED_AMLODIPINE = UUID("00000000-0000-0000-0000-00000000f003")
SRC_CPIC_CLOPIDOGREL = UUID("00000000-0000-0000-0000-00000000f101")
SRC_FDA_CLOPIDOGREL = UUID("00000000-0000-0000-0000-00000000f102")
SRC_FDA_SIMVASTATIN = UUID("00000000-0000-0000-0000-00000000f103")
RULE_PGX_INTERMEDIATE = UUID("00000000-0000-0000-0000-00000000f201")
RULE_PGX_POOR = UUID("00000000-0000-0000-0000-00000000f202")
RULE_DDI_CLOPIDOGREL_OMEPRAZOLE = UUID("00000000-0000-0000-0000-00000000f301")
RULE_DDI_SIMVASTATIN_GEMFIBROZIL = UUID("00000000-0000-0000-0000-00000000f302")
RULE_DOSE_SIMVASTATIN_AMLODIPINE = UUID("00000000-0000-0000-0000-00000000f401")


def upgrade() -> None:
    bind = op.get_bind()
    enum_definitions = (
        postgresql.ENUM(
            "ACTIVE", "INACTIVE", name="knowledge_status_enum", create_type=False
        ),
        postgresql.ENUM(
            "STRONG", "MODERATE", "LIMITED", "INSUFFICIENT",
            name="evidence_level_enum", create_type=False,
        ),
        postgresql.ENUM(
            "AVOID", "ALTERNATIVE", "CONSIDER", "MONITOR", "INFORMATIONAL",
            "INSUFFICIENT_EVIDENCE", name="recommendation_classification_enum", create_type=False,
        ),
        postgresql.ENUM(
            "CLINICAL_GUIDELINE", "REGULATORY_LABEL", "PEER_REVIEWED", "RESEARCH_DATASET",
            name="evidence_source_type_enum", create_type=False,
        ),
        postgresql.ENUM(
            "CONDITION", "MEDICATION", "ALLERGY", "LAB", "VITAL", "DEMOGRAPHIC",
            name="rule_condition_type_enum", create_type=False,
        ),
        postgresql.ENUM(
            "EQUALS", "CONTAINS", "GREATER_THAN", "GREATER_THAN_OR_EQUAL",
            "LESS_THAN", "LESS_THAN_OR_EQUAL", name="comparison_operator_enum", create_type=False,
        ),
    )
    for enum_type in enum_definitions:
        enum_type.create(bind, checkfirst=True)

    knowledge_status = enum_definitions[0]
    evidence_level = enum_definitions[1]
    recommendation_classification = enum_definitions[2]
    source_type = enum_definitions[3]
    condition_type = enum_definitions[4]
    comparison_operator = enum_definitions[5]

    op.create_table(
        "evidence_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("source_version", sa.String(length=150), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("reference_identifier", sa.String(length=300), nullable=True),
        sa.Column("status", knowledge_status, server_default="ACTIVE", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evidence_source_organization_title", "evidence_sources", ["organization", "title"]
    )

    def rule_columns() -> list[sa.Column]:
        return [
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("medication_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("evidence_source_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("effective_date", sa.Date(), nullable=True),
            sa.Column("review_date", sa.Date(), nullable=True),
            sa.Column("status", knowledge_status, server_default="ACTIVE", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        ]

    op.create_table(
        "pharmacogenomic_rules",
        *rule_columns()[:2],
        sa.Column("gene", sa.String(length=50), nullable=False),
        sa.Column("phenotype_condition", sa.String(length=150), nullable=True),
        sa.Column("genotype_condition", sa.String(length=150), nullable=True),
        sa.Column("clinical_implication", sa.Text(), nullable=False),
        sa.Column("recommendation_classification", recommendation_classification, nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("evidence_level", evidence_level, nullable=False),
        *rule_columns()[2:],
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_pgx_rule_medication_gene_status", "pharmacogenomic_rules",
        ["medication_id", "gene", "status"],
    )

    op.create_table(
        "drug_drug_interactions",
        *rule_columns()[:2],
        sa.Column("interacting_medication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinical_effect", sa.Text(), nullable=False),
        sa.Column("recommendation_classification", recommendation_classification, nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("evidence_level", evidence_level, nullable=False),
        *rule_columns()[2:],
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interacting_medication_id"], ["medications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ddi_medication_pair_status", "drug_drug_interactions",
        ["medication_id", "interacting_medication_id", "status"],
    )

    op.create_table(
        "contraindication_rules",
        *rule_columns()[:2],
        sa.Column("target_type", condition_type, nullable=False),
        sa.Column("target_value", sa.String(length=200), nullable=False),
        sa.Column("operator", comparison_operator, server_default="EQUALS", nullable=False),
        sa.Column("clinical_implication", sa.Text(), nullable=False),
        sa.Column("recommendation_classification", recommendation_classification, nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("evidence_level", evidence_level, nullable=False),
        *rule_columns()[2:],
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contraindication_rule_medication_target", "contraindication_rules",
        ["medication_id", "target_type", "status"],
    )

    op.create_table(
        "dose_rules",
        *rule_columns()[:2],
        sa.Column("factor_type", condition_type, nullable=False),
        sa.Column("factor_value", sa.String(length=200), nullable=False),
        sa.Column("operator", comparison_operator, nullable=False),
        sa.Column("maximum_dose", sa.Numeric(12, 4), nullable=True),
        sa.Column("minimum_dose", sa.Numeric(12, 4), nullable=True),
        sa.Column("dose_unit", sa.String(length=30), nullable=True),
        sa.Column("clinical_implication", sa.Text(), nullable=False),
        sa.Column("recommendation_classification", recommendation_classification, nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("evidence_level", evidence_level, nullable=False),
        *rule_columns()[2:],
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dose_rule_medication_factor", "dose_rules", ["medication_id", "factor_value", "status"]
    )

    op.create_table(
        "monitoring_rules",
        *rule_columns()[:2],
        sa.Column("factor_type", condition_type, nullable=False),
        sa.Column("factor_value", sa.String(length=200), nullable=False),
        sa.Column("operator", comparison_operator, nullable=False),
        sa.Column("threshold", sa.Numeric(12, 4), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("clinical_implication", sa.Text(), nullable=False),
        sa.Column("recommendation_classification", recommendation_classification, nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("evidence_level", evidence_level, nullable=False),
        *rule_columns()[2:],
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_monitoring_rule_medication_factor", "monitoring_rules",
        ["medication_id", "factor_value", "status"],
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
            sa.column("status", postgresql.ENUM("ACTIVE", "INACTIVE", name="medication_status_enum", create_type=False)),
        ),
        [
            {"id": MED_OMEPRAZOLE, "standardized_code": "RXNORM:7646", "generic_name": "Omeprazole", "brand_name": "Prilosec", "strength": "20 mg", "dosage_form": "CAPSULE", "status": "ACTIVE"},
            {"id": MED_GEMFIBROZIL, "standardized_code": "RXNORM:3101", "generic_name": "Gemfibrozil", "brand_name": "Lopid", "strength": "600 mg", "dosage_form": "TABLET", "status": "ACTIVE"},
            {"id": MED_AMLODIPINE, "standardized_code": "RXNORM:308135", "generic_name": "Amlodipine", "brand_name": "Norvasc", "strength": "5 mg", "dosage_form": "TABLET", "status": "ACTIVE"},
        ],
    )

    op.bulk_insert(
        sa.table(
            "evidence_sources",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("organization", sa.String),
            sa.column("title", sa.String),
            sa.column("source_type", source_type),
            sa.column("source_version", sa.String),
            sa.column("effective_date", sa.Date),
            sa.column("review_date", sa.Date),
            sa.column("source_url", sa.String),
            sa.column("reference_identifier", sa.String),
            sa.column("status", knowledge_status),
            sa.column("notes", sa.Text),
        ),
        [
            {"id": SRC_CPIC_CLOPIDOGREL, "organization": "Clinical Pharmacogenetics Implementation Consortium", "title": "CPIC Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update", "source_type": "CLINICAL_GUIDELINE", "source_version": "2022 Update", "effective_date": date(2022, 1, 1), "review_date": None, "source_url": "https://files.cpicpgx.org/data/guideline/publication/clopidogrel/2022/35034351.pdf", "reference_identifier": "PMID:35034351", "status": "ACTIVE", "notes": "Use only as clinician-reviewed decision support; indication-specific recommendations apply."},
            {"id": SRC_FDA_CLOPIDOGREL, "organization": "U.S. Food and Drug Administration / DailyMed", "title": "Clopidogrel Tablets, USP Prescribing Information", "source_type": "REGULATORY_LABEL", "source_version": "Current DailyMed label", "effective_date": None, "review_date": None, "source_url": "https://dailymed.nlm.nih.gov/dailymed/fda/fdaDrugXsl.cfm?setid=994dc0b4-0158-45db-965f-db827296f619&type=display", "reference_identifier": "Sections 2.4, 5.1, 7.1", "status": "ACTIVE", "notes": "Label states to avoid concomitant omeprazole or esomeprazole with clopidogrel."},
            {"id": SRC_FDA_SIMVASTATIN, "organization": "U.S. Food and Drug Administration / DailyMed", "title": "Simvastatin Tablets USP Prescribing Information", "source_type": "REGULATORY_LABEL", "source_version": "DailyMed label updated 2026-05-20", "effective_date": None, "review_date": None, "source_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5ae78a86-ccca-4714-b77e-7bc885b674b5", "reference_identifier": "Sections 2.5, 4, 5.1, 7.1", "status": "ACTIVE", "notes": "Label states that gemfibrozil coadministration is contraindicated and sets dose limits with amlodipine."},
        ],
    )

    op.bulk_insert(
        sa.table(
            "pharmacogenomic_rules",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("medication_id", postgresql.UUID(as_uuid=True)),
            sa.column("gene", sa.String),
            sa.column("phenotype_condition", sa.String),
            sa.column("genotype_condition", sa.String),
            sa.column("clinical_implication", sa.Text),
            sa.column("recommendation_classification", recommendation_classification),
            sa.column("recommendation_text", sa.Text),
            sa.column("evidence_level", evidence_level),
            sa.column("evidence_source_id", postgresql.UUID(as_uuid=True)),
            sa.column("effective_date", sa.Date),
            sa.column("review_date", sa.Date),
            sa.column("status", knowledge_status),
        ),
        [
            {"id": RULE_PGX_INTERMEDIATE, "medication_id": MED_CLOPIDOGREL, "gene": "CYP2C19", "phenotype_condition": "INTERMEDIATE_METABOLIZER", "genotype_condition": None, "clinical_implication": "Reduced clopidogrel active-metabolite formation and increased on-treatment platelet reactivity are described for this phenotype.", "recommendation_classification": "ALTERNATIVE", "recommendation_text": "For ACS and/or PCI, avoid standard-dose clopidogrel if possible and consider an alternative P2Y12 inhibitor at standard dose when clinically indicated and without a contraindication.", "evidence_level": "STRONG", "evidence_source_id": SRC_CPIC_CLOPIDOGREL, "effective_date": date(2022, 1, 1), "review_date": None, "status": "ACTIVE"},
            {"id": RULE_PGX_POOR, "medication_id": MED_CLOPIDOGREL, "gene": "CYP2C19", "phenotype_condition": "POOR_METABOLIZER", "genotype_condition": None, "clinical_implication": "Significantly reduced clopidogrel active-metabolite formation and increased on-treatment platelet reactivity are described for this phenotype.", "recommendation_classification": "ALTERNATIVE", "recommendation_text": "For ACS and/or PCI, avoid clopidogrel if possible and consider an alternative P2Y12 inhibitor at standard dose when clinically indicated and without a contraindication.", "evidence_level": "STRONG", "evidence_source_id": SRC_CPIC_CLOPIDOGREL, "effective_date": date(2022, 1, 1), "review_date": None, "status": "ACTIVE"},
        ],
    )

    op.bulk_insert(
        sa.table(
            "drug_drug_interactions",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("medication_id", postgresql.UUID(as_uuid=True)),
            sa.column("interacting_medication_id", postgresql.UUID(as_uuid=True)),
            sa.column("clinical_effect", sa.Text),
            sa.column("recommendation_classification", recommendation_classification),
            sa.column("recommendation_text", sa.Text),
            sa.column("evidence_level", evidence_level),
            sa.column("evidence_source_id", postgresql.UUID(as_uuid=True)),
            sa.column("effective_date", sa.Date),
            sa.column("review_date", sa.Date),
            sa.column("status", knowledge_status),
        ),
        [
            {"id": RULE_DDI_CLOPIDOGREL_OMEPRAZOLE, "medication_id": MED_CLOPIDOGREL, "interacting_medication_id": MED_OMEPRAZOLE, "clinical_effect": "Omeprazole reduces clopidogrel active-metabolite concentrations and antiplatelet activity.", "recommendation_classification": "AVOID", "recommendation_text": "Avoid concomitant use of clopidogrel with omeprazole; consider another acid-reducing agent with minimal or no CYP2C19 inhibitory effect when a PPI is required.", "evidence_level": "STRONG", "evidence_source_id": SRC_FDA_CLOPIDOGREL, "effective_date": None, "review_date": None, "status": "ACTIVE"},
            {"id": RULE_DDI_SIMVASTATIN_GEMFIBROZIL, "medication_id": UUID("00000000-0000-0000-0000-00000000e002"), "interacting_medication_id": MED_GEMFIBROZIL, "clinical_effect": "Concomitant use increases the risk of myopathy and rhabdomyolysis.", "recommendation_classification": "AVOID", "recommendation_text": "Do not coadminister simvastatin with gemfibrozil; select therapy only after clinician review of the current label and patient-specific alternatives.", "evidence_level": "STRONG", "evidence_source_id": SRC_FDA_SIMVASTATIN, "effective_date": None, "review_date": None, "status": "ACTIVE"},
        ],
    )

    op.bulk_insert(
        sa.table(
            "dose_rules",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("medication_id", postgresql.UUID(as_uuid=True)),
            sa.column("factor_type", condition_type),
            sa.column("factor_value", sa.String),
            sa.column("operator", comparison_operator),
            sa.column("maximum_dose", sa.Numeric),
            sa.column("minimum_dose", sa.Numeric),
            sa.column("dose_unit", sa.String),
            sa.column("clinical_implication", sa.Text),
            sa.column("recommendation_classification", recommendation_classification),
            sa.column("recommendation_text", sa.Text),
            sa.column("evidence_level", evidence_level),
            sa.column("evidence_source_id", postgresql.UUID(as_uuid=True)),
            sa.column("effective_date", sa.Date),
            sa.column("review_date", sa.Date),
            sa.column("status", knowledge_status),
        ),
        [{"id": RULE_DOSE_SIMVASTATIN_AMLODIPINE, "medication_id": UUID("00000000-0000-0000-0000-00000000e002"), "factor_type": "MEDICATION", "factor_value": "amlodipine", "operator": "EQUALS", "maximum_dose": 20, "minimum_dose": None, "dose_unit": "mg", "clinical_implication": "The simvastatin label limits simvastatin to 20 mg once daily with amlodipine.", "recommendation_classification": "CONSIDER", "recommendation_text": "Do not exceed simvastatin 20 mg once daily when amlodipine is coadministered.", "evidence_level": "STRONG", "evidence_source_id": SRC_FDA_SIMVASTATIN, "effective_date": None, "review_date": None, "status": "ACTIVE"}],
    )


def downgrade() -> None:
    for table_name in (
        "monitoring_rules", "dose_rules", "contraindication_rules", "drug_drug_interactions",
        "pharmacogenomic_rules", "evidence_sources",
    ):
        op.drop_table(table_name)
    bind = op.get_bind()
    for enum_name in (
        "comparison_operator_enum", "rule_condition_type_enum", "evidence_source_type_enum",
        "recommendation_classification_enum", "evidence_level_enum", "knowledge_status_enum",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
