# Implementation Plan

This plan controls incremental implementation for `portfolio-options-agent`.

Rules:

- Implement one task at a time unless the user explicitly approves a broader batch.
- After each task, update this file with status, verification notes, and rollback notes if they changed.
- Stop for review after each task.
- Do not modify `../TradingAgents`.
- Do not read, print, or depend on real `.env` files, API keys, broker credentials, private configs, real account data, or real reports.

Status values:

- `not_started`
- `in_progress`
- `blocked`
- `done`

## Phase 1 - Database Foundation

### P1-T1 - Docker Compose PostgreSQL

- Task id: `P1-T1`
- Title: Docker Compose PostgreSQL
- Objective: Add a local PostgreSQL service for development without adding application database code yet.
- Files expected to change:
  - `docker-compose.yml`
  - `.env.example`
  - `backend/README.md`
  - `docs/implementation_plan.md`
- Dependencies: Existing scaffold only.
- Implementation steps:
  1. Add a root `docker-compose.yml` with a `postgres` service.
  2. Use safe local-development defaults and Docker health checks.
  3. Add `.env.example` with placeholder database variable names only.
  4. Update `backend/README.md` with Postgres start/stop/status commands.
  5. Do not add SQLAlchemy, Alembic, or business tables.
- Acceptance criteria:
  - `docker compose up -d postgres` can start the database service.
  - The Postgres container reports healthy.
  - Existing backend health test still passes.
  - No real secrets or private data are added.
- Tests to run:
  - `docker compose up -d postgres`
  - `docker compose ps postgres`
  - `cd backend && pytest`
- Rollback notes:
  - Remove `docker-compose.yml`.
  - Remove database entries from `.env.example`.
  - Revert Postgres notes from `backend/README.md`.
  - If a local Docker volume was created, the user may remove it with `docker compose down -v`.
- Verification notes:
  - `git status --short --branch` showed `## main...origin/main` before verification.
  - `docker compose up -d postgres` completed successfully and started `portfolio-options-agent-postgres`.
  - `docker compose ps postgres` reported `Up ... (healthy)` with port `5432` published.
  - `docker inspect --format='{{json .State.Health}}' portfolio-options-agent-postgres` reported `"Status":"healthy"` and `pg_isready` output showed Postgres accepting connections.
  - `docker compose --env-file .env.example config` passed, confirming the Compose file renders with safe placeholder values.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 1 test passed in 0.44s.
- Status: `done`

### P1-T2 - Backend Config Loading

- Task id: `P1-T2`
- Title: Backend config loading
- Objective: Add typed backend settings that read safe environment variable names without exposing secret values.
- Files expected to change:
  - `backend/requirements.txt` or future `backend/pyproject.toml`
  - `backend/app/core/config.py`
  - `backend/tests/test_config.py`
  - `.env.example`
  - `docs/implementation_plan.md`
- Dependencies: `P1-T1`
- Implementation steps:
  1. Add a minimal settings module.
  2. Support `DATABASE_URL` and app environment values.
  3. Use placeholders in `.env.example`.
  4. Add tests for defaults and environment overrides using monkeypatch.
- Acceptance criteria:
  - Config loads without requiring real credentials.
  - Tests can override settings safely.
  - No `.env` file is read, printed, or modified by tests.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove config module and tests.
  - Revert dependency changes if any.
- Verification notes:
  - Added dependency-free typed settings in `backend/app/core/config.py`.
  - Added placeholder-only `APP_NAME` and `APP_ENV` entries to `.env.example`.
  - Added monkeypatch tests for safe defaults and environment overrides.
  - No `.env` file was read, printed, or modified.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 3 tests passed in 0.32s.
- Status: `done`

### P1-T3 - SQLAlchemy Session Setup

- Task id: `P1-T3`
- Title: SQLAlchemy session setup
- Objective: Add database engine/session wiring without adding business tables yet.
- Files expected to change:
  - `backend/requirements.txt` or future `backend/pyproject.toml`
  - `backend/app/db/session.py`
  - `backend/app/db/base.py`
  - `backend/tests/test_db_session.py`
  - `docs/implementation_plan.md`
- Dependencies: `P1-T2`
- Implementation steps:
  1. Add SQLAlchemy dependency.
  2. Create engine/session factory.
  3. Add dependency helper for FastAPI routes.
  4. Add a simple connection test that can be skipped if Postgres is unavailable.
- Acceptance criteria:
  - Backend imports cleanly.
  - Session helper is testable.
  - No business models are added.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove session/base modules and dependency changes.
- Verification notes:
  - Added SQLAlchemy, psycopg, and Alembic dependencies to `backend/requirements.txt`.
  - Added empty declarative metadata in `backend/app/db/base.py`; no business models or tables were added.
  - Added engine/session factory and FastAPI DB dependency helper in `backend/app/db/session.py`.
  - Added tests proving metadata starts empty and an explicit SQLite URL can create a working engine.
  - `cd backend && ./.venv/bin/python -m pytest` passed with local Postgres access: 6 tests passed in 0.68s.
- Status: `done`

### P1-T4 - Alembic Setup

- Task id: `P1-T4`
- Title: Alembic setup
- Objective: Add Alembic migration infrastructure with no business tables beyond metadata wiring.
- Files expected to change:
  - `backend/alembic.ini`
  - `backend/alembic/env.py`
  - `backend/alembic/versions/`
  - `backend/app/db/base.py`
  - `docs/implementation_plan.md`
- Dependencies: `P1-T3`
- Implementation steps:
  1. Initialize Alembic structure.
  2. Wire Alembic to backend settings and SQLAlchemy metadata.
  3. Document upgrade/downgrade commands.
  4. Avoid adding business schema in this task.
- Acceptance criteria:
  - `alembic upgrade head` runs against local Postgres.
  - `alembic downgrade -1` is explained or tested when a migration exists.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Remove Alembic files and dependency changes.
- Verification notes:
  - Added Alembic config in `backend/alembic.ini`.
  - Added Alembic environment wiring in `backend/alembic/env.py` using `get_settings().database_url` and `Base.metadata`.
  - Added `backend/alembic/versions/.gitkeep`; no migration revisions or business tables were created.
  - Added backend README migration notes.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed against local Postgres.
  - `alembic downgrade -1` was not run because no migration revisions exist yet; downgrade will be tested once the first schema migration is created.
- Status: `done`

### P1-T5 - DB Connection Test

- Task id: `P1-T5`
- Title: DB connection test
- Objective: Add a focused test or smoke check proving the backend can connect to local Postgres.
- Files expected to change:
  - `backend/tests/test_db_connection.py`
  - `backend/README.md`
  - `docs/implementation_plan.md`
- Dependencies: `P1-T3`, `P1-T4`
- Implementation steps:
  1. Add a safe connection test using configured database URL.
  2. Skip gracefully when Postgres is not running in local dev.
  3. Document exact command to run the check.
- Acceptance criteria:
  - Test passes when Postgres is up.
  - Test skip reason is clear when Postgres is unavailable.
- Tests to run:
  - `docker compose up -d postgres`
  - `cd backend && pytest`
- Rollback notes:
  - Remove DB connection test and README note.
- Verification notes:
  - Added `backend/tests/test_db_connection.py`.
  - The DB connection test uses the configured database URL and skips cleanly when Postgres is unavailable.
  - In the sandboxed test run, local TCP access was blocked and the DB connection test skipped with an explicit reason.
  - With local Postgres access allowed, `cd backend && ./.venv/bin/python -m pytest tests/test_db_connection.py -rs` passed: 1 test passed in 0.40s.
  - With local Postgres access allowed, `cd backend && ./.venv/bin/python -m pytest` passed: 6 tests passed in 0.68s.
- Status: `done`

## Phase 2 - Users and Accounts

### P2-T1 - Users Table

- Task id: `P2-T1`
- Title: users table
- Objective: Add the first user model for local multi-user support.
- Files expected to change:
  - `backend/app/models/user.py`
  - `backend/app/db/base.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: Phase 1 complete.
- Implementation steps:
  1. Define user model with UUID primary key and timestamps.
  2. Include display name and optional email.
  3. Add indexes/unique constraints where safe.
  4. Generate migration.
- Acceptance criteria:
  - Migration creates `users`.
  - Model imports without circular dependencies.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration or remove generated migration/model.
- Verification notes:
  - Added `backend/app/models/user.py` with UUID primary key, display name, optional email, auth provider, active flag, timestamps, and soft delete timestamp.
  - Imported `User` in `backend/app/db/base.py` so Alembic can see the model metadata.
  - Added migration `backend/alembic/versions/0001_create_users.py`.
  - Added `backend/tests/test_user_model.py`.
  - Updated the DB metadata test now that the first business model exists.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 9 tests passed in 0.62s.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0001_create_users`.
  - `cd backend && ./.venv/bin/alembic current` reported `0001_create_users (head)`.
  - Local Postgres metadata query confirmed `public.users` exists.
- Status: `done`

### P2-T2 - Accounts Table

- Task id: `P2-T2`
- Title: accounts table
- Objective: Add account model owned by users.
- Files expected to change:
  - `backend/app/models/account.py`
  - `backend/app/db/base.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: `P2-T1`
- Implementation steps:
  1. Define account model with `user_id` foreign key.
  2. Add broker name, account type, display name, base currency, and soft delete fields.
  3. Add ownership and active-account indexes.
  4. Generate migration.
- Acceptance criteria:
  - Every account belongs to a user.
  - Migration applies cleanly.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration or remove account model/migration.
- Verification notes:
  - Added `backend/app/models/account.py` with UUID primary key, `user_id` foreign key to `users.id`, broker name, account type, display name, base currency, manual-entry flag, timestamps, and soft delete timestamp.
  - Added account ownership and soft-delete indexes in `backend/alembic/versions/0002_create_accounts.py`.
  - Updated model metadata imports so Alembic can discover both `User` and `Account` without circular imports.
  - Added `backend/tests/test_account_model.py`.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0002_create_accounts`.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 20 tests passed in 0.27s.
- Status: `done`

### P2-T3 - First Migration

- Task id: `P2-T3`
- Title: first migration
- Objective: Consolidate or verify the initial users/accounts migration path.
- Files expected to change:
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: `P2-T1`, `P2-T2`
- Implementation steps:
  1. Review autogenerated migration.
  2. Confirm constraints and indexes.
  3. Test upgrade/downgrade locally when practical.
- Acceptance criteria:
  - Clean migration from empty DB to users/accounts schema.
  - Downgrade is safe in development.
- Tests to run:
  - `cd backend && alembic upgrade head`
  - `cd backend && alembic downgrade -1`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Revert migration file and associated models if needed.
- Verification notes:
  - Reviewed `0002_create_accounts` for primary key, user foreign key, account fields, timestamps, and indexes.
  - `cd backend && ./.venv/bin/alembic current` reported `0002_create_accounts (head)`.
  - `cd backend && ./.venv/bin/alembic downgrade 0001_create_users` passed.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed.
  - Final `cd backend && ./.venv/bin/alembic current` reported `0002_create_accounts (head)`.
- Status: `done`

### P2-T4 - User/Account Schemas

- Task id: `P2-T4`
- Title: user/account schemas
- Objective: Add Pydantic schemas for user and account API boundaries.
- Files expected to change:
  - `backend/app/schemas/user.py`
  - `backend/app/schemas/account.py`
  - `backend/tests/test_user_account_schemas.py`
  - `docs/implementation_plan.md`
- Dependencies: `P2-T1`, `P2-T2`
- Implementation steps:
  1. Add create/read/update schemas.
  2. Validate account type and base currency.
  3. Keep public schemas free of private broker credentials.
- Acceptance criteria:
  - Schemas validate expected inputs.
  - Invalid account types fail clearly.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove schema files and tests.
- Verification notes:
  - Added `backend/app/schemas/user.py` with create/read schemas and email validation.
  - Added `backend/app/schemas/account.py` with create/update/read schemas, account type validation, and base-currency normalization.
  - Added `email-validator` to `backend/requirements.txt` for Pydantic `EmailStr`.
  - Added `backend/tests/test_user_account_schemas.py`.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 20 tests passed in 0.27s.
- Status: `done`

### P2-T5 - User/Account Routes

- Task id: `P2-T5`
- Title: user/account routes
- Objective: Add minimal FastAPI routes for local users and accounts.
- Files expected to change:
  - `backend/app/api/routes/users.py`
  - `backend/app/api/routes/accounts.py`
  - `backend/app/main.py`
  - `backend/app/services/users.py`
  - `backend/app/services/accounts.py`
  - `docs/implementation_plan.md`
- Dependencies: `P2-T4`
- Implementation steps:
  1. Add create/list/get user routes.
  2. Add create/list/get/update/delete account routes.
  3. Enforce account ownership in service layer.
  4. Keep auth as local-user-selector assumption only.
- Acceptance criteria:
  - User/account CRUD works through API tests.
  - Account routes do not expose secrets.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove routes/services and route registration.
- Verification notes:
  - Added user service and routes for `POST /users`, `GET /users`, and `GET /users/{user_id}`.
  - Added account service and routes for `POST /users/{user_id}/accounts`, `GET /users/{user_id}/accounts`, `GET /accounts/{account_id}`, `PATCH /accounts/{account_id}`, and `DELETE /accounts/{account_id}`.
  - Registered the route modules in `backend/app/main.py`.
  - Account deletion is implemented as a soft delete for now.
  - Missing users/accounts return `404`; account list excludes soft-deleted accounts.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 20 tests passed in 0.27s.
- Status: `done`

### P2-T6 - Users/Accounts Tests

- Task id: `P2-T6`
- Title: users/accounts tests
- Objective: Add focused tests for user/account persistence and API behavior.
- Files expected to change:
  - `backend/tests/api/test_users.py`
  - `backend/tests/api/test_accounts.py`
  - `backend/tests/conftest.py`
  - `docs/implementation_plan.md`
- Dependencies: `P2-T5`
- Implementation steps:
  1. Add database test fixtures.
  2. Test create/list/get flows.
  3. Test account ownership checks.
  4. Test soft delete behavior if implemented.
- Acceptance criteria:
  - Tests cover the happy path and at least one ownership failure.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove test files and fixtures.
- Verification notes:
  - Added DB-backed pytest fixtures in `backend/tests/conftest.py` that clean users/accounts before and after each API test.
  - Added API tests for user create/list/get and missing-user behavior.
  - Added API tests for account create/list/get/update/delete, missing owner behavior, and missing account behavior.
  - Fixed the synthetic API test email to use a valid placeholder domain accepted by `EmailStr`.
  - Final test run: `cd backend && ./.venv/bin/python -m pytest` passed with 20 tests passed in 0.27s.
- Status: `done`

## Phase 3 - Internal Portfolio Storage Primitives

### P3-T1 - Cash Balances

- Task id: `P3-T1`
- Title: cash balances
- Objective: Model account cash categories including total, reserved collateral, free cash, premium cash, and DCA cash.
- Files expected to change:
  - `backend/app/models/cash_balance.py`
  - `backend/app/schemas/cash_balance.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: Phase 2 complete.
- Implementation steps:
  1. Add cash balance model and migration.
  2. Add create/latest read API.
  3. Store as snapshots with `as_of`.
- Acceptance criteria:
  - Cash snapshot can be created and retrieved per account.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove cash modules.
- Verification notes:
  - Added immutable cash snapshot model `backend/app/models/cash_balance.py`.
  - Added `backend/alembic/versions/0003_create_cash_balances.py`.
  - Added `backend/app/schemas/cash_balance.py`.
  - Added `backend/app/services/portfolio/cash_balances.py`.
  - Added portfolio cash routes in `backend/app/api/routes/portfolio.py` and registered them in `backend/app/main.py`.
  - Added API tests for create/latest cash balance flows and missing-account/missing-snapshot cases.
  - Added unit tests for the cash balance model and schema validation.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed.
  - `cd backend && ./.venv/bin/alembic downgrade 0002_create_accounts` passed.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed.
  - `cd backend && ./.venv/bin/alembic current` reported `0003_create_cash_balances (head)`.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 30 tests passed in 0.36s.
- Status: `done`

### P3-T2 - Stock Positions

- Task id: `P3-T2`
- Title: stock_positions
- Objective: Add normalized account-scoped stock/ETF position storage that can receive data from SnapTrade, manual entry, or CSV fallback.
- Files expected to change:
  - `backend/app/models/stock_position.py`
  - `backend/app/schemas/stock_position.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_stock_position_model.py`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T1`
- Implementation steps:
  1. Add stock/ETF position model with account ownership, symbol, quantity, cost basis fields, source, as-of timestamp, and safe raw metadata placeholder if needed.
  2. Add schema validation using synthetic examples only.
  3. Keep the model source-agnostic so SnapTrade, manual entry, and CSV import can all populate it later.
- Acceptance criteria:
  - Stock/ETF positions are normalized and account-scoped.
  - No broker-specific assumptions are hardcoded into the storage model.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove stock position model/schema/tests.
- Status: `not_started`

### P3-T3 - Option Contracts

- Task id: `P3-T3`
- Title: option_contracts
- Objective: Normalize option contract identity for SnapTrade option holdings, manual entry, CSV fallback, and future market quotes.
- Files expected to change:
  - `backend/app/models/option_contract.py`
  - `backend/app/schemas/option_contract.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_option_contract_model.py`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T2`
- Implementation steps:
  1. Add OCC symbol, underlying, expiration, strike, option type, style, and multiplier.
  2. Add uniqueness on OCC symbol.
  3. Add validation tests for synthetic contract fields.
- Acceptance criteria:
  - Option contracts can be resolved idempotently from provider or manual data.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove contract model/schema/tests.
- Status: `not_started`

### P3-T4 - Option Positions

- Task id: `P3-T4`
- Title: option_positions
- Objective: Add normalized account-scoped option position storage linked to option contracts.
- Files expected to change:
  - `backend/app/models/option_position.py`
  - `backend/app/schemas/option_position.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_option_position_model.py`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T3`
- Implementation steps:
  1. Add option position model linked to account and option contract.
  2. Support long/short quantity, average price, status, source, as-of timestamp, and safe raw metadata placeholder if needed.
  3. Keep data normalized for SnapTrade, manual, and CSV sources.
- Acceptance criteria:
  - Option positions belong to accounts and contracts.
  - Short and long positions can be represented without broker-specific coupling.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove option position model/schema/tests.
- Status: `not_started`

### P3-T5 - Portfolio Summary

- Task id: `P3-T5`
- Title: portfolio summary
- Objective: Compute a deterministic account portfolio summary from internal cash, stock, and option storage.
- Files expected to change:
  - `backend/app/services/portfolio/summary.py`
  - `backend/app/schemas/portfolio.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/tests/services/test_portfolio_summary.py`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T4`
- Implementation steps:
  1. Define input/output schemas for internal normalized portfolio records.
  2. Compute total cash, stock notional, option counts, and basic exposure placeholders.
  3. Avoid broker sync and market data dependencies in this phase.
- Acceptance criteria:
  - Synthetic internal records produce expected summary values.
  - Summary works regardless of whether data came from SnapTrade, manual input, or CSV fallback.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove summary service, route changes, and tests.
- Status: `not_started`

### P3-T6 - Portfolio Storage Tests

- Task id: `P3-T6`
- Title: portfolio storage tests
- Objective: Ensure cash, stock, option contract, option position, and summary flows work together using synthetic data.
- Files expected to change:
  - `backend/tests/api/test_portfolio.py`
  - `backend/tests/services/test_portfolio_summary.py`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T5`
- Implementation steps:
  1. Add end-to-end API tests for internal portfolio storage.
  2. Add service tests for summary calculations.
  3. Validate account ownership boundaries.
- Acceptance criteria:
  - Internal portfolio primitives are ready for SnapTrade normalization.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove portfolio storage tests and fixtures.
- Status: `not_started`

## Phase 4 - Broker Sync Foundation

### P4-T1 - broker_connections

- Task id: `P4-T1`
- Title: broker_connections
- Objective: Add connection metadata for read-only broker sync providers, starting with SnapTrade.
- Files expected to change:
  - `backend/app/models/broker_connection.py`
  - `backend/app/schemas/broker_connection.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_broker_connection_model.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 3 storage primitives complete.
- Implementation steps:
  1. Add user-scoped broker connection model.
  2. Store provider, broker name, provider connection ID, status fields, consent metadata, timestamps, and `secret_ref`.
  3. Do not store plaintext provider secrets.
- Acceptance criteria:
  - Broker connection metadata supports SnapTrade without exposing credentials.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove broker connection model/schema/tests.
- Status: `not_started`

### P4-T2 - broker_accounts

- Task id: `P4-T2`
- Title: broker_accounts
- Objective: Map provider accounts to internal accounts without coupling internal IDs to SnapTrade IDs.
- Files expected to change:
  - `backend/app/models/broker_account.py`
  - `backend/app/schemas/broker_account.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_broker_account_model.py`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T1`
- Implementation steps:
  1. Add provider account ID, broker connection ID, optional internal account ID, display name, account type, and freshness fields.
  2. Enforce uniqueness by broker connection and provider account ID.
  3. Preserve safe provider metadata in JSONB only where useful.
- Acceptance criteria:
  - A SnapTrade brokerage account can be mapped to an internal account record.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove broker account model/schema/tests.
- Status: `not_started`

### P4-T3 - broker_sync_runs

- Task id: `P4-T3`
- Title: broker_sync_runs
- Objective: Track individual broker sync attempts for observability, retries, and stale-data warnings.
- Files expected to change:
  - `backend/app/models/broker_sync_run.py`
  - `backend/app/schemas/broker_sync_run.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_broker_sync_run_model.py`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T2`
- Implementation steps:
  1. Add sync run model with trigger, status, started/completed timestamps, counts, provider request ID, summary, and error JSONB.
  2. Link runs to broker connection and optionally broker account.
  3. Avoid storing sensitive raw credentials or account secrets.
- Acceptance criteria:
  - Sync runs can represent succeeded, failed, partial, and cancelled syncs.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove sync run model/schema/tests.
- Status: `not_started`

### P4-T4 - Provider Credentials Metadata

- Task id: `P4-T4`
- Title: provider_credentials_metadata or secret reference model
- Objective: Store provider credential metadata and secret references without storing plaintext secrets.
- Files expected to change:
  - `backend/app/models/provider_credentials_metadata.py`
  - `backend/app/schemas/provider_credentials_metadata.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_provider_credentials_metadata_model.py`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T1`
- Implementation steps:
  1. Add provider, credential name, scopes, status, and `secret_ref` or `encrypted_secret_ref`.
  2. Ensure model and docs forbid plaintext SnapTrade `userSecret` storage.
  3. Keep frontend responses from exposing secret references unless explicitly safe.
- Acceptance criteria:
  - Provider credential metadata can reference secrets safely.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove credential metadata model/schema/tests.
- Status: `not_started`

### P4-T5 - Broker Sync Status Enums

- Task id: `P4-T5`
- Title: connection_status, sync_status, data_freshness_status enums
- Objective: Standardize broker connection and freshness status values used by SnapTrade and future providers.
- Files expected to change:
  - `backend/app/services/broker_import/statuses.py`
  - `backend/app/schemas/broker_sync_status.py`
  - `backend/tests/unit/test_broker_sync_statuses.py`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T3`
- Implementation steps:
  1. Define connection status values such as connected, disconnected, reauth_required, error, unknown.
  2. Define sync status values such as idle, queued, running, succeeded, failed, partially_succeeded, cancelled.
  3. Define data freshness values such as fresh, cached, stale, unknown, error, reauth_required.
- Acceptance criteria:
  - Status values are centralized and test-covered.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove status modules and tests.
- Status: `not_started`

### P4-T6 - Broker Sync Interfaces

- Task id: `P4-T6`
- Title: broker sync interfaces
- Objective: Define app-owned broker sync service boundaries before adding SnapTrade-specific code.
- Files expected to change:
  - `backend/app/services/broker_import/interfaces.py`
  - `backend/app/services/broker_import/models.py`
  - `backend/tests/services/test_broker_sync_interfaces.py`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T5`
- Implementation steps:
  1. Define internal broker sync request/result models.
  2. Keep provider-specific HTTP details out of internal services.
  3. Make room for SnapTrade, Akoya, Plaid, manual, and CSV sources.
- Acceptance criteria:
  - Internal sync service interfaces are importable and testable without network or credentials.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove interface/model/test files.
- Status: `not_started`

### P4-T7 - Broker Sync Foundation Tests

- Task id: `P4-T7`
- Title: broker sync foundation tests
- Objective: Cover broker connection/account/sync metadata, statuses, and safe secret-reference behavior.
- Files expected to change:
  - `backend/tests/api/test_broker_sync_foundation.py`
  - `backend/tests/services/test_broker_sync_interfaces.py`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T6`
- Implementation steps:
  1. Add synthetic model/schema tests.
  2. Add status and interface tests.
  3. Add assertions that fixtures use fake secret references only.
- Acceptance criteria:
  - Broker sync foundation is ready for a SnapTrade adapter without storing real credentials.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove broker sync foundation tests.
- Status: `not_started`

## Phase 5 - SnapTrade Read-Only Adapter, Mock-First

### P5-T1 - BrokerPortfolioProvider Interface

- Task id: `P5-T1`
- Title: BrokerPortfolioProvider interface
- Objective: Define the read-only provider interface for account, balance, position, option position, transaction, and refresh operations.
- Files expected to change:
  - `backend/app/services/broker_import/providers/base.py`
  - `backend/app/services/broker_import/providers/models.py`
  - `backend/tests/adapters/test_broker_portfolio_provider_interface.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 4 complete.
- Implementation steps:
  1. Define methods for accounts, balances, positions, option positions, transactions, and refresh.
  2. Include sync timestamp, sync status, and data freshness status in provider models.
  3. Keep market data quotes out of this interface.
- Acceptance criteria:
  - Provider interface can be tested without SnapTrade credentials or network calls.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove provider interface files and tests.
- Status: `not_started`

### P5-T2 - SnapTradeAdapter Skeleton

- Task id: `P5-T2`
- Title: SnapTradeAdapter skeleton
- Objective: Add a read-only SnapTrade adapter shell that does not call trading/order endpoints.
- Files expected to change:
  - `backend/app/services/broker_import/providers/snaptrade.py`
  - `backend/tests/adapters/test_snaptrade_adapter_skeleton.py`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T1`
- Implementation steps:
  1. Add adapter class implementing `BrokerPortfolioProvider`.
  2. Stub read-only methods only.
  3. Add explicit guardrails against trading/order operations.
- Acceptance criteria:
  - Adapter skeleton imports and exposes read-only methods only.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove SnapTrade adapter skeleton and tests.
- Status: `not_started`

### P5-T3 - SnapTrade Config Names

- Task id: `P5-T3`
- Title: config from environment variable names only
- Objective: Add configuration names for SnapTrade without adding real credentials or reading private `.env` content.
- Files expected to change:
  - `backend/app/core/config.py`
  - `.env.example`
  - `backend/tests/unit/test_config.py`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T2`
- Implementation steps:
  1. Add placeholder variable names only, such as `SNAPTRADE_CLIENT_ID` and `SNAPTRADE_CONSUMER_KEY`.
  2. Keep placeholder values synthetic.
  3. Do not read, print, or modify `.env`.
- Acceptance criteria:
  - Config documents expected environment variable names without real secrets.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove SnapTrade config fields and placeholder docs.
- Status: `not_started`

### P5-T4 - SnapTrade Exceptions and Response Models

- Task id: `P5-T4`
- Title: exception classes and response models
- Objective: Add app-owned exceptions and typed response models for SnapTrade adapter behavior.
- Files expected to change:
  - `backend/app/services/broker_import/providers/exceptions.py`
  - `backend/app/services/broker_import/providers/snaptrade_models.py`
  - `backend/tests/adapters/test_snaptrade_models.py`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T3`
- Implementation steps:
  1. Define provider unavailable, auth, reauth required, stale data, and rate-limit exceptions.
  2. Define typed models for accounts, balances, positions, option positions, and connection portal URL responses.
  3. Keep raw provider payload handling safe and optional.
- Acceptance criteria:
  - SnapTrade errors map to app-owned exceptions.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove exceptions/models/tests.
- Status: `not_started`

### P5-T5 - Mocked SnapTrade User and Account Tests

- Task id: `P5-T5`
- Title: mocked tests for register user, connection portal URL, and list accounts
- Objective: Test SnapTrade registration, connection portal URL, and account listing with mocked HTTP responses.
- Files expected to change:
  - `backend/tests/adapters/test_snaptrade_user_and_accounts.py`
  - `backend/app/services/broker_import/providers/snaptrade.py`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T4`
- Implementation steps:
  1. Mock register/create user response.
  2. Mock connection portal URL response.
  3. Mock list accounts response with connection/account IDs and freshness status.
- Acceptance criteria:
  - Tests pass without network, real SnapTrade credentials, or real broker data.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove mocked adapter tests and related adapter methods.
- Status: `not_started`

### P5-T6 - Mocked SnapTrade Portfolio Data Tests

- Task id: `P5-T6`
- Title: mocked tests for balances, positions, and option positions
- Objective: Test read-only SnapTrade account data methods with synthetic mocked payloads.
- Files expected to change:
  - `backend/tests/adapters/test_snaptrade_portfolio_data.py`
  - `backend/app/services/broker_import/providers/snaptrade.py`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T5`
- Implementation steps:
  1. Mock balances response.
  2. Mock stock/ETF positions response.
  3. Mock option positions response.
  4. Verify market quote data is not treated as broker sync data.
- Acceptance criteria:
  - SnapTrade adapter reads portfolio data only and never calls trading/order endpoints.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove mocked portfolio data tests and related adapter methods.
- Status: `not_started`

### P5-T7 - External Test Guardrails

- Task id: `P5-T7`
- Title: external tests skipped by default
- Objective: Prepare optional external SnapTrade tests that are disabled unless explicitly selected later.
- Files expected to change:
  - `backend/tests/adapters/test_snaptrade_external.py`
  - `backend/tests/README.md`
  - `backend/pytest.ini`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T6`
- Implementation steps:
  1. Add skipped external test placeholder or documented marker guidance.
  2. Require `external` marker for real provider tests.
  3. Ensure default `pytest` still avoids network and credentials.
- Acceptance criteria:
  - External tests cannot run accidentally in the default suite.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && pytest -m external` only when explicitly configured later.
- Rollback notes:
  - Remove external test placeholder/docs.
- Status: `not_started`

## Phase 6 - SnapTrade Connection Flow Backend

### P6-T1 - Register SnapTrade User Endpoint

- Task id: `P6-T1`
- Title: backend endpoint to register/create SnapTrade user
- Objective: Add backend-only flow for creating or resolving a SnapTrade user without exposing secrets to frontend.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/snaptrade_connection.py`
  - `backend/tests/api/test_snaptrade_connection_flow.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 5 complete.
- Implementation steps:
  1. Add endpoint that uses backend config and secret references only.
  2. Store provider connection/user metadata safely.
  3. Mock SnapTrade calls in API tests.
- Acceptance criteria:
  - Endpoint works with mocked SnapTrade and never returns provider secrets.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove route/service/tests.
- Status: `not_started`

### P6-T2 - Connection Portal URL Endpoint

- Task id: `P6-T2`
- Title: backend endpoint to generate connection portal URL
- Objective: Generate a SnapTrade connection portal URL through the backend only.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/snaptrade_connection.py`
  - `backend/tests/api/test_snaptrade_connection_flow.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T1`
- Implementation steps:
  1. Add endpoint for connection portal URL generation.
  2. Return only the URL and non-sensitive metadata.
  3. Mock provider call and verify no secrets in response.
- Acceptance criteria:
  - Frontend can receive portal URL without SnapTrade secrets.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove portal endpoint/service/test changes.
- Status: `not_started`

### P6-T3 - List Broker Connections Endpoint

- Task id: `P6-T3`
- Title: endpoint to list broker connections
- Objective: List broker connections and statuses for a user.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/connections.py`
  - `backend/tests/api/test_broker_connections.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T2`
- Implementation steps:
  1. Add user-scoped list endpoint.
  2. Include connection status, sync status, freshness, and last sync timestamps.
  3. Exclude secret references unless explicitly safe for backend-only diagnostics.
- Acceptance criteria:
  - Connections can be listed without exposing credentials.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove list endpoint/service/tests.
- Status: `not_started`

### P6-T4 - List Broker Accounts Endpoint

- Task id: `P6-T4`
- Title: endpoint to list broker accounts
- Objective: List provider accounts mapped to internal accounts.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/accounts.py`
  - `backend/tests/api/test_broker_accounts.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T3`
- Implementation steps:
  1. Add connection-scoped or user-scoped account list endpoint.
  2. Include provider account ID, mapped account ID, sync status, and data freshness.
  3. Keep account data synthetic in tests.
- Acceptance criteria:
  - Broker accounts can be listed and mapped safely.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove broker account endpoint/service/tests.
- Status: `not_started`

### P6-T5 - Sync Account Data Endpoint

- Task id: `P6-T5`
- Title: endpoint to sync account data
- Objective: Trigger a read-only SnapTrade account sync through backend services.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/sync.py`
  - `backend/tests/api/test_broker_sync.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T4`
- Implementation steps:
  1. Add endpoint to queue or run a read-only sync.
  2. Create broker sync run metadata.
  3. Mock provider calls for accounts, balances, positions, and option positions.
- Acceptance criteria:
  - Sync endpoint creates traceable sync run records without trading/order calls.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove sync endpoint/service/tests.
- Status: `not_started`

### P6-T6 - Broker Sync Run Status Endpoint

- Task id: `P6-T6`
- Title: endpoint to inspect broker sync run status
- Objective: Let UI inspect broker sync progress, errors, and freshness status.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/sync_runs.py`
  - `backend/tests/api/test_broker_sync_runs.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T5`
- Implementation steps:
  1. Add sync run detail endpoint.
  2. Return status, counts, timestamps, and sanitized error details.
  3. Avoid raw secrets or sensitive payloads.
- Acceptance criteria:
  - Sync run status is visible and safe for frontend consumption.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove sync run status endpoint/service/tests.
- Status: `not_started`

### P6-T7 - SnapTrade Connection Flow API Tests

- Task id: `P6-T7`
- Title: mocked API tests only
- Objective: Cover SnapTrade connection and sync endpoints using mocked provider responses only.
- Files expected to change:
  - `backend/tests/api/test_snaptrade_connection_flow.py`
  - `backend/tests/api/test_broker_sync.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T6`
- Implementation steps:
  1. Add happy-path mocked API tests.
  2. Add reauth/error/stale provider scenarios.
  3. Assert no secrets appear in API responses.
- Acceptance criteria:
  - Connection flow backend is covered without real SnapTrade calls.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove connection flow API tests.
- Status: `not_started`

## Phase 7 - SnapTrade Portfolio Normalization

### P7-T1 - Balances to Cash Balances

- Task id: `P7-T1`
- Title: map balances to cash_balances
- Objective: Normalize SnapTrade balances into internal cash snapshot records.
- Files expected to change:
  - `backend/app/services/broker_import/normalization/cash.py`
  - `backend/tests/services/test_snaptrade_cash_normalization.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 6 complete.
- Implementation steps:
  1. Map provider balances to total cash and related cash categories where available.
  2. Preserve sync timestamp and source.
  3. Use conservative defaults when provider fields are missing.
- Acceptance criteria:
  - Synthetic SnapTrade balances produce expected cash snapshots.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove cash normalization module/tests.
- Status: `not_started`

### P7-T2 - Stock/ETF Position Normalization

- Task id: `P7-T2`
- Title: map stock/ETF positions to stock_positions
- Objective: Normalize SnapTrade stock/ETF holdings into internal stock position records.
- Files expected to change:
  - `backend/app/services/broker_import/normalization/stocks.py`
  - `backend/tests/services/test_snaptrade_stock_normalization.py`
  - `docs/implementation_plan.md`
- Dependencies: `P7-T1`
- Implementation steps:
  1. Map symbols, quantities, costs, market values if present, and as-of timestamps.
  2. Preserve provider IDs where useful.
  3. Avoid treating provider market values as live quote data.
- Acceptance criteria:
  - Synthetic SnapTrade holdings produce expected stock position records.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove stock normalization module/tests.
- Status: `not_started`

### P7-T3 - Option Position Normalization

- Task id: `P7-T3`
- Title: map option positions to option_contracts and option_positions
- Objective: Normalize SnapTrade option holdings into contracts and account positions.
- Files expected to change:
  - `backend/app/services/broker_import/normalization/options.py`
  - `backend/tests/services/test_snaptrade_option_normalization.py`
  - `docs/implementation_plan.md`
- Dependencies: `P7-T2`
- Implementation steps:
  1. Parse provider option identifiers into normalized contracts where possible.
  2. Create or resolve option contracts idempotently.
  3. Map long/short quantities and status into option positions.
- Acceptance criteria:
  - Synthetic SnapTrade option holdings produce expected contract and position records.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove option normalization module/tests.
- Status: `not_started`

### P7-T4 - Safe Raw Provider Payloads

- Task id: `P7-T4`
- Title: preserve safe raw provider payload in JSONB where useful
- Objective: Retain useful provider metadata for audit/debugging without storing secrets or unsafe payloads.
- Files expected to change:
  - `backend/app/services/broker_import/normalization/sanitization.py`
  - `backend/tests/services/test_provider_payload_sanitization.py`
  - `docs/implementation_plan.md`
- Dependencies: `P7-T3`
- Implementation steps:
  1. Define allowlist or redaction behavior for raw provider payload fields.
  2. Strip credentials, tokens, secrets, and sensitive auth fields.
  3. Test redaction with synthetic payloads.
- Acceptance criteria:
  - Raw payload persistence cannot leak provider secrets.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove sanitization module/tests.
- Status: `not_started`

### P7-T5 - Reconciliation and Duplicate Handling

- Task id: `P7-T5`
- Title: reconciliation and duplicate handling
- Objective: Prevent duplicated positions and handle provider updates deterministically.
- Files expected to change:
  - `backend/app/services/broker_import/reconciliation.py`
  - `backend/tests/services/test_broker_reconciliation.py`
  - `docs/implementation_plan.md`
- Dependencies: `P7-T4`
- Implementation steps:
  1. Define idempotency keys for provider account, symbol/contract, source, and as-of timestamps.
  2. Handle updates, missing positions, and duplicate payload rows.
  3. Preserve enough sync-run metadata for review.
- Acceptance criteria:
  - Re-running the same synthetic sync does not duplicate holdings.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove reconciliation module/tests.
- Status: `not_started`

### P7-T6 - SnapTrade Normalization Tests

- Task id: `P7-T6`
- Title: tests with synthetic mocked SnapTrade payloads
- Objective: Cover end-to-end normalization from mocked SnapTrade portfolio payloads into internal tables.
- Files expected to change:
  - `backend/tests/services/test_snaptrade_normalization_end_to_end.py`
  - `docs/implementation_plan.md`
- Dependencies: `P7-T5`
- Implementation steps:
  1. Add synthetic account, balance, stock, ETF, and option fixtures.
  2. Verify internal cash, stock, contract, and option records.
  3. Verify sync and freshness metadata are preserved.
- Acceptance criteria:
  - SnapTrade normalization is ready for dashboard backend use.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove end-to-end normalization tests.
- Status: `not_started`

## Phase 8 - Portfolio Dashboard Backend from Synced Data

### P8-T1 - Portfolio Summary from Internal Tables

- Task id: `P8-T1`
- Title: portfolio summary from internal tables
- Objective: Serve portfolio summary using normalized synced/manual/CSV records.
- Files expected to change:
  - `backend/app/services/portfolio/summary.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/tests/api/test_portfolio_summary.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 7 complete.
- Implementation steps:
  1. Read cash, stock, and option position records.
  2. Produce deterministic account summary fields.
  3. Include source and as-of metadata.
- Acceptance criteria:
  - Portfolio summary works from SnapTrade-normalized synthetic data.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove summary endpoint/service changes/tests.
- Status: `not_started`

### P8-T2 - Broker Sync Freshness Endpoint

- Task id: `P8-T2`
- Title: broker sync freshness endpoint
- Objective: Expose broker sync freshness separately from market quote freshness.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/freshness.py`
  - `backend/tests/api/test_broker_sync_freshness.py`
  - `docs/implementation_plan.md`
- Dependencies: `P8-T1`
- Implementation steps:
  1. Add endpoint for account broker sync freshness.
  2. Include last successful sync, current status, data freshness status, and reauth/error flags.
  3. Do not include market quote freshness here.
- Acceptance criteria:
  - UI can display broker sync freshness independently.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove freshness endpoint/service/tests.
- Status: `not_started`

### P8-T3 - Stale/Cached/Unknown Data Warnings

- Task id: `P8-T3`
- Title: stale/cached/unknown data warnings
- Objective: Generate backend warning flags when broker data freshness is not fresh.
- Files expected to change:
  - `backend/app/services/portfolio/warnings.py`
  - `backend/app/schemas/portfolio.py`
  - `backend/tests/services/test_portfolio_warnings.py`
  - `docs/implementation_plan.md`
- Dependencies: `P8-T2`
- Implementation steps:
  1. Add warning generation for cached, stale, unknown, error, and reauth-required broker data.
  2. Make warnings explicit that market prices may be current while holdings/cash are stale.
  3. Keep quote freshness warnings separate for Phase 10.
- Acceptance criteria:
  - Stale broker data is never presented as immediately actionable.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove warning service/schema/tests.
- Status: `not_started`

### P8-T4 - Dashboard Backend Tests

- Task id: `P8-T4`
- Title: tests
- Objective: Cover portfolio summary and broker freshness behavior from synced data.
- Files expected to change:
  - `backend/tests/api/test_portfolio_dashboard_backend.py`
  - `backend/tests/services/test_portfolio_warnings.py`
  - `docs/implementation_plan.md`
- Dependencies: `P8-T3`
- Implementation steps:
  1. Add synthetic synced-data fixtures.
  2. Test summary output and freshness warnings.
  3. Ensure no market data provider calls occur.
- Acceptance criteria:
  - Dashboard backend can support a synced portfolio view without market data coupling.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove dashboard backend tests.
- Status: `not_started`

## Phase 9 - Manual Input and CSV Fallback

### P9-T1 - Manual Entry Fallback

- Task id: `P9-T1`
- Title: keep manual entry available
- Objective: Preserve manual user/account/cash/position entry as a fallback when SnapTrade is unavailable or intentionally disabled.
- Files expected to change:
  - `backend/app/api/routes/portfolio.py`
  - `backend/tests/api/test_manual_portfolio_entry.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 8 complete.
- Implementation steps:
  1. Ensure manual entry uses the same internal storage primitives as SnapTrade normalization.
  2. Mark manual records with source metadata.
  3. Keep tests synthetic.
- Acceptance criteria:
  - Manual entry remains functional without broker API credentials.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove manual fallback route/test changes.
- Status: `not_started`

### P9-T2 - Fidelity CSV Import Backup

- Task id: `P9-T2`
- Title: simple CSV import backup
- Objective: Add CSV import backup for positions/transactions when API sync is unavailable.
- Files expected to change:
  - `backend/app/services/broker_import/fidelity_csv.py`
  - `backend/app/api/routes/imports.py`
  - `backend/tests/services/test_fidelity_csv_import.py`
  - `docs/implementation_plan.md`
- Dependencies: `P9-T1`
- Implementation steps:
  1. Parse synthetic CSV fixtures only.
  2. Validate and preview imported rows before persistence.
  3. Avoid storing broker files in git or tests with real data.
- Acceptance criteria:
  - CSV import can act as a backup without scraping or credentials.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove CSV parser/routes/tests.
- Status: `not_started`

### P9-T3 - Synthetic CSV Fixtures

- Task id: `P9-T3`
- Title: synthetic fixtures only
- Objective: Add safe synthetic CSV fixtures and documentation for fallback import tests.
- Files expected to change:
  - `backend/tests/fixtures/fidelity_positions_demo.csv`
  - `backend/tests/fixtures/fidelity_transactions_demo.csv`
  - `backend/tests/README.md`
  - `docs/implementation_plan.md`
- Dependencies: `P9-T2`
- Implementation steps:
  1. Add small fake CSV samples.
  2. Use demo symbols and fake account labels only.
  3. Document that real broker CSVs are gitignored and must not be committed.
- Acceptance criteria:
  - CSV tests use synthetic data only.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove synthetic fixtures and docs.
- Status: `not_started`

### P9-T4 - Fallback Tests

- Task id: `P9-T4`
- Title: do not block SnapTrade progress
- Objective: Verify manual and CSV fallback paths do not block the SnapTrade-first architecture.
- Files expected to change:
  - `backend/tests/api/test_portfolio_fallbacks.py`
  - `backend/tests/services/test_import_fallbacks.py`
  - `docs/implementation_plan.md`
- Dependencies: `P9-T3`
- Implementation steps:
  1. Test manual fallback without provider credentials.
  2. Test CSV fallback with synthetic files.
  3. Verify SnapTrade-specific paths are not required for fallback tests.
- Acceptance criteria:
  - Manual and CSV backups remain available without becoming the main integration path.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove fallback tests.
- Status: `not_started`

## Phase 10 - Market Data Layer

### P10-T1 - MarketDataProvider

- Task id: `P10-T1`
- Title: MarketDataProvider
- Objective: Define provider-agnostic stock quote and intraday bar interfaces separate from broker sync.
- Files expected to change:
  - `backend/app/services/market_data/interfaces.py`
  - `backend/app/services/market_data/models.py`
  - `backend/tests/services/market_data/test_interfaces.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 8 complete.
- Implementation steps:
  1. Define market quote provider protocol.
  2. Include quote timestamp, provider, and quote freshness.
  3. Do not include broker holdings/cash fields.
- Acceptance criteria:
  - Market data interfaces are separate from `BrokerPortfolioProvider`.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove market data interface files/tests.
- Status: `not_started`

### P10-T2 - OptionDataProvider

- Task id: `P10-T2`
- Title: OptionDataProvider
- Objective: Define option quote, option chain, IV, and Greeks provider interfaces.
- Files expected to change:
  - `backend/app/services/market_data/interfaces.py`
  - `backend/app/services/market_data/models.py`
  - `backend/tests/services/market_data/test_option_interfaces.py`
  - `docs/implementation_plan.md`
- Dependencies: `P10-T1`
- Implementation steps:
  1. Add option expirations, chain, snapshot, and quote methods.
  2. Include IV and Greeks fields.
  3. Include quote freshness and provider timestamp.
- Acceptance criteria:
  - Option market data is represented without broker account coupling.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Revert option interface additions.
- Status: `not_started`

### P10-T3 - Quote Freshness

- Task id: `P10-T3`
- Title: quote freshness
- Objective: Centralize live/delayed/stale/EOD quote freshness classification.
- Files expected to change:
  - `backend/app/services/market_data/freshness.py`
  - `backend/tests/services/market_data/test_freshness.py`
  - `docs/implementation_plan.md`
- Dependencies: `P10-T2`
- Implementation steps:
  1. Define quote freshness statuses.
  2. Implement timestamp and provider-mode based classification.
  3. Keep broker sync freshness separate.
- Acceptance criteria:
  - Stale quote data is never labeled immediately actionable.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove quote freshness module/tests.
- Status: `not_started`

### P10-T4 - Manual Market Data Provider

- Task id: `P10-T4`
- Title: manual provider
- Objective: Add a deterministic market data provider for manually entered quote snapshots and tests.
- Files expected to change:
  - `backend/app/services/market_data/manual_provider.py`
  - `backend/tests/services/market_data/test_manual_provider.py`
  - `docs/implementation_plan.md`
- Dependencies: `P10-T3`
- Implementation steps:
  1. Implement provider using explicit synthetic quote inputs.
  2. Mark freshness based on supplied quote timestamps.
  3. Avoid network and API keys.
- Acceptance criteria:
  - Market data tests can run without external providers.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove manual provider and tests.
- Status: `not_started`

### P10-T5 - Low-Cost Fallback Provider

- Task id: `P10-T5`
- Title: low-cost fallback provider
- Objective: Add one low-cost fallback provider behind the market data interface without treating it as production-grade live OPRA data.
- Files expected to change:
  - `backend/app/services/market_data/yfinance_provider.py`
  - `backend/requirements.txt` or future `backend/pyproject.toml`
  - `backend/tests/services/market_data/test_yfinance_provider.py`
  - `docs/implementation_plan.md`
- Dependencies: `P10-T4`
- Implementation steps:
  1. Add provider adapter with clear data-mode labels.
  2. Keep network tests mocked by default.
  3. Document limitations and freshness behavior.
- Acceptance criteria:
  - Provider can be mocked in tests.
  - API consumers can see delayed/stale/EOD status.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove provider, dependency, and tests.
- Status: `not_started`

### P10-T6 - Market Data Tests

- Task id: `P10-T6`
- Title: tests
- Objective: Cover market data provider interfaces, manual provider, fallback provider mocks, and quote freshness.
- Files expected to change:
  - `backend/tests/services/market_data/*`
  - `docs/implementation_plan.md`
- Dependencies: `P10-T5`
- Implementation steps:
  1. Add provider contract tests.
  2. Add fallback behavior tests.
  3. Add stale quote warning tests.
- Acceptance criteria:
  - Market data layer is safe to use without real credentials and remains separate from broker sync.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove market data tests and fixtures.
- Status: `not_started`
