from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.assessments import router as assessment_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.clinical import router as clinical_router
from app.api.decisions import router as decision_router
from app.api.genomics import router as genomics_router
from app.api.knowledge import router as knowledge_router
from app.api.medications import router as medication_router
from app.api.notifications import router as notification_router
from app.api.patients import router as patient_router
from app.api.reports import router as report_router
from app.api.reviews import router as review_router
from app.api.timeline import router as timeline_router
from app.core.config import Settings, get_settings
from app.core.exceptions import exception_handlers
from app.core.logging import configure_logging
from app.db.session import get_db, verify_database_connection


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)

    application = FastAPI(title=runtime_settings.project_name)
    application.state.settings = runtime_settings
    application.include_router(auth_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(assessment_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(audit_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(decision_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(patient_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(report_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(review_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(clinical_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(genomics_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(knowledge_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(medication_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(notification_router, prefix=runtime_settings.api_v1_prefix)
    application.include_router(timeline_router, prefix=runtime_settings.api_v1_prefix)
    for exception_type, handler in exception_handlers().items():
        application.add_exception_handler(exception_type, handler)

    if runtime_settings.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=runtime_settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Correlation-ID"],
        )

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "genomixai-backend"}

    @application.get(f"{runtime_settings.api_v1_prefix}/health/database", tags=["health"])
    async def database_health(
        session: AsyncSession = Depends(get_db),  # noqa: B008 - FastAPI dependency declaration.
    ) -> dict[str, str]:
        await verify_database_connection(session)
        return {"status": "ok", "database": "ok", "service": "genomixai-backend"}

    return application


app = create_app()

__all__ = ["app", "create_app"]
