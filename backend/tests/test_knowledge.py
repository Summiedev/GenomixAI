import httpx
import pytest
from sqlalchemy import select

from app.db.session import get_db
from app.main import create_app
from app.models import (
    KnowledgeStatus,
    Medication,
    PharmacogenomicRule,
)


async def knowledge_client(db_session, settings):
    application = create_app(settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://test")


async def auth_headers(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "physician.a@genomixai.demo", "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_knowledge_retrieval_versioning_and_unknown_drug(db_session, settings) -> None:
    clopidogrel = await db_session.scalar(
        select(Medication).where(Medication.generic_name == "Clopidogrel")
    )
    assert clopidogrel is not None
    async with await knowledge_client(db_session, settings) as client:
        headers = await auth_headers(client)
        rules = await client.get(
            "/api/v1/knowledge/pharmacogenomic-rules",
            params={"medication_id": str(clopidogrel.id)},
            headers=headers,
        )
        interactions = await client.get(
            "/api/v1/knowledge/drug-interactions",
            params={"medication_id": str(clopidogrel.id)},
            headers=headers,
        )
        unknown = await client.get(
            "/api/v1/knowledge/pharmacogenomic-rules",
            params={"medication_id": "00000000-0000-0000-0000-000000000000"},
            headers=headers,
        )

    assert rules.status_code == 200
    assert len(rules.json()) == 2
    assert {item["phenotype_condition"] for item in rules.json()} == {
        "INTERMEDIATE_METABOLIZER",
        "POOR_METABOLIZER",
    }
    assert all(item["evidence_source"]["source_version"] == "2022 Update" for item in rules.json())
    assert interactions.status_code == 200
    assert interactions.json()[0]["evidence_source"]["organization"].startswith("U.S. Food")
    assert unknown.status_code == 200
    assert unknown.json() == []


@pytest.mark.asyncio
async def test_inactive_rule_is_not_retrieved(db_session, settings) -> None:
    rule = await db_session.scalar(select(PharmacogenomicRule).limit(1))
    assert rule is not None
    original_status = rule.status
    rule.status = KnowledgeStatus.INACTIVE
    await db_session.commit()
    try:
        async with await knowledge_client(db_session, settings) as client:
            headers = await auth_headers(client)
            response = await client.get(
                "/api/v1/knowledge/pharmacogenomic-rules",
                params={"gene": rule.gene},
                headers=headers,
            )
        assert response.status_code == 200
        assert all(item["id"] != str(rule.id) for item in response.json())
    finally:
        rule.status = original_status
        await db_session.commit()
