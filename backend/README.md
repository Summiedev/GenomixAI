# GenomixAI Backend

FastAPI backend foundation for GenomixAI. The persistence layer uses PostgreSQL,
SQLAlchemy 2.x async, asyncpg, and Alembic. The application never creates schema
objects on startup; all schema changes are migration-managed.

## Setup

Install Python with `uv`, then create the environment and install dependencies:

```powershell
uv sync --all-groups
Copy-Item .env.example .env
```

Set `DATABASE_URL` in `.env` to an isolated PostgreSQL database that exists and is reachable.
Do not put a real JWT secret in source control.

## Development commands

```powershell
uv run fastapi dev app/main.py
uv run pytest
uv run ruff check .
uv run ruff format .
uv run ruff format --check .
```

## Migrations

```powershell
uv run alembic upgrade head
uv run alembic downgrade -1
```

The initial `migration_probes` table exists only to verify metadata discovery and
migration wiring. It is not a business feature.

## Identity and authentication

Phase 3 stores organizations, departments, users, and organization memberships.
Roles are resolved from active database memberships; they are never inferred from
email addresses or client-side state. A user can have memberships in multiple
organizations.

Phase 4 exposes one professional login portal:

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`

Access tokens are short-lived signed JWTs and logout revokes the token server-side.
Seeded demo users have the password `ChangeMe123!`; replace or disable them before
using a non-development environment.

Patient access is organization-scoped through `PatientOrganizationLink`, which
stores each hospital's MRN. Patient search/details use an authenticated
`organization_id` context:

- `GET /api/v1/patients?organization_id=<uuid>&search=<term>&page=1&page_size=25`
- `GET /api/v1/patients/{patient_id}?organization_id=<uuid>`

Normalized encounter, condition, note, vital, lab, allergy, and adverse-reaction
records are available under `/api/v1/patients/{patient_id}/...`. Their persisted
clinical events power `GET /api/v1/patients/{patient_id}/timeline`, with event-type,
date-range, and pagination filters.

## Health endpoints

- `GET /health` returns application health without requiring the database.
- `GET /api/v1/health/database` runs `SELECT 1` through the async session dependency.
