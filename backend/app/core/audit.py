"""Small helpers for append-only clinical audit events."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditEvent


def append_audit_event(
    db: AsyncSession,
    *,
    action: AuditAction,
    actor_id: UUID | None,
    organization_id: UUID | None,
    resource_type: str,
    resource_id: UUID | None = None,
    request: Request | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> AuditEvent:
    """Stage one immutable audit event; the caller commits with its business action."""

    request_id = request.headers.get("X-Request-ID") if request is not None else None
    correlation_id = request.headers.get("X-Correlation-ID") if request is not None else None
    event = AuditEvent(
        actor_id=actor_id,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        timestamp=datetime.now(UTC),
        request_id=request_id[:150] if request_id else None,
        correlation_id=correlation_id[:150] if correlation_id else None,
        metadata_json=_safe_metadata(metadata),
    )
    db.add(event)
    return event


def _safe_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    safe: dict[str, Any] = {}
    for key, value in list(metadata.items())[:20]:
        if not isinstance(key, str) or len(key) > 100:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        elif isinstance(value, (list, tuple)) and all(
            isinstance(item, (str, int, float, bool)) or item is None for item in value[:20]
        ):
            safe[key] = list(value[:20])
    return safe


__all__ = ["append_audit_event"]
