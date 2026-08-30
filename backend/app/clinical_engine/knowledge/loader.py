"""Schema and loader for the curated cardiovascular PGx knowledge base."""

import json
from datetime import date
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class ClaimCategory(StrEnum):
    INDICATION = "INDICATION"
    PHARMACOGENOMIC_EFFECT = "PHARMACOGENOMIC_EFFECT"
    CONTRAINDICATION = "CONTRAINDICATION"
    DRUG_INTERACTION = "DRUG_INTERACTION"
    DOSE_CONSIDERATION = "DOSE_CONSIDERATION"
    MONITORING = "MONITORING"
    ALTERNATIVE = "ALTERNATIVE"
    EVIDENCE_GAP = "EVIDENCE_GAP"


class EvidenceStatus(StrEnum):
    ACTIONABLE = "ACTIONABLE"
    SUPPORTED = "SUPPORTED"
    LIMITED = "LIMITED"
    INSUFFICIENT = "INSUFFICIENT"
    REGULATORY_LABEL = "REGULATORY_LABEL"


class EvidenceSourceRecord(BaseModel):
    source_id: str
    publisher: str
    title: str
    source_type: str
    source_version: str
    publication_date: date | None = None
    accessed_date: date
    url: str
    identifiers: list[str] = Field(default_factory=list)
    notes: str | None = None


class DrugRecord(BaseModel):
    drug_id: str
    generic_name: str
    rxnorm_rxcui: str
    rxnorm_term_type: str = "IN"
    therapeutic_area: str = "CARDIOVASCULAR"


class ClaimSourceReference(BaseModel):
    source_id: str
    locator: str
    native_evidence_level: str
    source_specific_note: str | None = None


class KnowledgeClaim(BaseModel):
    claim_id: str
    drug_id: str
    category: ClaimCategory
    statement: str
    evidence_status: EvidenceStatus
    gene: str | None = None
    phenotype_or_genotype: str | None = None
    indication_scope: str | None = None
    interacting_substance: str | None = None
    recommendation: str | None = None
    limitations: str | None = None
    source_refs: list[ClaimSourceReference] = Field(min_length=1)


class CardiovascularKnowledgeBase(BaseModel):
    schema_version: str
    dataset_id: str
    dataset_version: str
    title: str
    curated_on: date
    review_due: date
    clinical_status: str
    disclaimer: str
    sources: list[EvidenceSourceRecord]
    drugs: list[DrugRecord]
    claims: list[KnowledgeClaim]

    @model_validator(mode="after")
    def validate_relations(self) -> "CardiovascularKnowledgeBase":
        source_ids = {source.source_id for source in self.sources}
        drug_ids = {drug.drug_id for drug in self.drugs}
        if len(source_ids) != len(self.sources):
            raise ValueError("source_id values must be unique")
        if len(drug_ids) != len(self.drugs):
            raise ValueError("drug_id values must be unique")
        if len(self.drugs) != 5:
            raise ValueError("the initial cardiovascular dataset must contain exactly five drugs")
        claim_ids: set[str] = set()
        for claim in self.claims:
            if claim.claim_id in claim_ids:
                raise ValueError(f"duplicate claim_id: {claim.claim_id}")
            claim_ids.add(claim.claim_id)
            if claim.drug_id not in drug_ids:
                raise ValueError(f"unknown drug_id in claim {claim.claim_id}")
            for reference in claim.source_refs:
                if reference.source_id not in source_ids:
                    raise ValueError(
                        f"unknown source_id {reference.source_id} in claim {claim.claim_id}"
                    )
        return self


DATA_PATH = Path(__file__).with_name("cardiovascular_pgx.v1.json")


@lru_cache(maxsize=1)
def load_cardiovascular_knowledge() -> CardiovascularKnowledgeBase:
    """Load and validate the repository-pinned curated dataset."""

    with DATA_PATH.open(encoding="utf-8") as source_file:
        return CardiovascularKnowledgeBase.model_validate(json.load(source_file))


__all__ = [
    "CardiovascularKnowledgeBase",
    "ClaimCategory",
    "EvidenceStatus",
    "load_cardiovascular_knowledge",
]
