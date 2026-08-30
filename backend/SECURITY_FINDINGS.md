# GenomixAI MVP 1 Security Findings

## Scope

This focused review covered FastAPI route authorization, tenant scoping, JWT
handling, membership status, request validation, CORS, configuration, password
hashing, logging, and the clinical workflow APIs. It is an engineering security
review, not a certification or a claim of HIPAA, GDPR, or NDPR compliance.

## Findings

| ID | Area | Severity | Finding | Disposition |
| --- | --- | --- | --- | --- |
| SEC-01 | Principal resolution | High | Authentication accepted an alternate `request.state.user_id` principal, which could bypass bearer-token resolution if another middleware populated that state. | Fixed: the principal is now derived only from the signed bearer token and server-side user lookup. |
| SEC-02 | CORS | Medium | CORS allowed every method and header and enabled credentials although the application uses bearer headers rather than cookies. | Fixed: explicit methods/headers and credentials disabled; wildcard origins rejected by configuration. |
| SEC-03 | Production configuration | High | A missing or weak JWT secret could allow the application to start with unsafe authentication configuration. | Fixed: production settings require a 32-character secret; token creation still fails closed when no secret is configured. |
| SEC-04 | Object-level authorization | High | Patient, assessment, review, report, audit, notification, and medication-order access must be scoped through the active organization membership and resource organization. | Verified by existing route tests and the PostgreSQL security regression/E2E tests. |
| SEC-05 | Role escalation | High | Physician-only assessment/final-decision actions and pharmacist-only review actions must not be interchangeable. | Verified: role dependencies and workflow transition checks return 403/409 as appropriate. |
| SEC-06 | JWT manipulation | High | Forged, malformed, expired, future-issued, revoked, or algorithm-mismatched tokens must be rejected. | Verified: signature, fixed algorithm, timestamps, revocation, and active-user checks are enforced. |
| SEC-07 | Mass assignment | Medium | Request schemas were reviewed for client-controlled identity and tenant fields. | No exploitable finding: route handlers take actor, organization, creator, and patient ownership from authenticated context/path validation rather than blindly copying those fields. |
| SEC-08 | Sensitive data exposure | Medium | Generic audit metadata and error responses must not contain patient data, passwords, tokens, or tracebacks. | Verified: audit metadata is allow-listed/truncated and malformed identifier responses do not expose traceback or password content. |
| SEC-09 | Password handling | High | Plaintext passwords must never be persisted. | Verified: passwords are stored as salted PBKDF2-SHA256 hashes with 600,000 iterations and constant-time comparison. |
| SEC-10 | Logging | Medium | Application logs must not include credentials or clinical payloads. | Verified in the reviewed code: logging is configuration/startup oriented; ML failures log only exception type, not context or patient data. |

## Residual risks

- Production deployment still needs operational controls outside this repository:
  secret rotation, TLS termination, database encryption/backups, dependency and
  image scanning, rate limiting/lockout, centralized access review, and incident
  response.
- Clinical authorization policy should be reviewed by the product owner before
  expanding hospital-admin or platform-admin privileges.
- The current access token is intentionally short-lived and server-revocable;
  refresh tokens and device/session management are not part of this MVP review.

## Verification

The regression suite covers cross-tenant patient/assessment/review access,
physician/pharmacist role boundaries, inactive memberships, token failures,
configuration rejection, malformed identifiers, and optional ML failure handling.
