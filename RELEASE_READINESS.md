# Cyber DNA — Release Readiness Register

Last reviewed: 2026-10-30

This register describes capabilities visible in the repository and the work still required before accepting paying customers. A merged change or a successful Vercel build is not, by itself, proof of production readiness.

## Implemented in the current codebase

- Server-side login, PBKDF2-HMAC-SHA256 password hashing, opaque database-backed sessions, logout revocation, and forced temporary-password change.
- One-time first platform administrator bootstrap protected by an out-of-band `CYBERDNA_BOOTSTRAP_SECRET`.
- Platform-admin-provisioned organizations and users; organization roles include organization admin, security analyst, and read-only viewer.
- Tenant context derived from authenticated sessions or organization-scoped collector keys; ORM tenant query scoping is used for telemetry and detection models.
- Collector keys are stored as SHA-256 hashes, returned only once at creation, and can be revoked.
- Onboarding state and assessment data are persisted. Activation checks for recent tenant events and enabled detection rules.
- Pricing-rule configuration and estimate calculation exist; estimates are explicitly not quotes.
- Rule-based event detection, persisted findings, incident correlation, and an Isolation Forest v25 artifact are present.
- AI Analyst supports a configured external provider and deterministic fallback. Provider connectivity requires a real credential and explicit live test.
- New protected Platform Admin APIs and a role-gated dashboard are included on the `release/saas-foundation-audit-fixes` branch (PR #5): overview, organization usage, user access control, audit logs, and pricing-rule visibility.

## Not yet release-complete

- Public company self-registration with verified email is not implemented. Organization creation is currently provisioned by a platform administrator.
- Email verification, customer password-reset email delivery, and MFA need an identity/email provider and operational configuration.
- Platform Admin dashboard currently provides visibility and account enable/disable. Full organization lifecycle actions, plan approval UI, collector inventory UI, and support workflows remain.
- Payment processing, invoices, tax handling, payment webhooks, and subscription enforcement are not implemented. Pricing estimates are not billing.
- The collector heartbeat endpoint acknowledges but does not persist a heartbeat. Collector presence is inferred from recent event ingestion; a durable per-collector inventory/heartbeat model is still needed.
- The ML event-ID compatibility mapping still needs validation against the original training aggregation pipeline and representative labelled AD telemetry. Artifact availability is not evidence of accuracy.
- The AI provider has not been confirmed against the customer's production API credential. Never display it as connected until a live check succeeds.
- Real Windows AD collector installation, secure transport, service-account permissions, reconnect behavior, and end-to-end field mapping require customer-lab testing.
- Tenant-isolation tests need to cover every API route, relationship traversal, AI context retrieval, exports, collector paths, and admin operations. Existing tests are a useful start, not a complete security certification.
- Login throttling, MFA, password recovery, session anomaly monitoring, backup/restore drills, retention/deletion policies, and production incident response need completion.
- The first frontend CI run exposed stale test assumptions about the old `/assistant/chat` route and a JavaScript syntax issue introduced during the change. The route expectations and syntax were corrected; the latest frontend test run has not yet been confirmed green.

## Current change set

PR: https://github.com/million410/Cyber-DNA-/pull/5

- Adds read-only platform metrics and tenant inventory endpoints.
- Adds platform user access disable/enable. Disabling an account revokes its active sessions.
- Adds an admin-only frontend area. It is rendered only for a server-authenticated `platform_admin`.
- Does not change existing API paths or request/response contracts.
- Backend tests and Python compilation passed in GitHub Actions. The first frontend CI run failed; the parser syntax issue was fixed and a subsequent Vercel preview build reached READY. The newest commits are still awaiting a fresh complete frontend CI result. READY is a build result, not a release approval.

## Release gates

Before enabling customer self-registration or accepting production customer data:

1. Complete an independent tenant-isolation review and cross-tenant negative tests for every endpoint.
2. Add login throttling, MFA, verified email, password recovery, secure cookie enforcement, CSRF review, and session lifecycle controls.
3. Implement durable collector inventory and heartbeat, scoped collector disable/rotation, and HTTPS-only production transport.
4. Validate the v25 feature transformation using the original training pipeline and labelled, representative AD data; publish precision, recall, F1, false-positive rate, and test-set details.
5. Verify AI provider connectivity with the production secret and ensure sensitive tenant data is not sent beyond approved retention and privacy rules.
6. Implement subscription entitlements and payment provider webhooks before presenting paid plans as purchasable.
7. Run backend tests, frontend tests, production builds, browser/API end-to-end tests, migration/backup/restore tests, and security scans.
8. Configure production database backups, monitoring, alerting, log retention, incident response, and customer offboarding/data deletion.

## Environment variables requiring operator configuration

- `DATABASE_URI` or `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `CYBERDNA_BOOTSTRAP_SECRET` for one-time initial platform administrator creation
- `CYBERDNA_COOKIE_SECURE=true` for HTTPS production cookies
- `CORS_ORIGINS` set to the exact trusted production origins
- `OPENAI_API_KEY` and approved `AI_PROVIDER` / `AI_MODEL` if AI explanations are enabled
- ML artifact/config paths and `ML_ENABLED` set and verified for the deployed runtime

Do not commit secrets, database files, collector keys, or customer telemetry to Git.
