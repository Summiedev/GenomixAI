from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.authorization import (
    require_organization_membership,
    require_role,
    resolve_organization_membership,
)
from app.models import (
    Department,
    MembershipStatus,
    Organization,
    OrganizationMembership,
    Role,
    User,
    UserStatus,
)


async def get_seeded_user(db_session, email: str) -> User:
    return await db_session.scalar(select(User).where(User.email == email))


async def get_seeded_organization(db_session, slug: str) -> Organization:
    return await db_session.scalar(select(Organization).where(Organization.slug == slug))


@pytest.mark.asyncio
async def test_physician_membership_resolves_correctly(db_session) -> None:
    user = await get_seeded_user(db_session, "physician.a@genomixai.demo")
    organization = await get_seeded_organization(db_session, "hospital-a")

    membership = await resolve_organization_membership(db_session, user.id, organization.id)

    assert membership.role is Role.PHYSICIAN
    assert membership.status is MembershipStatus.ACTIVE


@pytest.mark.asyncio
async def test_pharmacist_membership_resolves_correctly(db_session) -> None:
    user = await get_seeded_user(db_session, "pharmacist.a@genomixai.demo")
    organization = await get_seeded_organization(db_session, "hospital-a")

    membership = await resolve_organization_membership(db_session, user.id, organization.id)

    assert membership.role is Role.CLINICAL_PHARMACIST


@pytest.mark.asyncio
async def test_inactive_membership_is_denied(db_session) -> None:
    user = await get_seeded_user(db_session, "physician.a@genomixai.demo")
    organization = await get_seeded_organization(db_session, "hospital-a")
    membership = await resolve_organization_membership(db_session, user.id, organization.id)
    membership.status = MembershipStatus.INACTIVE
    await db_session.commit()

    with pytest.raises(HTTPException) as error:
        await require_organization_membership(organization.id, user, db_session)

    assert error.value.status_code == 403
    membership.status = MembershipStatus.ACTIVE
    await db_session.commit()


@pytest.mark.asyncio
async def test_user_without_membership_is_denied(db_session) -> None:
    user = User(
        email=f"unassigned-{uuid4()}@genomixai.demo",
        full_name="Unassigned User",
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    await db_session.commit()
    organization = await get_seeded_organization(db_session, "hospital-a")

    with pytest.raises(HTTPException) as error:
        await resolve_organization_membership(db_session, user.id, organization.id)

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_role_checks_work(db_session) -> None:
    physician = await get_seeded_user(db_session, "physician.a@genomixai.demo")
    pharmacist = await get_seeded_user(db_session, "pharmacist.a@genomixai.demo")
    organization = await get_seeded_organization(db_session, "hospital-a")
    physician_membership = await resolve_organization_membership(
        db_session, physician.id, organization.id
    )
    pharmacist_membership = await resolve_organization_membership(
        db_session, pharmacist.id, organization.id
    )

    physician_only = require_role(Role.PHYSICIAN)
    assert await physician_only(physician_membership) is physician_membership
    with pytest.raises(HTTPException) as error:
        await physician_only(pharmacist_membership)
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_department_relationship_works(db_session) -> None:
    user = await get_seeded_user(db_session, "physician.a@genomixai.demo")
    organization = await get_seeded_organization(db_session, "hospital-a")
    membership = await resolve_organization_membership(db_session, user.id, organization.id)

    assert membership.department is not None
    assert membership.department.name == "Cardiology"
    assert membership.department.organization_id == organization.id


@pytest.mark.asyncio
async def test_organization_relationship_works(db_session) -> None:
    user = await get_seeded_user(db_session, "pharmacist.a@genomixai.demo")
    organization = await get_seeded_organization(db_session, "hospital-a")
    membership = await resolve_organization_membership(db_session, user.id, organization.id)

    assert membership.organization.name == "Hospital A"
    assert membership.user.email == user.email


@pytest.mark.asyncio
async def test_user_can_have_multiple_organization_memberships(db_session) -> None:
    user = await get_seeded_user(db_session, "physician.a@genomixai.demo")
    hospital_b = await get_seeded_organization(db_session, "hospital-b")
    cardiology_b = await db_session.scalar(
        select(Department).where(
            Department.organization_id == hospital_b.id,
            Department.slug == "cardiology",
        )
    )
    db_session.add(
        OrganizationMembership(
            user_id=user.id,
            organization_id=hospital_b.id,
            department_id=cardiology_b.id,
            role=Role.PHYSICIAN,
            status=MembershipStatus.ACTIVE,
        )
    )
    await db_session.commit()

    memberships = (
        await db_session.scalars(
            select(OrganizationMembership).where(OrganizationMembership.user_id == user.id)
        )
    ).all()
    assert len(memberships) == 2
