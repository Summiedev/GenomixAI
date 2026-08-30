import httpx
import pytest

from app.clinical_engine.knowledge import load_cardiovascular_knowledge
from app.clinical_engine.knowledge.loader import ClaimCategory, EvidenceStatus
from app.core.authorization import require_authenticated_user
from app.core.config import Settings
from app.main import create_app
from scripts.seed_synthetic_patients import genotype_fixture, validate_count


def test_curated_knowledge_has_verified_five_drug_scope() -> None:
    knowledge = load_cardiovascular_knowledge()

    assert {drug.generic_name: drug.rxnorm_rxcui for drug in knowledge.drugs} == {
        "clopidogrel": "32968",
        "warfarin": "11289",
        "simvastatin": "36567",
        "atorvastatin": "83367",
        "metoprolol": "6918",
    }
    assert all(claim.source_refs for claim in knowledge.claims)
    assert all(source.source_version for source in knowledge.sources)
    assert all(source.accessed_date for source in knowledge.sources)


def test_each_drug_has_required_claim_categories_and_evidence_gaps() -> None:
    knowledge = load_cardiovascular_knowledge()
    required = {
        ClaimCategory.INDICATION,
        ClaimCategory.PHARMACOGENOMIC_EFFECT,
        ClaimCategory.CONTRAINDICATION,
        ClaimCategory.DRUG_INTERACTION,
        ClaimCategory.DOSE_CONSIDERATION,
        ClaimCategory.MONITORING,
        ClaimCategory.ALTERNATIVE,
        ClaimCategory.EVIDENCE_GAP,
    }

    for drug in knowledge.drugs:
        claims = [claim for claim in knowledge.claims if claim.drug_id == drug.drug_id]
        assert required <= {claim.category for claim in claims}


def test_fda_evidence_sections_are_not_collapsed_into_one_score() -> None:
    knowledge = load_cardiovascular_knowledge()
    by_id = {claim.claim_id: claim for claim in knowledge.claims}

    clopidogrel_levels = {
        reference.native_evidence_level
        for reference in by_id["clopidogrel.cyp2c19.im-pm.acs-pci"].source_refs
    }
    simvastatin_levels = {
        reference.native_evidence_level
        for reference in by_id["simvastatin.pgx.slco1b1"].source_refs
    }
    atorvastatin_levels = {
        reference.native_evidence_level
        for reference in by_id["atorvastatin.pgx.slco1b1"].source_refs
    }

    assert "FDA Table Section 1" in clopidogrel_levels
    assert "FDA Table Section 2" in simvastatin_levels
    assert any(level.startswith("FDA Table Section 3") for level in atorvastatin_levels)
    assert (
        by_id["atorvastatin.gap.fda-clinical-impact"].evidence_status is EvidenceStatus.INSUFFICIENT
    )
    assert by_id["metoprolol.pgx.cyp2d6-um-gap"].recommendation == (
        "No genotype-specific recommendation."
    )


@pytest.mark.parametrize("count", [50, 100, 200])
def test_synthetic_patient_count_bounds(count: int) -> None:
    assert validate_count(count) == count


@pytest.mark.parametrize("count", [0, 49, 201, 1000])
def test_synthetic_patient_count_rejects_out_of_range(count: int) -> None:
    with pytest.raises(ValueError, match="between 50 and 200"):
        validate_count(count)


def test_synthetic_genotypes_are_labeled_and_not_interpretations() -> None:
    calls = genotype_fixture(2)

    assert {call["gene"] for call in calls} == {
        "CYP2C19",
        "CYP2C9",
        "VKORC1",
        "CYP4F2",
        "SLCO1B1",
        "CYP2D6",
    }
    assert all(call["genotype"] for call in calls)


@pytest.mark.asyncio
async def test_claim_level_knowledge_is_available_from_read_only_api() -> None:
    application = create_app(
        Settings(database_url="postgresql+asyncpg://unused/unused", jwt_secret="test-secret")
    )
    application.dependency_overrides[require_authenticated_user] = lambda: object()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/knowledge/cardiovascular-pgx")

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_version"] == "2026.08.30"
    assert len(payload["drugs"]) == 5
    assert len(payload["claims"]) == 44
