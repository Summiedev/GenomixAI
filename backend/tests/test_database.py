from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db import session as session_module
from app.db.session import get_db
from app.models import MigrationProbe


@pytest.mark.asyncio
async def test_async_session_can_open(db_session) -> None:
    assert db_session.is_active
    result = await db_session.execute(select(MigrationProbe))
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_transaction_succeeds(db_session) -> None:
    probe = MigrationProbe(name=f"transaction-{uuid4()}")
    async with db_session.begin():
        db_session.add(probe)

    result = await db_session.execute(select(MigrationProbe).where(MigrationProbe.id == probe.id))
    assert result.scalar_one().name == probe.name


@pytest.mark.asyncio
async def test_rollback_works(db_session) -> None:
    probe = MigrationProbe(name=f"rollback-{uuid4()}")
    with pytest.raises(RuntimeError, match="rollback"):
        async with db_session.begin():
            db_session.add(probe)
            raise RuntimeError("rollback")

    result = await db_session.execute(select(MigrationProbe).where(MigrationProbe.id == probe.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_get_db_closes_sessions(monkeypatch) -> None:
    class TrackingSession:
        closed = False

        async def close(self) -> None:
            self.closed = True

    class SessionContext:
        def __init__(self) -> None:
            self.session = TrackingSession()

        async def __aenter__(self) -> TrackingSession:
            return self.session

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

    context = SessionContext()
    monkeypatch.setattr(session_module, "async_session_factory", lambda: context)

    dependency = get_db()
    session = await anext(dependency)
    assert session is context.session
    await dependency.aclose()
    assert context.session.closed is True
