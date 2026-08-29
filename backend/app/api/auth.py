from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.authorization import require_authenticated_user
from app.core.config import Settings, get_request_settings
from app.core.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.db.session import get_db
from app.models import (
    Department,
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
    RevokedToken,
    Role,
    User,
    UserStatus,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    status: UserStatus


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    status: OrganizationStatus


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    status: OrganizationStatus


class MembershipResponse(BaseModel):
    id: UUID
    organization: OrganizationResponse
    department: DepartmentResponse | None
    role: Role
    status: MembershipStatus


class MeResponse(BaseModel):
    user: UserResponse
    membership: MembershipResponse | None
    memberships: list[MembershipResponse]


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008 - FastAPI dependency declaration.
    settings: Settings = Depends(get_request_settings),  # noqa: B008
) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == credentials.email.strip().lower()))
    # Keep this response identical for unknown and invalid accounts.
    if user is None or user.status is not UserStatus.ACTIVE:
        raise _invalid_login()
    if not verify_password(credentials.password, user.password_hash):
        raise _invalid_login()

    token, expires_at, _ = create_access_token(user.id, settings)
    return TokenResponse(access_token=token, expires_at=expires_at)


@router.get("/me", response_model=MeResponse)
async def me(
    user: User = Depends(require_authenticated_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MeResponse:
    memberships = (
        await db.scalars(
            select(OrganizationMembership)
            .options(
                joinedload(OrganizationMembership.organization),
                joinedload(OrganizationMembership.department),
            )
            .join(Organization)
            .outerjoin(Department, OrganizationMembership.department_id == Department.id)
            .where(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.status == MembershipStatus.ACTIVE,
                Organization.status == OrganizationStatus.ACTIVE,
                (OrganizationMembership.department_id.is_(None))
                | (Department.organization_id == OrganizationMembership.organization_id),
            )
            .order_by(OrganizationMembership.created_at)
        )
    ).all()
    serialized = [_membership_response(membership) for membership in memberships]
    return MeResponse(
        user=UserResponse.model_validate(user),
        membership=serialized[0] if serialized else None,
        memberships=serialized,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_request_settings),  # noqa: B008
) -> Response:
    del request
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _authentication_required()
    try:
        claims = decode_access_token(credentials.credentials, settings)
    except TokenError as exc:
        raise _authentication_required() from exc

    jti = str(claims["jti"])
    already_revoked = await db.get(RevokedToken, jti)
    if already_revoked is None:
        db.add(
            RevokedToken(
                jti=jti,
                expires_at=datetime.fromtimestamp(float(claims["exp"]), tz=UTC),
            )
        )
        await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


def _membership_response(membership: OrganizationMembership) -> MembershipResponse:
    return MembershipResponse(
        id=membership.id,
        organization=OrganizationResponse.model_validate(membership.organization),
        department=(
            DepartmentResponse.model_validate(membership.department)
            if membership.department is not None
            else None
        ),
        role=membership.role,
        status=membership.status,
    )


def _invalid_login() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _authentication_required() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


__all__ = ["MeResponse", "LoginRequest", "TokenResponse", "router"]
