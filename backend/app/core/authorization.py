from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import get_settings
from app.core.security import TokenError, decode_access_token
from app.db.session import get_db
from app.models.identity import (
    MembershipStatus,
    OrganizationMembership,
    RevokedToken,
    Role,
    User,
    UserStatus,
)
from app.models.organization import Department, Organization, OrganizationStatus

bearer_scheme = HTTPBearer(auto_error=False)


async def get_authenticated_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> UUID:
    """Resolve the principal from a signed bearer token or trusted server state."""

    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        try:
            return UUID(str(user_id))
        except ValueError as exc:
            raise _authentication_required("Invalid principal") from exc

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _authentication_required()
    settings = getattr(request.app.state, "settings", None) or get_settings()
    try:
        claims = decode_access_token(credentials.credentials, settings)
        token_id = str(claims["jti"])
        revoked = await db.get(RevokedToken, token_id)
        if revoked is not None:
            raise TokenError("Token has been revoked")
        return UUID(str(claims["sub"]))
    except (TokenError, ValueError, KeyError) as exc:
        raise _authentication_required() from exc


async def require_authenticated_user(
    user_id: UUID = Depends(get_authenticated_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await db.scalar(select(User).where(User.id == user_id, User.status == UserStatus.ACTIVE))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user not found"
        )
    return user


async def resolve_organization_membership(
    db: AsyncSession, user_id: UUID, organization_id: UUID
) -> OrganizationMembership:
    membership = await db.scalar(
        select(OrganizationMembership)
        .options(
            joinedload(OrganizationMembership.user),
            joinedload(OrganizationMembership.organization),
            joinedload(OrganizationMembership.department),
        )
        .join(Organization)
        .join(User)
        .outerjoin(Department, OrganizationMembership.department_id == Department.id)
        .where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.status == MembershipStatus.ACTIVE,
            Organization.status == OrganizationStatus.ACTIVE,
            User.status == UserStatus.ACTIVE,
            (OrganizationMembership.department_id.is_(None))
            | (Department.organization_id == organization_id),
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active organization membership required",
        )
    return membership


async def require_organization_membership(
    organization_id: UUID,
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationMembership:
    return await resolve_organization_membership(db, user.id, organization_id)


def require_role(*roles: Role):
    allowed_roles = {Role(role) for role in roles}

    async def dependency(
        membership: OrganizationMembership = Depends(require_organization_membership),
    ) -> OrganizationMembership:
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient organization role",
            )
        return membership

    return dependency


def _authentication_required(detail: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


__all__ = [
    "get_authenticated_user_id",
    "require_authenticated_user",
    "require_organization_membership",
    "require_role",
    "resolve_organization_membership",
]
