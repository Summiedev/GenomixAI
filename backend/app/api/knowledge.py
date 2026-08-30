"""Read-only access to the provenance-backed clinical knowledge layer."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.clinical_engine.knowledge import (
    CardiovascularKnowledgeBase,
    load_cardiovascular_knowledge,
)
from app.core.authorization import require_authenticated_user
from app.db.session import get_db
from app.models import (
    ContraindicationRule,
    DrugDrugInteraction,
    EvidenceLevel,
    EvidenceSourceType,
    KnowledgeStatus,
    PharmacogenomicRule,
    RecommendationClassification,
    RuleConditionType,
    User,
)

router = APIRouter(prefix="/knowledge", tags=["clinical knowledge"])


@router.get("/cardiovascular-pgx", response_model=CardiovascularKnowledgeBase)
async def get_cardiovascular_pgx_knowledge(
    user: User = Depends(require_authenticated_user),  # noqa: B008
) -> CardiovascularKnowledgeBase:
    """Return the repository-pinned, claim-level five-drug starter dataset."""

    del user
    return load_cardiovascular_knowledge()


class EvidenceSourceRead(BaseModel):
    id: UUID
    organization: str
    title: str
    source_type: EvidenceSourceType
    source_version: str | None
    effective_date: date | None
    review_date: date | None
    source_url: str | None
    reference_identifier: str | None


class MedicationReferenceRead(BaseModel):
    id: UUID
    generic_name: str
    brand_name: str | None
    standardized_code: str | None


class PharmacogenomicRuleRead(BaseModel):
    id: UUID
    medication: MedicationReferenceRead
    gene: str
    phenotype_condition: str | None
    genotype_condition: str | None
    clinical_implication: str
    recommendation_classification: RecommendationClassification
    recommendation_text: str
    evidence_level: EvidenceLevel
    evidence_source: EvidenceSourceRead
    effective_date: date | None
    review_date: date | None
    status: KnowledgeStatus


class DrugDrugInteractionRead(BaseModel):
    id: UUID
    medication: MedicationReferenceRead
    interacting_medication: MedicationReferenceRead
    clinical_effect: str
    recommendation_classification: RecommendationClassification
    recommendation_text: str
    evidence_level: EvidenceLevel
    evidence_source: EvidenceSourceRead
    effective_date: date | None
    review_date: date | None
    status: KnowledgeStatus


class ContraindicationRuleRead(BaseModel):
    id: UUID
    medication: MedicationReferenceRead
    target_type: RuleConditionType
    target_value: str
    clinical_implication: str
    recommendation_classification: RecommendationClassification
    recommendation_text: str
    evidence_level: EvidenceLevel
    evidence_source: EvidenceSourceRead
    effective_date: date | None
    review_date: date | None
    status: KnowledgeStatus


def _medication_options():
    return joinedload(PharmacogenomicRule.medication), joinedload(
        PharmacogenomicRule.evidence_source
    )


@router.get("/pharmacogenomic-rules", response_model=list[PharmacogenomicRuleRead])
async def list_pharmacogenomic_rules(
    medication_id: UUID | None = None,
    gene: str | None = Query(default=None, max_length=50),
    user: User = Depends(require_authenticated_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[PharmacogenomicRule]:
    del user
    query = (
        select(PharmacogenomicRule)
        .options(*_medication_options())
        .where(PharmacogenomicRule.status == KnowledgeStatus.ACTIVE)
    )
    if medication_id is not None:
        query = query.where(PharmacogenomicRule.medication_id == medication_id)
    if gene:
        query = query.where(PharmacogenomicRule.gene.ilike(gene.strip()))
    return list((await db.scalars(query.order_by(PharmacogenomicRule.gene))).all())


@router.get("/drug-interactions", response_model=list[DrugDrugInteractionRead])
async def list_drug_interactions(
    medication_id: UUID | None = None,
    interacting_medication_id: UUID | None = None,
    user: User = Depends(require_authenticated_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[DrugDrugInteraction]:
    del user
    query = (
        select(DrugDrugInteraction)
        .options(
            joinedload(DrugDrugInteraction.medication),
            joinedload(DrugDrugInteraction.interacting_medication),
            joinedload(DrugDrugInteraction.evidence_source),
        )
        .where(DrugDrugInteraction.status == KnowledgeStatus.ACTIVE)
    )
    if medication_id is not None:
        query = query.where(
            (DrugDrugInteraction.medication_id == medication_id)
            | (DrugDrugInteraction.interacting_medication_id == medication_id)
        )
    if interacting_medication_id is not None:
        query = query.where(
            (DrugDrugInteraction.medication_id == interacting_medication_id)
            | (DrugDrugInteraction.interacting_medication_id == interacting_medication_id)
        )
    return list((await db.scalars(query.order_by(DrugDrugInteraction.id))).all())


def _simple_rule_options(model):
    return joinedload(model.medication), joinedload(model.evidence_source)


@router.get("/contraindication-rules", response_model=list[ContraindicationRuleRead])
async def list_contraindication_rules(
    medication_id: UUID | None = None,
    user: User = Depends(require_authenticated_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[ContraindicationRule]:
    del user
    query = (
        select(ContraindicationRule)
        .options(*_simple_rule_options(ContraindicationRule))
        .where(ContraindicationRule.status == KnowledgeStatus.ACTIVE)
    )
    if medication_id is not None:
        query = query.where(ContraindicationRule.medication_id == medication_id)
    return list((await db.scalars(query.order_by(ContraindicationRule.id))).all())


__all__ = ["router"]
