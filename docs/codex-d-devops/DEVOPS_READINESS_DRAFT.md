# DevOps Readiness Draft

This is a placeholder for Codex D. Do not treat it as a production plan yet.

## Environments

- Local development
- Future staging
- Future production
- Separation of real brokerage data from synthetic/dev data

## Environment Variables and Secrets

- Backend-only app secrets
- SnapTrade client credentials
- SnapTrade secret encryption key
- Local development access token
- Frontend must not receive provider secrets
- `.env` and `.env.*` remain private

## CI

- Backend unit/service/API tests
- Frontend typecheck/lint/build
- Alembic migration checks
- External/slow tests excluded by default
- Secret scanning before push/deploy

## Deployment

- Backend image build
- Frontend build/static hosting
- Database migration procedure
- Environment-specific config
- Rollback path

## Database Migrations

- Upgrade and downgrade checks
- Backup before production migration
- Data retention and deletion policies
- Migration ownership and review gate

## Health Checks

- Backend health endpoint
- Database connectivity
- Broker provider dependency health without leaking secrets
- Frontend availability

## Logging and Monitoring

- Request latency and error rate
- Broker sync success/failure without raw payload logging
- Background job status if introduced
- No account values, holdings, secrets, provider raw data, or portal URLs in logs

## Rollback

- Application rollback
- Migration rollback policy
- Feature flags if needed
- Manual recovery checklist

## Staging vs Production

- Separate databases
- Separate credentials
- Separate SnapTrade apps if needed
- Synthetic fixtures for staging where possible

## Launch Checklist

- Security review complete
- Privacy policy and disclaimer drafted
- Backup/restore tested
- Monitoring in place
- Incident response owner identified
- Data deletion/export path defined

## Engineering Review Framework Sections

Codex D should apply `docs/shared/ENGINEERING_REVIEW_FRAMEWORK.md` sections on reliability, dependency management, scalability/cost, concurrency, metrics/observability, CI/CD, deployment, documentation, and handoff readiness.
