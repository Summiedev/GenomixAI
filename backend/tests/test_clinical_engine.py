from types import SimpleNamespace

from app.clinical_engine import (
    AdverseDrugReactionContext,
    AllergyContext,
    ClinicalAssessmentPipeline,
    GenomicFindingContext,
    LabContext,
    MedicationContext,
    PatientClinicalContext,
)
from app.clinical_engine.result import FindingCategory, FindingSeverity


def medication(identifier: str, name: str) -> MedicationContext:
    return MedicationContext(name=name, medication_id=identifier)


def evidence_source() -> SimpleNamespace:
    return SimpleNamespace(
        id="source-1",
        organization="Verified clinical source",
        title="Verified guideline",
        source_type="CLINICAL_GUIDELINE",
        source_version="v1",
        effective_date=None,
        review_date=None,
        source_url="https://example.test/source",
        reference_identifier="REF-1",
    )


def rule(**values: object) -> SimpleNamespace:
    defaults = {
        "id": "rule-1",
        "status": "ACTIVE",
        "recommendation_classification": "CONSIDER",
        "recommendation_text": "Review this result.",
        "clinical_implication": "The result is relevant.",
        "evidence_level": "STRONG",
        "evidence_source": evidence_source(),
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_pgx_relevant_and_irrelevant_findings_are_separate() -> None:
    clopidogrel = medication("clopidogrel", "Clopidogrel")
    pgx_rule = rule(
        id="pgx-1",
        medication=clopidogrel,
        gene="CYP2C19",
        phenotype_condition="POOR_METABOLIZER",
        genotype_condition=None,
        recommendation_classification="ALTERNATIVE",
    )
    pipeline = ClinicalAssessmentPipeline(pharmacogenomic_rules=[pgx_rule])

    relevant = pipeline.assess(
        PatientClinicalContext(
            genomic_findings=[GenomicFindingContext(gene="CYP2C19", phenotype="POOR_METABOLIZER")]
        ),
        [clopidogrel],
    )
    irrelevant = pipeline.assess(
        PatientClinicalContext(
            genomic_findings=[GenomicFindingContext(gene="DPYD", phenotype="POOR_METABOLIZER")]
        ),
        [clopidogrel],
    )

    assert relevant.findings[0].category is FindingCategory.PHARMACOGENOMICS
    assert relevant.findings[0].evidence[0].source_version == "v1"
    assert irrelevant.findings == ()


def test_no_genomic_data_unknown_phenotype_and_missing_evidence_are_safe() -> None:
    clopidogrel = medication("clopidogrel", "Clopidogrel")
    pgx_rule = rule(
        medication=clopidogrel,
        gene="CYP2C19",
        phenotype_condition="POOR_METABOLIZER",
        evidence_source=None,
    )
    pipeline = ClinicalAssessmentPipeline(pharmacogenomic_rules=[pgx_rule])

    no_data = pipeline.assess(PatientClinicalContext(), [clopidogrel])
    unknown = pipeline.assess(
        PatientClinicalContext(genomic_findings=[GenomicFindingContext(gene="CYP2C19")]),
        [clopidogrel],
    )
    no_evidence = pipeline.assess(
        PatientClinicalContext(
            genomic_findings=[GenomicFindingContext(gene="CYP2C19", phenotype="POOR_METABOLIZER")]
        ),
        [clopidogrel],
    )

    assert no_data.findings == ()
    assert unknown.findings[0].metadata["reason"] == "UNKNOWN_PHENOTYPE"
    assert no_evidence.findings[0].classification == "INSUFFICIENT_EVIDENCE"
    assert no_evidence.findings[0].severity is FindingSeverity.UNKNOWN
    assert not no_evidence.has_actionable_findings


def test_multiple_medications_check_both_interaction_directions() -> None:
    clopidogrel = medication("clopidogrel", "Clopidogrel")
    omeprazole = medication("omeprazole", "Omeprazole")
    simvastatin = medication("simvastatin", "Simvastatin")
    existing_interaction = rule(
        id="ddi-existing",
        medication=clopidogrel,
        interacting_medication=omeprazole,
        clinical_effect="Reduced antiplatelet activity.",
        recommendation_classification="AVOID",
    )
    proposed_interaction = rule(
        id="ddi-proposed",
        medication=simvastatin,
        interacting_medication=omeprazole,
        clinical_effect="Increased toxicity risk.",
        recommendation_classification="AVOID",
    )
    result = ClinicalAssessmentPipeline(
        interaction_rules=[existing_interaction, proposed_interaction]
    ).assess(
        PatientClinicalContext(medications=[clopidogrel]),
        [omeprazole, simvastatin],
    )

    assert len(result.findings) == 2
    assert {finding.metadata["pair_type"] for finding in result.findings} == {
        "EXISTING_VS_PROPOSED",
        "PROPOSED_VS_PROPOSED",
    }


def test_allergy_adr_monitoring_and_no_actionable_finding() -> None:
    aspirin = medication("aspirin", "Aspirin")
    simvastatin = medication("simvastatin", "Simvastatin")
    pipeline = ClinicalAssessmentPipeline(
        monitoring_rules=[
            rule(
                id="monitor-alt",
                medication=simvastatin,
                factor_type="LAB",
                factor_value="alt",
                operator="GREATER_THAN",
                threshold=100,
                clinical_implication="The recorded ALT is above the rule threshold.",
                recommendation_classification="MONITOR",
            )
        ]
    )
    context = PatientClinicalContext(
        allergies=[AllergyContext(allergen="Aspirin", reaction="Urticaria", severity="SEVERE")],
        adverse_drug_reactions=[
            AdverseDrugReactionContext(medication="Simvastatin", reaction="Myalgia")
        ],
        labs=[LabContext(test_name="ALT", numeric_value=140, unit="U/L")],
    )
    result = pipeline.assess(context, [aspirin, simvastatin])

    assert {finding.category for finding in result.findings} == {
        FindingCategory.ALLERGY,
        FindingCategory.ADVERSE_DRUG_REACTION,
        FindingCategory.MONITORING,
    }
    assert (
        ClinicalAssessmentPipeline().assess(PatientClinicalContext(), []).overall_classification
        == "NO_ACTION"
    )
