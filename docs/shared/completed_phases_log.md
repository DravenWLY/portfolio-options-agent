# Completed Phases Log

Archived implementation history for completed work. Keep this file for auditability, but do not load it into Claude/Opus reviews unless the review specifically concerns historical implementation details.

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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
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

### P3-T1B - Cash Snapshot Provenance Alignment

- Task id: `P3-T1B`
- Title: cash snapshot provenance alignment
- Objective: Align completed cash balance snapshots with the SnapTrade-first architecture by adding source and freshness metadata.
- Files expected to change:
  - `backend/app/models/cash_balance.py`
  - `backend/app/schemas/cash_balance.py`
  - `backend/app/services/portfolio/cash_balances.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_cash_balance_model.py`
  - `backend/tests/unit/test_cash_balance_schema.py`
  - `backend/tests/api/test_portfolio_cash.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P3-T1`
- Implementation steps:
  1. Add source, source reference, and data freshness fields to cash snapshots.
  2. Keep defaults compatible with manual entry.
  3. Avoid adding broker sync foreign keys until `broker_sync_runs` exists.
- Acceptance criteria:
  - Cash snapshots can represent manual, CSV, or future SnapTrade-normalized balance sources.
  - No SnapTrade credentials or broker secrets are stored.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove provenance fields/tests.
- Verification notes:
  - Added `source`, `source_ref`, and `data_freshness_status` to `backend/app/models/cash_balance.py`.
  - Added migration `backend/alembic/versions/0004_add_cash_balance_provenance.py`.
  - Updated `backend/app/schemas/cash_balance.py` to support `manual`, `csv`, and `snaptrade` sources with safe freshness statuses.
  - Updated cash balance service and API tests to preserve provenance/freshness metadata.
  - Did not add a `broker_sync_run_id` foreign key yet because `broker_sync_runs` belongs to Phase 4.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0004_add_cash_balance_provenance`.
  - `cd backend && ./.venv/bin/alembic downgrade 0003_create_cash_balances` passed.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 41 tests passed in 0.36s.
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
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added normalized stock/ETF position model `backend/app/models/stock_position.py`.
  - Added migration `backend/alembic/versions/0005_create_stock_positions.py`.
  - Added `backend/app/schemas/stock_position.py` with symbol normalization, source, freshness, and safe raw provider payload support.
  - Added `backend/app/services/portfolio/stock_positions.py`.
  - Added `POST /accounts/{account_id}/stock-positions` and `GET /accounts/{account_id}/stock-positions` to portfolio routes.
  - Added unit tests for model/schema behavior and API tests for create/list/missing-account/validation paths.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0005_create_stock_positions`.
  - `cd backend && ./.venv/bin/alembic downgrade 0003_create_cash_balances` passed.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed.
  - `cd backend && ./.venv/bin/alembic current` reported `0005_create_stock_positions (head)`.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 41 tests passed in 0.36s.
- Status: `done`

### P3-T3 - Option Contracts

- Task id: `P3-T3`
- Title: option_contracts
- Objective: Normalize option contract identity for SnapTrade option holdings, manual entry, CSV fallback, and future market quotes.
- Files expected to change:
  - `backend/app/models/option_contract.py`
  - `backend/app/schemas/option_contract.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_option_contract_model.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added normalized option contract model `backend/app/models/option_contract.py`.
  - Added migration `backend/alembic/versions/0006_create_option_contracts.py`.
  - Added `backend/app/schemas/option_contract.py` with OCC symbol normalization, option type, style, expiration, strike, and multiplier validation.
  - Added `backend/app/services/portfolio/option_contracts.py` to resolve contracts idempotently by OCC symbol.
  - Added unit tests for option contract model and schema behavior using synthetic contract data.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0006_create_option_contracts`.
  - `cd backend && ./.venv/bin/alembic downgrade 0005_create_stock_positions` passed as part of the Phase 3 migration round-trip.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed after downgrade.
  - `cd backend && ./.venv/bin/alembic current` reported `0007_create_option_positions (head)`.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 56 tests passed in 0.52s after the migration round-trip.
- Status: `done`

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
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added normalized account-scoped option position model `backend/app/models/option_position.py`.
  - Added migration `backend/alembic/versions/0007_create_option_positions.py`.
  - Added `backend/app/schemas/option_position.py` with long/short position side, status, source, freshness, nested contract payload, and safe raw provider payload support.
  - Added `backend/app/services/portfolio/option_positions.py` to create/list option positions and reuse option contracts by OCC symbol.
  - Added `POST /accounts/{account_id}/option-positions` and `GET /accounts/{account_id}/option-positions` to portfolio routes.
  - Added API tests for create/list flows, missing account handling, and idempotent contract reuse.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0007_create_option_positions`.
  - `cd backend && ./.venv/bin/alembic downgrade 0005_create_stock_positions` passed as part of the Phase 3 migration round-trip.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed after downgrade.
  - `cd backend && ./.venv/bin/alembic current` reported `0007_create_option_positions (head)`.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 56 tests passed in 0.52s after the migration round-trip.
- Status: `done`

### P3-T5 - Portfolio Summary

- Task id: `P3-T5`
- Title: portfolio summary
- Objective: Compute a deterministic account portfolio summary from internal cash, stock, and option storage.
- Files expected to change:
  - `backend/app/services/portfolio/summary.py`
  - `backend/app/schemas/portfolio.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/tests/services/test_portfolio_summary.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added deterministic portfolio summary schema `backend/app/schemas/portfolio.py`.
  - Added portfolio summary service `backend/app/services/portfolio/summary.py`.
  - Added `GET /accounts/{account_id}/portfolio` to portfolio routes.
  - Summary currently aggregates latest cash, stock market value, option market value, position counts, data sources, and freshness statuses from internal normalized tables only.
  - Summary remains independent of broker sync, market data providers, LLMs, and TradingAgents.
  - Added service tests with synthetic cash, stock, and option records.
  - Added API flow test that creates internal portfolio records and verifies the summary response.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 56 tests passed in 0.52s.
- Status: `done`

### P3-T6 - Portfolio Storage Tests

- Task id: `P3-T6`
- Title: portfolio storage tests
- Objective: Ensure cash, stock, option contract, option position, and summary flows work together using synthetic data.
- Files expected to change:
  - `backend/tests/api/test_portfolio.py`
  - `backend/tests/services/test_portfolio_summary.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Moved the reusable database cleanup fixture to `backend/tests/conftest.py` so API and service tests can share it.
  - Added end-to-end internal portfolio API test `backend/tests/api/test_portfolio.py`.
  - Added direct portfolio summary service test `backend/tests/services/test_portfolio_summary.py`.
  - Added option contract and option position API/unit coverage.
  - Confirmed all test data is synthetic and no external APIs, broker credentials, LLM calls, or TradingAgents imports are required.
  - `cd backend && ./.venv/bin/python -m pytest` passed before the migration round-trip: 56 tests passed in 0.56s.
  - `cd backend && ./.venv/bin/python -m pytest` passed after the migration round-trip: 56 tests passed in 0.52s.
- Status: `done`

### P3-T7 - Portfolio Summary Correctness Hardening

- Task id: `P3-T7`
- Title: portfolio summary correctness hardening
- Objective: Fix Phase 3 portfolio summary semantics before broker sync foundation begins by preventing duplicate snapshot aggregation and applying correct option liability sign handling.
- Files expected to change:
  - `backend/app/services/portfolio/summary.py`
  - `backend/tests/api/test_portfolio.py`
  - `backend/tests/services/test_portfolio_summary.py`
  - `backend/tests/regression/test_portfolio_summary_regressions.py`
  - `backend/README.md`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P3-T6`
- Implementation steps:
  1. Keep cash balance logic unchanged; cash summary already uses the correct latest-snapshot pattern via `as_of DESC` and `created_at DESC`.
  2. Treat stock and option position rows as immutable observations for the early MVP.
  3. Update portfolio summary to use only the latest stock row per `(account_id, symbol)`. Do not add a stock `status` column in this task.
  4. Update portfolio summary to use only the latest open option row per `(account_id, option_contract_id)`.
  5. Use deterministic latest-row ordering, such as `as_of DESC`, `created_at DESC`, and `id DESC`, so ties resolve predictably.
  6. Aggregate option market value with `position_side` semantics: long option market value adds to net value, short option market value subtracts as a liability.
  7. Update existing API and service assertions from `Decimal("14710.00")` to `Decimal("14290.00")` for the synthetic account with `10000` cash, `4500` stock value, and `210` short option liability.
  8. Add regression tests in `backend/tests/regression/test_portfolio_summary_regressions.py` for repeated stock snapshots, repeated option snapshots, long option value, and short option liability.
  9. Mark the regression tests with `pytest.mark.regression` and `pytest.mark.db` when database fixtures are used.
  10. Refresh `backend/README.md` to reflect the actual Phase 1-3 backend surface.
  11. Do not add migrations, database constraints, new indexes, service-layer commit refactors, broker sync code, SnapTrade code, market data code, frontend code, or TradingAgents integration in this task.
- Acceptance criteria:
  - Repeated stock snapshots for the same account/symbol do not inflate portfolio summary.
  - Repeated option snapshots for the same account/option contract do not inflate portfolio summary.
  - Long option market value increases net option value.
  - Short option market value reduces net option value and `total_internal_value`.
  - Existing API/service tests reflect `10000 + 4500 - 210 = 14290`.
  - The regression pytest marker is exercised by at least one test.
  - Summary remains independent of broker sync, market data providers, LLMs, frontend code, and TradingAgents.
  - No real broker data, credentials, API keys, reports, imports, exports, or private configs are used.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd backend && ./.venv/bin/alembic current`
  - `cd backend && ./.venv/bin/alembic upgrade head`
- Rollback notes:
  - Revert summary service changes, remove the new regression tests, restore prior summary assertions, and revert the backend README refresh.
- Deferrals:
  - Insert-level idempotency and uniqueness for repeated provider sync payloads are deferred to Phase 7 SnapTrade portfolio normalization or a separate hardening task.
  - Covering indexes such as `(account_id, symbol, as_of)` or `(account_id, option_contract_id, as_of)` are deferred to a schema/performance hardening task.
  - Service-layer commit boundary refactors, migration round-trip pytest automation, CHECK constraints, snapshot uniqueness constraints, and broader pagination/latest-filter API design are out of scope for P3-T7.
- Verification notes:
  - Updated `backend/app/services/portfolio/summary.py` to summarize latest stock snapshots per `(account_id, symbol)` and latest open option snapshots per `(account_id, option_contract_id)`.
  - Kept cash balance summary logic unchanged because it already uses the latest cash snapshot.
  - Applied option sign semantics in the summary: long option market value adds to net value and short option market value subtracts as a liability.
  - Updated existing API and service expectations from `14710.00` to `14290.00` for the synthetic short-put scenario.
  - Added regression tests in `backend/tests/regression/test_portfolio_summary_regressions.py` covering repeated stock snapshots, repeated option snapshots, long option value, and short option liability.
  - Refreshed `backend/README.md` to reflect the actual Phase 1-3 backend surface.
  - Did not add migrations, constraints, indexes, broker sync code, SnapTrade code, market data code, frontend code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 59 tests passed in 0.63s.
  - `cd backend && ./.venv/bin/alembic current` reported `0007_create_option_positions (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed with no pending migrations.
- Status: `done`

### P3-T8 - Portfolio Storage and Migration Hardening

- Task id: `P3-T8`
- Title: portfolio storage and migration hardening
- Objective: Track non-blocking storage, transaction-boundary, and migration-test hardening items discovered during Phase 3 review without expanding P3-T7.
- Files expected to change:
  - `backend/app/models/*`
  - `backend/app/services/*`
  - `backend/alembic/versions/*`
  - `backend/tests/db/*`
  - `backend/tests/regression/*`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P3-T7`
- Implementation steps:
  1. Evaluate service-layer commit boundary refactor or a future unit-of-work pattern before broker sync writes multiple rows atomically.
  2. Evaluate database CHECK constraints for enum-like string columns.
  3. Evaluate snapshot uniqueness constraints or provider-source idempotency keys after Phase 7 normalization requirements are clearer.
  4. Evaluate covering indexes for latest-position summary queries after query shape and expected data volume are clearer.
  5. Evaluate a dedicated migration round-trip pytest strategy using an isolated migration test database.
- Acceptance criteria:
  - Hardening scope is explicitly approved before implementation.
  - No hardening change is mixed into feature work without a focused task and tests.
- Phase-gate note:
  - This is a tracked future hardening stub, not a blocker for starting Phase 4 after P3-T7 is complete.
  - Do not implement this broad task without breaking it into smaller approved tasks.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - Migration-specific commands to be defined when this task is approved.
- Rollback notes:
  - Revert any hardening migrations, service refactors, and associated tests from the focused hardening task.
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
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added user-scoped broker connection metadata model `backend/app/models/broker_connection.py`.
  - Added migration `backend/alembic/versions/0008_create_broker_connections.py`.
  - Added `backend/app/schemas/broker_connection.py` with provider, connection status, sync status, data freshness status, timestamps, scopes, metadata, and `secret_ref`.
  - Added schema validation to reject obvious plaintext credential material in `secret_ref`.
  - Added unit tests for broker connection model registration, columns, constraints, indexes, and schema validation.
  - Updated shared database test cleanup fixture to remove broker connection rows before users.
  - Did not add broker account mapping, sync runs, SnapTrade adapter code, endpoints, external API calls, frontend code, market data code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0008_create_broker_connections`.
  - `cd backend && ./.venv/bin/alembic downgrade 0007_create_option_positions` passed.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed after downgrade.
  - `cd backend && ./.venv/bin/alembic current` reported `0008_create_broker_connections (head)`.
  - `cd backend && ./.venv/bin/python -m pytest` passed after the migration round-trip: 65 tests passed in 0.57s.
- Status: `done`

### P4-T2 - broker_accounts

- Task id: `P4-T2`
- Title: broker_accounts
- Objective: Map provider accounts to internal accounts without coupling internal IDs to SnapTrade IDs.
- Files expected to change:
  - `backend/app/models/broker_account.py`
  - `backend/app/schemas/broker_account.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_broker_account_model.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added provider-account mapping model `backend/app/models/broker_account.py`.
  - Added migration `backend/alembic/versions/0009_create_broker_accounts.py`.
  - Added `backend/app/schemas/broker_account.py` with broker connection ID, optional internal account ID, provider account ID, display name, account type, base currency, sync status, freshness status, last successful sync timestamp, and safe raw payload metadata.
  - Enforced uniqueness on `(broker_connection_id, provider_account_id)`.
  - Added indexes for broker connection lookup, mapped internal account lookup, and connection/freshness filtering.
  - Added unit tests for broker account model registration, columns, constraints, indexes, and schema validation.
  - Updated shared database test cleanup fixture to remove broker account rows before broker connections.
  - Did not add broker sync runs, provider credentials metadata, broker sync interfaces, SnapTrade adapter code, endpoints, external API calls, frontend code, market data code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0009_create_broker_accounts`.
  - `cd backend && ./.venv/bin/alembic downgrade 0008_create_broker_connections` passed.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed after downgrade.
  - `cd backend && ./.venv/bin/alembic current` reported `0009_create_broker_accounts (head)`.
  - `cd backend && ./.venv/bin/python -m pytest` passed after the migration round-trip: 71 tests passed in 0.58s.
- Status: `done`

### P4-T3 - broker_sync_runs

- Task id: `P4-T3`
- Title: broker_sync_runs
- Objective: Track individual broker sync attempts for observability, retries, and stale-data warnings.
- Files expected to change:
  - `backend/app/models/broker_sync_run.py`
  - `backend/app/schemas/broker_sync_run.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_broker_sync_run_model.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added broker sync run metadata model `backend/app/models/broker_sync_run.py`.
  - Added migration `backend/alembic/versions/0010_create_broker_sync_runs.py`.
  - Added `backend/app/schemas/broker_sync_run.py` with broker connection/account links, trigger, status, started/completed timestamps, provider request ID, count fields, sanitized error JSONB, and summary JSONB.
  - Linked sync runs to `broker_connections` and optionally to `broker_accounts`.
  - Added schema validation for non-negative counts and completion timestamps after start timestamps.
  - Added unit tests for broker sync run model registration, columns, indexes, defaults, metadata, count validation, and timestamp validation.
  - Updated shared database test cleanup fixture to remove broker sync run rows before broker accounts and broker connections.
  - Did not add provider credentials metadata, broker sync interfaces, SnapTrade adapter code, endpoints, external API calls, frontend code, market data code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0010_create_broker_sync_runs`.
  - `cd backend && ./.venv/bin/alembic downgrade 0009_create_broker_accounts` passed.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed after downgrade.
  - `cd backend && ./.venv/bin/alembic current` reported `0010_create_broker_sync_runs (head)`.
  - `cd backend && ./.venv/bin/python -m pytest` passed after the migration round-trip: 78 tests passed in 0.59s.
- Status: `done`

### P4-T4 - Provider Credentials Metadata

- Task id: `P4-T4`
- Title: provider_credentials_metadata or secret reference model
- Objective: Store provider credential metadata and secret references without storing plaintext secrets.
- Files expected to change:
  - `backend/app/models/provider_credentials_metadata.py`
  - `backend/app/schemas/provider_credentials_metadata.py`
  - `backend/alembic/versions/*`
  - `backend/tests/unit/test_provider_credentials_metadata_model.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added provider credential metadata model `backend/app/models/provider_credentials_metadata.py`.
  - Added migration `backend/alembic/versions/0011_create_provider_credentials_metadata.py` with revision ID `0011_provider_credentials`.
  - Added `backend/app/schemas/provider_credentials_metadata.py` with provider, credential name, scopes, status, last tested timestamp, metadata, and exactly one of `secret_ref` or `encrypted_secret_ref`.
  - Added public read schema that does not expose secret references by default, plus an explicit internal read schema for backend-only use.
  - Added schema validation to reject obvious plaintext credential material in secret reference fields.
  - Added unit tests for provider credential metadata model registration, columns, indexes, schema normalization, reference exclusivity, plaintext-secret rejection, and public/internal read schema separation.
  - Updated shared database test cleanup fixture to remove provider credential metadata rows before users.
  - Did not read `.env`, store real credentials, add provider HTTP calls, add frontend exposure, add SnapTrade adapter code, add endpoints, add market data code, or modify TradingAgents.
  - `cd backend && ./.venv/bin/alembic upgrade head` initially exposed that the long Alembic revision ID exceeded Alembic's `version_num` column; the migration revision ID was shortened to `0011_provider_credentials`.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed, applying `0011_provider_credentials`.
  - `cd backend && ./.venv/bin/alembic downgrade 0010_create_broker_sync_runs` passed.
  - `cd backend && ./.venv/bin/alembic upgrade head` passed after downgrade.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/python -m pytest` passed after the migration round-trip: 87 tests passed in 0.57s.
- Status: `done`

### P4-T5 - Broker Sync Status Enums

- Task id: `P4-T5`
- Title: connection_status, sync_status, data_freshness_status enums
- Objective: Standardize broker connection and freshness status values used by SnapTrade and future providers.
- Files expected to change:
  - `backend/app/services/broker_import/statuses.py`
  - `backend/app/schemas/broker_sync_status.py`
  - `backend/tests/unit/test_broker_sync_statuses.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added centralized broker sync status constants and helpers in `backend/app/services/broker_import/statuses.py`.
  - Added broker sync status schema aliases and catalog model in `backend/app/schemas/broker_sync_status.py`.
  - Updated broker connection, broker account, and broker sync run schemas to use the centralized status type aliases.
  - Kept sync run records from accepting `idle`; `idle` remains valid for connection/account sync state but not for individual sync run rows.
  - Added unit tests for status constants, helper predicates, catalog output, schema acceptance, and sync-run rejection of `idle`.
  - Did not add migrations, database constraints, endpoints, provider calls, SnapTrade adapter code, frontend code, market data code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 92 tests passed in 0.71s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
- Status: `done`

### P4-T6 - Broker Sync Interfaces

- Task id: `P4-T6`
- Title: broker sync interfaces
- Objective: Define app-owned broker sync service boundaries before adding SnapTrade-specific code.
- Files expected to change:
  - `backend/app/services/broker_import/interfaces.py`
  - `backend/app/services/broker_import/models.py`
  - `backend/tests/services/test_broker_sync_interfaces.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added provider-neutral broker sync snapshot and request/result models in `backend/app/services/broker_import/models.py`.
  - Added `BrokerSyncService` protocol in `backend/app/services/broker_import/interfaces.py`.
  - Kept the interface app-owned and provider-neutral; the read-only `BrokerPortfolioProvider` and SnapTrade adapter remain Phase 5 work.
  - Added service tests in `backend/tests/services/test_broker_sync_interfaces.py` using a synthetic fake broker sync service with no network, credentials, or provider SDK.
  - Added validation tests for invalid triggers, invalid status values, and invalid sync result states.
  - Did not add migrations, endpoints, provider credentials changes, SnapTrade adapter code, external API calls, frontend code, market data code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 98 tests passed in 0.77s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
- Status: `done`

### P4-T7 - Broker Sync Foundation Tests

- Task id: `P4-T7`
- Title: broker sync foundation tests
- Objective: Cover broker connection/account/sync metadata, statuses, and safe secret-reference behavior.
- Files expected to change:
  - `backend/tests/api/test_broker_sync_foundation.py`
  - `backend/tests/services/test_broker_sync_interfaces.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added broker sync foundation smoke tests in `backend/tests/api/test_broker_sync_foundation.py`.
  - Added assertions that OpenAPI does not expose `secret_ref` or `encrypted_secret_ref`.
  - Added synthetic fake secret-reference test using `secret://snaptrade/synthetic-user`.
  - Reused `backend/tests/services/test_broker_sync_interfaces.py` to cover status and interface behavior.
  - Confirmed all broker sync foundation tests are synthetic and require no network, real credentials, broker data, SnapTrade SDK, or TradingAgents import.
  - Did not add routes, external API calls, frontend code, market data code, SnapTrade adapter code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 98 tests passed in 0.77s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
- Status: `done`

## Phase 5 - SnapTrade Read-Only Adapter, Mock-First

### P5-T1 - BrokerPortfolioProvider Interface

- Task id: `P5-T1`
- Title: BrokerPortfolioProvider interface
- Objective: Define the read-only provider interface for account, balance, position, option position, transaction, and refresh operations.
- Files expected to change:
  - `backend/app/services/broker_import/providers/base.py`
  - `backend/app/services/broker_import/providers/models.py`
  - `backend/tests/adapters/test_broker_portfolio_provider_interface.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added provider-facing read-only model contract in `backend/app/services/broker_import/providers/models.py`.
  - Added `BrokerPortfolioProvider` protocol in `backend/app/services/broker_import/providers/base.py`.
  - Added provider package marker `backend/app/services/broker_import/providers/__init__.py`.
  - Covered account, balance, stock/ETF position, option position, transaction, and refresh operations.
  - Included provider, sync timestamp, received timestamp, sync status, and data freshness status in provider models.
  - Kept market data quotes/chains and trading/order methods out of the provider interface.
  - Added adapter contract tests in `backend/tests/adapters/test_broker_portfolio_provider_interface.py` using a synthetic fake provider only.
  - Did not add SnapTrade adapter code, config, credentials, endpoints, external API calls, frontend code, market data code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 102 tests passed in 0.74s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
- Status: `done`

### P5-T2 - SnapTradeAdapter Skeleton

- Task id: `P5-T2`
- Title: SnapTradeAdapter skeleton
- Objective: Add a read-only SnapTrade adapter shell that does not call trading/order endpoints.
- Files expected to change:
  - `backend/app/services/broker_import/providers/snaptrade.py`
  - `backend/tests/adapters/test_snaptrade_adapter_skeleton.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added read-only `SnapTradeAdapter` skeleton in `backend/app/services/broker_import/providers/snaptrade.py`.
  - Added `SnapTradeAdapterNotConfiguredError` for clear failures until config and mocked/real integration tasks land.
  - Implemented the `BrokerPortfolioProvider` protocol methods only: connections, accounts, balances, positions, option positions, transactions, and refresh.
  - Added explicit tests that forbidden trading/order methods such as place/submit/cancel/execute trade are not exposed.
  - Added tests that every read-only method raises the not-configured error instead of making network calls.
  - Did not add config, credentials, SnapTrade SDK usage, HTTP calls, endpoints, frontend code, market data code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 112 tests passed in 1.13s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
- Status: `done`

### P5-T3 - SnapTrade Config Names

- Task id: `P5-T3`
- Title: config from environment variable names only
- Objective: Add configuration names for SnapTrade without adding real credentials or reading private `.env` content.
- Files expected to change:
  - `backend/app/core/config.py`
  - `.env.example`
  - `backend/tests/unit/test_config.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added SnapTrade config field names to `backend/app/core/config.py`: `SNAPTRADE_CLIENT_ID`, `SNAPTRADE_CONSUMER_KEY`, and `SNAPTRADE_ENVIRONMENT`.
  - Kept runtime defaults safe: SnapTrade credential values default to empty strings and environment defaults to `sandbox`.
  - Added placeholder-only entries to `.env.example`.
  - Updated config tests to use synthetic monkeypatched values only.
  - Added test coverage that SnapTrade config defaults do not contain real-looking credentials.
  - Did not read, print, or modify `.env` or any private config.
  - Did not add real credentials, external API calls, SnapTrade SDK usage, endpoints, frontend code, market data code, or TradingAgents integration.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 113 tests passed in 0.78s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
- Status: `done`

### P5-T4 - SnapTrade Exceptions and Response Models

- Task id: `P5-T4`
- Title: exception classes and response models
- Objective: Add app-owned exceptions and typed response models for SnapTrade adapter behavior.
- Files expected to change:
  - `backend/app/services/broker_import/providers/exceptions.py`
  - `backend/app/services/broker_import/providers/snaptrade_models.py`
  - `backend/tests/adapters/test_snaptrade_models.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added app-owned broker provider exceptions for unavailable provider, auth failure, reauth required, rate limit, and stale data cases.
  - Added typed SnapTrade response models for user registration, connection portal URL, connections, accounts, balances, positions, option positions, transactions, and refresh results.
  - Added model-to-provider snapshot/result mapping helpers so the rest of the app can depend on provider-neutral broker sync types.
  - Added validation that secret material must be represented by a safe secret reference, not plaintext SnapTrade secrets.
  - Added adapter tests for exception mapping, response validation, status validation, and provider-neutral conversion.
  - Did not add the SnapTrade SDK, make network calls, read `.env`, or add real credentials.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 127 tests passed, 1 deselected in 0.82s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P5-T5 - Mocked SnapTrade User and Account Tests

- Task id: `P5-T5`
- Title: mocked tests for register user, connection portal URL, and list accounts
- Objective: Test SnapTrade registration, connection portal URL, and account listing with mocked HTTP responses.
- Files expected to change:
  - `backend/tests/adapters/test_snaptrade_user_and_accounts.py`
  - `backend/app/services/broker_import/providers/snaptrade.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added a dependency-injected read-only SnapTrade client protocol to the adapter skeleton.
  - Added mocked adapter methods for register user, create connection portal URL, list connections, and list accounts.
  - Added synthetic mocked tests that verify safe secret-reference handling and no frontend exposure of SnapTrade user secrets.
  - Kept adapter behavior read-only and confirmed trading/order methods remain absent.
  - Did not add real HTTP calls, credentials, SDK usage, frontend code, or endpoint code.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 127 tests passed, 1 deselected in 0.82s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P5-T6 - Mocked SnapTrade Portfolio Data Tests

- Task id: `P5-T6`
- Title: mocked tests for balances, positions, and option positions
- Objective: Test read-only SnapTrade account data methods with synthetic mocked payloads.
- Files expected to change:
  - `backend/tests/adapters/test_snaptrade_portfolio_data.py`
  - `backend/app/services/broker_import/providers/snaptrade.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added mocked read-only adapter coverage for balances, stock/ETF positions, option positions, transactions, and account refresh status.
  - Verified broker sync snapshots expose broker/account holdings fields only and do not become market quote objects with bid/ask/quote timestamps.
  - Preserved raw provider payload as optional synthetic metadata for later normalization while keeping market data architecture separate.
  - Did not add business normalization, database writes, external calls, market-data provider code, or SnapTrade trading/order behavior.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 127 tests passed, 1 deselected in 0.82s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P5-T7 - External Test Guardrails

- Task id: `P5-T7`
- Title: external tests skipped by default
- Objective: Prepare optional external SnapTrade tests that are disabled unless explicitly selected later.
- Files expected to change:
  - `backend/tests/adapters/test_snaptrade_external.py`
  - `backend/tests/README.md`
  - `backend/pytest.ini`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added a SnapTrade external-test placeholder marked `external` and skipped by default.
  - Updated backend test docs to make real provider tests opt-in only, with no `.env`, broker credential, account data, or secret reads/prints.
  - Documented that mocked SnapTrade tests are the default and real-provider coverage requires an approved external-test plan.
  - Confirmed `backend/pytest.ini` excludes `external` and `slow` tests from the default suite.
  - Did not run `pytest -m external` because real-provider testing has not been explicitly configured or approved.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 127 tests passed, 1 deselected in 0.82s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

## Phase 6 - SnapTrade Connection Flow Backend

### P6-T1 - Register SnapTrade User Endpoint

- Task id: `P6-T1`
- Title: backend endpoint to register/create SnapTrade user
- Objective: Add backend-only flow for creating or resolving a SnapTrade user without exposing secrets to frontend.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/snaptrade_connection.py`
  - `backend/tests/api/test_snaptrade_connection_flow.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added backend-only SnapTrade user registration endpoint at `POST /broker-sync/snaptrade/users`.
  - Added `snaptrade_connection` service that stores SnapTrade user metadata in `provider_credentials_metadata` with a backend-only safe credential reference.
  - API response returns only provider, SnapTrade user id, and credential metadata id; it does not return credential references or provider secrets.
  - API tests mock the adapter and verify no provider secrets appear in responses.
  - Did not add real SnapTrade SDK calls, external API calls, frontend code, or portfolio normalization.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 140 tests passed, 1 deselected in 1.12s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P6-T2 - Connection Portal URL Endpoint

- Task id: `P6-T2`
- Title: backend endpoint to generate connection portal URL
- Objective: Generate a SnapTrade connection portal URL through the backend only.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/snaptrade_connection.py`
  - `backend/tests/api/test_snaptrade_connection_flow.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added backend-only connection portal endpoint at `POST /broker-sync/snaptrade/connection-portal`.
  - Endpoint looks up the stored SnapTrade user metadata and credential reference server-side.
  - Response returns only the portal URL and expiration metadata, never SnapTrade user secrets or credential references.
  - Added mocked API tests for successful portal generation and missing-registration conflict behavior.
  - Did not expose SnapTrade secrets to frontend or read `.env`.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 140 tests passed, 1 deselected in 1.12s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P6-T3 - List Broker Connections Endpoint

- Task id: `P6-T3`
- Title: endpoint to list broker connections
- Objective: List broker connections and statuses for a user.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/connections.py`
  - `backend/tests/api/test_broker_connections.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added `GET /users/{user_id}/broker-connections`.
  - Added broker connection listing service scoped by user id and active/non-deleted connections.
  - Response model excludes `secret_ref`, raw provider metadata, and private credential fields.
  - Added API tests that prove connection listing omits secret references.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 140 tests passed, 1 deselected in 1.12s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P6-T4 - List Broker Accounts Endpoint

- Task id: `P6-T4`
- Title: endpoint to list broker accounts
- Objective: List provider accounts mapped to internal accounts.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/accounts.py`
  - `backend/tests/api/test_broker_accounts.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added `GET /broker-connections/{broker_connection_id}/accounts`.
  - Added broker account listing service scoped by broker connection id.
  - Response model includes provider account id, optional mapped internal account id, sync status, and freshness while excluding raw provider payloads.
  - Added API tests with synthetic provider account data.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 140 tests passed, 1 deselected in 1.12s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P6-T5 - Sync Account Data Endpoint

- Task id: `P6-T5`
- Title: endpoint to sync account data
- Objective: Trigger a read-only SnapTrade account sync through backend services.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/sync.py`
  - `backend/tests/api/test_broker_sync.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added `POST /broker-accounts/{broker_account_id}/sync`.
  - Added read-only broker sync service that creates a traceable `broker_sync_runs` record.
  - Mocked provider calls cover account refresh, balances, stock/ETF positions, and option positions, but do not normalize data into portfolio tables yet.
  - Sync summary records counts and safe metadata only; no trading/order calls are implemented.
  - Added API tests for successful sync and reauthorization failure as a failed sync run.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 140 tests passed, 1 deselected in 1.12s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P6-T6 - Broker Sync Run Status Endpoint

- Task id: `P6-T6`
- Title: endpoint to inspect broker sync run status
- Objective: Let UI inspect broker sync progress, errors, and freshness status.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/sync_runs.py`
  - `backend/tests/api/test_broker_sync_runs.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added `GET /broker-sync-runs/{sync_run_id}`.
  - Added sync run lookup service and safe public response model for sync status, counts, timestamps, sanitized error, and summary fields.
  - Added API tests for existing and missing sync run lookups.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 140 tests passed, 1 deselected in 1.12s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P6-T7 - SnapTrade Connection Flow API Tests

- Task id: `P6-T7`
- Title: mocked API tests only
- Objective: Cover SnapTrade connection and sync endpoints using mocked provider responses only.
- Files expected to change:
  - `backend/tests/api/test_snaptrade_connection_flow.py`
  - `backend/tests/api/test_broker_sync.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added mocked API coverage across the Phase 6 SnapTrade connection and sync flow.
  - Covered happy-path registration, portal URL generation, connection listing, account listing, sync creation, sync status lookup, missing resources, provider unavailable, and reauthorization-required scenarios.
  - Assertions verify API responses do not expose credential references, provider secrets, raw provider payloads, or private account data.
  - Default test suite still deselects external tests and makes no real SnapTrade calls.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 140 tests passed, 1 deselected in 1.12s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

## Phase 7 - SnapTrade Portfolio Normalization

### P7-T1 - Balances to Cash Balances

- Task id: `P7-T1`
- Title: map balances to cash_balances
- Objective: Normalize SnapTrade balances into internal cash snapshot records.
- Files expected to change:
  - `backend/app/services/broker_import/normalization/cash.py`
  - `backend/tests/services/test_snaptrade_cash_normalization.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added SnapTrade balance normalization into internal `cash_balances` snapshots.
  - Mapped provider total cash and available cash into total/free cash using conservative zero defaults for reserved collateral, premium income, and DCA cash.
  - Preserved provider account reference, source, data freshness, and sync timestamp.
  - Added synthetic service tests for available-cash and missing-available-cash cases.
  - Did not add migrations, endpoints, real provider calls, or business strategy logic.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 152 tests passed, 1 deselected in 1.27s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P7-T2 - Stock/ETF Position Normalization

- Task id: `P7-T2`
- Title: map stock/ETF positions to stock_positions
- Objective: Normalize SnapTrade stock/ETF holdings into internal stock position records.
- Files expected to change:
  - `backend/app/services/broker_import/normalization/stocks.py`
  - `backend/tests/services/test_snaptrade_stock_normalization.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added SnapTrade stock/ETF normalization into internal `stock_positions` snapshots.
  - Mapped symbol, asset type, quantity, market value, source reference, freshness, and as-of timestamp.
  - Preserved sanitized raw provider metadata and intentionally left `market_price` unset so broker holdings are not treated as live market quotes.
  - Added synthetic service tests for stock normalization and quote-separation behavior.
  - Did not add market-data provider logic or dashboard endpoints.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 152 tests passed, 1 deselected in 1.27s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P7-T3 - Option Position Normalization

- Task id: `P7-T3`
- Title: map option positions to option_contracts and option_positions
- Objective: Normalize SnapTrade option holdings into contracts and account positions.
- Files expected to change:
  - `backend/app/services/broker_import/normalization/options.py`
  - `backend/tests/services/test_snaptrade_option_normalization.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added OCC option symbol parsing for synthetic SnapTrade option identifiers.
  - Added option normalization into `option_contracts` and `option_positions` using existing contract get-or-create behavior.
  - Mapped underlying, expiration, strike, option type, position side, quantity, market value, source reference, freshness, and as-of timestamp.
  - Added synthetic tests for OCC parsing, option contract/position creation, and idempotent contract/position resolution.
  - Did not add deterministic option strategy calculations or market quote logic.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 152 tests passed, 1 deselected in 1.27s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P7-T4 - Safe Raw Provider Payloads

- Task id: `P7-T4`
- Title: preserve safe raw provider payload in JSONB where useful
- Objective: Retain useful provider metadata for audit/debugging without storing secrets or unsafe payloads.
- Files expected to change:
  - `backend/app/services/broker_import/normalization/sanitization.py`
  - `backend/tests/services/test_provider_payload_sanitization.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added recursive provider payload sanitization for raw metadata that may be retained for audit/debugging.
  - Redacts secret-like fields such as token, authorization, password, API key, credential, and secret keys.
  - Added unit tests for nested dictionaries, lists, scalar values, and null payloads.
  - Did not store real provider payloads or credentials.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 152 tests passed, 1 deselected in 1.27s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P7-T5 - Reconciliation and Duplicate Handling

- Task id: `P7-T5`
- Title: reconciliation and duplicate handling
- Objective: Prevent duplicated positions and handle provider updates deterministically.
- Files expected to change:
  - `backend/app/services/broker_import/reconciliation.py`
  - `backend/tests/services/test_broker_reconciliation.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added application-level reconciliation helpers for provider snapshot source references and existing cash/stock/option snapshot lookup.
  - Idempotency is based on account, source, provider account/symbol or contract reference, and as-of timestamp.
  - Added synthetic tests proving repeated cash and stock snapshots update the existing row instead of duplicating holdings.
  - Kept database uniqueness constraints and covering indexes deferred to a later hardening task as planned.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 152 tests passed, 1 deselected in 1.27s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P7-T6 - SnapTrade Normalization Tests

- Task id: `P7-T6`
- Title: tests with synthetic mocked SnapTrade payloads
- Objective: Cover end-to-end normalization from mocked SnapTrade portfolio payloads into internal tables.
- Files expected to change:
  - `backend/tests/services/test_snaptrade_normalization_end_to_end.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Added end-to-end synthetic normalization test from mocked SnapTrade balance, stock/ETF positions, and option positions into internal tables.
  - Verified cash, stock, option contract, and option position records are created with SnapTrade source, freshness, and as-of metadata.
  - Confirmed normalization remains internal service-layer behavior; no real provider calls, frontend code, market data, TradingAgents integration, or automatic trading was added.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 152 tests passed, 1 deselected in 1.27s.
  - `cd backend && ./.venv/bin/alembic current` reported `0011_provider_credentials (head)`.
  - `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P7-T7 - Pre-Real SnapTrade Integration Hardening

- Task id: `P7-T7`
- Title: pre-real SnapTrade / Fidelity integration hardening
- Objective: Close the security, ownership, ingestion, and normalization gaps required before a real read-only SnapTrade/Fidelity integration spike.
- Migration impact:
  - No new migrations required; uses the existing `encrypted_secret_ref` column, a JSON encryption envelope with `key_id`, and existing `String(40)` freshness columns.
- Files expected to change:
  - `.env.example`
  - `backend/app/core/config.py`
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/schemas/broker_sync_api.py`
  - `backend/app/schemas/cash_balance.py`
  - `backend/app/schemas/stock_position.py`
  - `backend/app/schemas/option_position.py`
  - `backend/app/schemas/provider_credentials_metadata.py`
  - `backend/app/services/broker_import/secrets.py`
  - `backend/app/services/broker_import/snaptrade_connection.py`
  - `backend/app/services/broker_import/connections.py`
  - `backend/app/services/broker_import/accounts.py`
  - `backend/app/services/broker_import/sync.py`
  - `backend/app/services/broker_import/sync_runs.py`
  - `backend/app/services/broker_import/refresh_connections.py`
  - `backend/app/services/broker_import/providers/snaptrade_models.py`
  - `backend/app/services/broker_import/providers/snaptrade.py`
  - `backend/app/services/broker_import/statuses.py`
  - `backend/app/services/broker_import/normalization/options.py`
  - `backend/app/services/broker_import/normalization/sanitization.py`
  - `backend/app/services/accounts.py`
  - `backend/tests/api/test_broker_sync.py`
  - `backend/tests/api/test_snaptrade_connection_flow.py`
  - `backend/tests/api/test_broker_connections.py`
  - `backend/tests/api/test_broker_accounts.py`
  - `backend/tests/api/test_broker_sync_runs.py`
  - `backend/tests/api/test_broker_sync_foundation.py`
  - `backend/tests/api/test_broker_ownership.py`
  - `backend/tests/services/test_secret_encryption.py`
  - `backend/tests/services/test_sync_to_normalization_integration.py`
  - `backend/tests/services/test_snaptrade_refresh_connections.py`
  - `backend/tests/services/test_provider_payload_sanitization.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P7-T6`
- Implementation steps:
  1. (F1, F7, F19) Add `SNAPTRADE_SECRET_ENCRYPTION_KEY` placeholder/config and encrypt SnapTrade `userSecret` into `encrypted_secret_ref`; never persist it in `secret_ref`, raw metadata, logs, API responses, fixtures, or reports. Include a JSON encryption envelope with `key_id`/`KeyVersion` alongside ciphertext so future key rotation does not require a schema change.
  2. (F11) Make SnapTrade registration idempotent: return the existing active credential without re-calling `adapter.register_user`.
  3. (F6, F7, F8, F21) Sanitize and allowlist provider-origin metadata before writing credential metadata, broker connections, broker accounts, sync errors, sync summaries, and raw provider payloads.
  4. (F3, B1) Add a user-scoped `POST /users/{user_id}/broker-sync/snaptrade/refresh-connections` endpoint that persists mocked SnapTrade connections/accounts. For each provider account, look up an internal `Account` by `(user_id, broker_name, account_type)`; if a matching `Account` exists with no current `BrokerAccount.account_id` pointing at it, reuse it and flip `is_manual` to `false`; otherwise create a new internal `Account` with `is_manual=false`. Record provider request ID and sanitized warnings, where supplied, on the resulting `BrokerSyncRun.summary` for auditability.
  5. (F5, F13) Convert broker-sync routes/services to user-scoped ownership checks through `BrokerConnection.user_id`, using shared service helpers rather than route-local duplicated joins. Path-scoped route changes:
     - `POST /broker-sync/snaptrade/users` -> `POST /users/{user_id}/broker-sync/snaptrade/register`
     - `POST /broker-sync/snaptrade/connection-portal` -> `POST /users/{user_id}/broker-sync/snaptrade/connection-portal`
     - `GET /broker-connections/{id}/accounts` -> `GET /users/{user_id}/broker-connections/{id}/accounts`
     - `POST /broker-accounts/{id}/sync` -> `POST /users/{user_id}/broker-accounts/{id}/sync`
     - `GET /broker-sync-runs/{id}` -> `GET /users/{user_id}/broker-sync-runs/{id}`
     - `GET /users/{user_id}/broker-connections` remains unchanged.
     Every path-scoped route must JOIN-validate that the resource belongs to `user_id`; path scoping alone is not sufficient.
  6. (F2) Wire sync to normalize balances, stock/ETF positions, and option positions into internal tables. Provider HTTP calls happen before the sync-run / normalization DB transaction begins, so a slow SnapTrade response never holds locks open.
  7a. (F10) Compute `sync_run.status` from the union of refresh result, balance fetch, position fetch, option fetch, and normalization outcomes. `succeeded` requires every step to complete cleanly; `partially_succeeded` applies when any step produced empty/skipped results or any per-row normalization failure; `failed` applies when any required step raises.
  7b. (F15, F16, F17) Make unsupported OCC symbols resilient: catch parse failures per option row, append a sanitized entry to `partial_failures` in `BrokerSyncRun.summary`, and continue. Detect and warn on underlying mismatch. Document the current OCC year window.
  8. (F12) Add active sync-run guard: before inserting a new sync run, look for an existing `(broker_account_id, status in ("queued", "running"))`; if found, return HTTP 409 with the in-flight `sync_run_id` in the response body.
  9. (F4, F22) Unify freshness vocabulary across broker and portfolio schemas. Add a comment explaining that `delayed` on a position/cash snapshot means the broker/provider holdings or balances are not confirmed live, independent of market quote freshness.
  10. (F24, F25) Strengthen broker sync foundation tests with a structural OpenAPI walk and a UUID-shaped negative secret test.
- Acceptance criteria:
  - A UUID-shaped fake secret is rejected from any `secret_ref` write path, accepted into the in-memory `user_secret` field, and persisted only as ciphertext in `encrypted_secret_ref`.
  - The application refuses to start when the SnapTrade adapter is configured (`SNAPTRADE_CLIENT_ID` non-empty) but `SNAPTRADE_SECRET_ENCRYPTION_KEY` is missing or empty.
  - The Pydantic field name `user_secret_ref` is replaced with `user_secret` in `SnapTradeUserRegistrationResponse`; the field is never persisted in its raw shape.
  - OpenAPI and API responses expose no secret reference, ciphertext, provider raw payload, or provider secret fields.
  - Refresh-connections persists synthetic connections/accounts and maps them to internal accounts.
  - Refresh-connections never creates a duplicate internal `Account` when a matching manual `Account` exists.
  - A mocked sync populates `cash_balances`, `stock_positions`, `option_contracts`, and `option_positions`.
  - Delayed/cached/stale/reauth freshness values validate consistently across broker and portfolio schemas.
  - Every broker-sync route returns 404 when the path `user_id` does not own the resource.
  - Concurrent active sync attempts return 409 with the in-flight `sync_run_id` in the response body.
  - Unsupported option symbols do not fail the whole sync.
  - Default `pytest` continues to exclude `external` and `slow` markers and makes zero real SnapTrade calls; any real-integration smoke is opt-in via `pytest -m external` and an explicit `SNAPTRADE_*` configuration.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd backend && ./.venv/bin/alembic current`
  - `cd backend && ./.venv/bin/alembic upgrade head`
- Rollback notes:
  - Remove P7-T7 hardening service/routes/tests and restore Phase 7 mock-only behavior.
- Deferrals:
  - F18 cost-basis provider mapping.
  - F8 value-heuristic sanitizer.
  - F9 DB-level snapshot uniqueness and covering indexes (`P3-T8`).
  - F14 global Unit of Work refactor (`P3-T8`).
  - F23 DB CHECK constraint on exactly one of `secret_ref` / `encrypted_secret_ref` (`P3-T8`).
  - Key rotation strategy beyond the JSON envelope `key_id`.
  - External secret manager backend.
  - Webhook ingestion.
  - Explicit account remap/edit UI.
  - OCC year window beyond 2099.
  - F11 explicit secret rotation path.
- Verification notes:
  - Phase 4-7 baseline was committed before this task as `8f54f7c Add SnapTrade broker sync foundation (Phase 4-7, mock-first)`.
  - Changed files: `.env.example`, `backend/app/core/config.py`, `backend/app/api/routes/broker_sync.py`, `backend/app/schemas/broker_sync_api.py`, `backend/app/schemas/cash_balance.py`, `backend/app/schemas/stock_position.py`, `backend/app/schemas/option_position.py`, `backend/app/schemas/provider_credentials_metadata.py`, `backend/app/services/accounts.py`, `backend/app/services/broker_import/accounts.py`, `backend/app/services/broker_import/connections.py`, `backend/app/services/broker_import/refresh_connections.py`, `backend/app/services/broker_import/secrets.py`, `backend/app/services/broker_import/snaptrade_connection.py`, `backend/app/services/broker_import/statuses.py`, `backend/app/services/broker_import/sync.py`, `backend/app/services/broker_import/sync_runs.py`, `backend/app/services/broker_import/normalization/options.py`, `backend/app/services/broker_import/normalization/sanitization.py`, `backend/app/services/broker_import/providers/snaptrade.py`, `backend/app/services/broker_import/providers/snaptrade_models.py`, adapter/API/service/unit tests listed in this task, and this plan.
  - Secret handling evidence: `backend/tests/services/test_secret_encryption.py`, `backend/tests/api/test_snaptrade_connection_flow.py`, `backend/tests/api/test_broker_sync_foundation.py`, and `backend/tests/unit/test_config.py` verify UUID-shaped secret rejection, encrypted persistence, no raw secret in `provider_credentials_metadata`, in-memory `user_secret`, OpenAPI hiding, and startup failure when SnapTrade is configured without `SNAPTRADE_SECRET_ENCRYPTION_KEY`.
  - Refresh and ownership evidence: `backend/tests/services/test_snaptrade_refresh_connections.py`, `backend/tests/api/test_snaptrade_connection_flow.py`, `backend/tests/api/test_broker_ownership.py`, `backend/tests/api/test_broker_accounts.py`, `backend/tests/api/test_broker_connections.py`, and `backend/tests/api/test_broker_sync_runs.py` verify connection/account ingestion, manual-account dedup, path-scoped routes, removed `provider_connection_id`, and cross-user 404 behavior.
  - Sync and normalization evidence: `backend/tests/api/test_broker_sync.py` and `backend/tests/services/test_sync_to_normalization_integration.py` verify sync populates internal cash/stock/option tables, active sync conflicts return 409 with `sync_run_id`, unsupported OCC rows produce sanitized partial failures, and summaries/errors use typed sanitized payloads.
  - Freshness vocabulary evidence: portfolio schemas now share the broker freshness literal vocabulary including `delayed`, with broker-vs-market freshness documented in `backend/app/services/broker_import/statuses.py`.
  - Test result: `cd backend && ./.venv/bin/python -m pytest` -> `166 passed, 1 deselected in 1.20s`.
  - Alembic result: `cd backend && ./.venv/bin/alembic current` -> `0011_provider_credentials (head)`.
  - Alembic result: `cd backend && ./.venv/bin/alembic upgrade head` completed successfully at head.
  - Residual risk: local envelope encryption is a development bridge until an external secret manager and explicit key rotation strategy are added; DB-level uniqueness/check constraints and a global Unit of Work refactor remain deferred; no real SnapTrade/Fidelity calls were made.
- Status: `done`

## Phase 8 - Portfolio Dashboard Backend from Synced Data

### P8-T1 - Portfolio Summary from Internal Tables

- Task id: `P8-T1`
- Title: portfolio summary from internal tables
- Objective: Serve portfolio summary using normalized synced/manual/CSV records.
- Files expected to change:
  - `backend/app/services/portfolio/summary.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/tests/api/test_portfolio_summary.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Changed files: `backend/app/schemas/portfolio.py`, `backend/app/services/portfolio/summary.py`, `backend/tests/api/test_portfolio.py`, `backend/tests/api/test_portfolio_summary.py`, `backend/tests/services/test_portfolio_summary.py`, and `docs/shared/implementation_plan.md`.
  - Added dashboard-facing as-of metadata: `stock_positions_as_of`, `option_positions_as_of`, and `latest_snapshot_as_of`, while keeping `cash_as_of`, source list, and freshness list.
  - Added API coverage proving `/accounts/{account_id}/portfolio` works after mocked SnapTrade sync normalization populates internal cash, stock, option contract, and option position tables.
  - Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/api/test_portfolio.py tests/api/test_portfolio_summary.py tests/services/test_portfolio_summary.py tests/regression/test_portfolio_summary_regressions.py` -> `6 passed in 0.37s`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `167 passed, 1 deselected in 1.48s`.
- Status: `done`

### P8-T2 - Broker Sync Freshness Endpoint

- Task id: `P8-T2`
- Title: broker sync freshness endpoint
- Objective: Expose broker sync freshness separately from market quote freshness.
- Files expected to change:
  - `backend/app/api/routes/broker_sync.py`
  - `backend/app/services/broker_import/freshness.py`
  - `backend/tests/api/test_broker_sync_freshness.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P8-T1`
- Implementation steps:
  1. Add endpoint for account broker sync freshness.
  2. Include last successful sync, current status, data freshness status, and reauth/error flags.
  3. Do not include market quote freshness here.
  4. Response contract must keep broker-sync freshness separate from market-quote freshness; do not collapse them into a single timestamp.
- Acceptance criteria:
  - UI can display broker sync freshness independently.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove freshness endpoint/service/tests.
- Verification notes:
  - Changed files: `backend/app/api/routes/broker_sync.py`, `backend/app/schemas/broker_sync_api.py`, `backend/app/services/broker_import/freshness.py`, `backend/tests/api/test_broker_sync_freshness.py`, and `docs/shared/implementation_plan.md`.
  - Added `GET /users/{user_id}/broker-accounts/{broker_account_id}/freshness` for broker portfolio sync freshness only.
  - Response includes broker connection/account status, data freshness, latest sync run metadata, last successful/attempted sync timestamps, and reauth/error flags.
  - Response intentionally uses `freshness_scope="broker_portfolio"` and does not include market quote freshness or quote timestamps.
  - Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/api/test_broker_sync_freshness.py tests/api/test_broker_ownership.py tests/api/test_broker_sync.py tests/api/test_broker_accounts.py` -> `10 passed in 0.44s`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `170 passed, 1 deselected in 1.35s`.
- Status: `done`

### P8-T3 - Stale/Cached/Unknown Data Warnings

- Task id: `P8-T3`
- Title: stale/cached/unknown data warnings
- Objective: Generate backend warning flags when broker data freshness is not fresh.
- Files expected to change:
  - `backend/app/services/portfolio/warnings.py`
  - `backend/app/schemas/portfolio.py`
  - `backend/tests/services/test_portfolio_warnings.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Changed files: `backend/app/schemas/portfolio.py`, `backend/app/services/portfolio/summary.py`, `backend/app/services/portfolio/warnings.py`, `backend/tests/api/test_portfolio.py`, `backend/tests/api/test_portfolio_summary.py`, `backend/tests/services/test_portfolio_summary.py`, `backend/tests/services/test_portfolio_warnings.py`, and `docs/shared/implementation_plan.md`.
  - Added broker portfolio warning objects to portfolio summaries via `broker_data_warnings`.
  - Warning generation covers `cached`, `delayed`, `stale`, `unknown`, `error`, and `reauth_required` broker data freshness statuses.
  - Warning messages explicitly separate broker holdings/cash freshness from market price freshness.
  - Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/test_portfolio_warnings.py tests/services/test_portfolio_summary.py tests/api/test_portfolio.py tests/api/test_portfolio_summary.py` -> `11 passed in 0.23s`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `178 passed, 1 deselected in 1.40s`.
- Status: `done`

### P8-T4 - Dashboard Backend Tests

- Task id: `P8-T4`
- Title: tests
- Objective: Cover portfolio summary and broker freshness behavior from synced data.
- Files expected to change:
  - `backend/tests/api/test_portfolio_dashboard_backend.py`
  - `backend/tests/services/test_portfolio_warnings.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Changed files: `backend/tests/api/test_portfolio_dashboard_backend.py`, `backend/tests/services/test_portfolio_warnings.py`, and `docs/shared/implementation_plan.md`.
  - Added dashboard backend API coverage proving synced SnapTrade-style data can support portfolio summary, broker freshness, and broker-data warnings without any market data provider calls.
  - Verified summary and freshness responses keep broker portfolio freshness separate from market quote freshness by excluding market quote fields.
  - Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/api/test_portfolio_dashboard_backend.py tests/api/test_portfolio_summary.py tests/api/test_broker_sync_freshness.py tests/services/test_portfolio_warnings.py` -> `13 passed in 0.31s`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `179 passed, 1 deselected in 1.50s`.
- Status: `done`

### P8-T5 - Phase 8 Wording, Vocabulary, and Edge-Case Hardening

- Task id: `P8-T5`
- Title: phase 8 wording, vocabulary, and edge-case hardening
- Objective: Tighten Phase 8 dashboard backend before manual fallback work starts in Phase 9 by fixing warning copy that over-promises capability, eliminating freshness vocabulary drift, defining explicit behavior for missing `market_value`, tightening the `has_error` predicate, and adding the missing regression / structural tests.
- Migration impact: no new migrations required.
- Files expected to change:
  - `backend/app/services/portfolio/warnings.py`
  - `backend/app/services/portfolio/summary.py`
  - `backend/app/schemas/portfolio.py`
  - `backend/app/services/broker_import/freshness.py`
  - `backend/app/api/routes/broker_sync.py`
  - `backend/tests/regression/test_portfolio_summary_regressions.py`
  - `backend/tests/api/test_portfolio.py`
  - `backend/tests/api/test_portfolio_summary.py`
  - `backend/tests/api/test_portfolio_dashboard_backend.py`
  - `backend/tests/api/test_broker_sync_freshness.py`
  - `backend/tests/api/test_broker_sync_foundation.py`
  - `backend/tests/api/test_manual_portfolio_summary.py`
  - `backend/tests/services/test_portfolio_summary.py`
  - `backend/tests/services/test_portfolio_warnings.py`
  - `backend/tests/unit/test_broker_sync_statuses.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P8-T4`
- Implementation steps:
  1. (I1) Replace the `market prices may be current while account data is not` clause in `WARNING_DETAILS` with factual, scope-only copy: `Broker portfolio holdings and cash are <state>. Review the latest snapshot timestamp and verify in your broker before manual action.` Apply the same pattern to cached, delayed, stale, error, and reauth-required entries.
  2. (I2) Replace the literal `NON_FRESH_BROKER_STATUSES` set with `set(DATA_FRESHNESS_STATUSES) - {"fresh"}` imported from `app.services.broker_import.statuses`.
  3. (L1) Rename the `broker_reauth_required` warning code to `broker_data_reauth_required` and update tests.
  4. (I3) Add a `broker_data_market_value_missing` warning at severity `warning`. In `summary.py`, after selecting latest stock and option snapshots, detect any latest position with `market_value is None` and emit this warning. Document the response contract on `PortfolioSummaryRead`: market value totals sum latest snapshots that supplied market value; positions without market value still count toward position counts and surface this warning.
  5. (M3) In `freshness.py:get_broker_account_freshness`, compute `has_error` from connection/account error statuses plus `latest_run.status in {"failed", "partially_succeeded"}`. Stop checking `latest_run.error` directly.
  6. (P1/M5) In `broker_sync.py`, drop the unused `exc` parameter from `_provider_unavailable` and keep the HTTP detail generic.
  7. (T1) Add a multi-snapshot regression in `test_portfolio_summary_regressions.py` covering latest `*_as_of` values, latest-only counts, and `latest_snapshot_as_of`.
  8. (T2) Add a `market_value is None` regression in `test_portfolio_summary_regressions.py`.
  9. (T3) Add `test_manual_portfolio_summary.py` for the manual-only path using only existing manual POST endpoints. Do not call SnapTrade registration, broker sync, or `/broker-accounts/{id}/sync`.
  10. (T4) Add latest-success-after-failed-run freshness coverage in `test_broker_sync_freshness.py`.
  11. (T5) Add a structural OpenAPI check for `BrokerSyncFreshnessRead` and `PortfolioSummaryRead` in `test_broker_sync_foundation.py`; use exact snapshot-style allowlists for both response schemas and a precise forbidden-token list for market quote fields. Broker-sync snapshot timestamps such as `last_successful_sync_at` and `last_attempted_sync_at` are allowed; market quote fields are not. Keep the existing secret-field structural test.
  12. (T6) Add freshness vocabulary parity coverage in `test_broker_sync_statuses.py`.
  13. Update existing wording assertions in `test_portfolio.py`, `test_portfolio_summary.py`, `test_portfolio_dashboard_backend.py`, and service-level `test_portfolio_summary.py`; verify no backend test/source text still contains `market prices may be current`.
- Acceptance criteria:
  - No warning `message` in `WARNING_DETAILS` contains `market prices may be current` or any other reference to market prices.
  - `NON_FRESH_BROKER_STATUSES` is derived from `statuses.DATA_FRESHNESS_STATUSES`; `test_broker_sync_statuses.py` confirms parity.
  - `broker_data_reauth_required` is the canonical reauth code; the old `broker_reauth_required` code is no longer emitted or asserted.
  - When any latest stock or option position has `market_value is None`, `broker_data_warnings` contains `broker_data_market_value_missing`; regression coverage confirms this.
  - `has_error` returns false when the latest sync run succeeds after an older failed run; `test_broker_sync_freshness.py` confirms this.
  - `/openapi.json` resolved schemas for `BrokerSyncFreshnessRead` and `PortfolioSummaryRead` match explicit allowlists and contain no market quote fields such as `quote_timestamp`, `market_quote_freshness`, `bid`, `ask`, or provider quote fields. Broker-sync `last_*` timestamps remain allowed.
  - `/accounts/{account_id}/portfolio` works for a manual-only account with no broker connection.
  - Default `pytest` continues to exclude `external` and `slow`.
  - No new migrations.
  - No real SnapTrade calls, no `.env` reads, and no `../TradingAgents` modifications.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd backend && ./.venv/bin/alembic current`
  - `cd backend && ./.venv/bin/alembic upgrade head`
- Rollback notes:
  - Revert warning copy, vocabulary unification, reauth code rename, missing-market-value warning, freshness predicate tightening, route wrapper cleanup, and the new tests.
- Deferrals:
  - Per-source freshness rollups remain deferred.
  - Granularity beyond freshness statuses, such as clearer connection vs. account vs. run freshness fields in the freshness response, remains deferred.
  - Synthesized human age / staleness duration strings remain deferred.
  - Surfacing `summary.warnings` / `summary.partial_failures` counts on the freshness response remains deferred.
  - Hard-coded message string updates in dashboard backend tests are handled inside this task.
- Verification notes:
  - Changed files: `backend/app/api/routes/broker_sync.py`, `backend/app/services/broker_import/freshness.py`, `backend/app/services/portfolio/warnings.py`, `backend/app/services/portfolio/summary.py`, `backend/app/schemas/portfolio.py`, `backend/tests/regression/test_portfolio_summary_regressions.py`, `backend/tests/api/test_broker_sync_freshness.py`, `backend/tests/api/test_broker_sync_foundation.py`, `backend/tests/api/test_manual_portfolio_summary.py`, `backend/tests/api/test_portfolio.py`, `backend/tests/api/test_portfolio_dashboard_backend.py`, `backend/tests/services/test_portfolio_summary.py`, `backend/tests/services/test_portfolio_warnings.py`, `backend/tests/unit/test_broker_sync_statuses.py`, and `docs/shared/implementation_plan.md`.
  - Warning copy evidence: `backend/app/services/portfolio/warnings.py` uses factual broker-snapshot wording; `rg -n "market prices may be current|broker_reauth_required" backend --glob '!backend/.venv/**'` returned no matches.
  - Vocabulary evidence: `backend/tests/unit/test_broker_sync_statuses.py::test_portfolio_warning_freshness_statuses_match_broker_status_catalog` verifies `NON_FRESH_BROKER_STATUSES == set(DATA_FRESHNESS_STATUSES) - {"fresh"}`.
  - Missing market value evidence: `backend/tests/regression/test_portfolio_summary_regressions.py::test_missing_market_values_count_positions_and_emit_warning` verifies positions still count, market values sum to zero, and `broker_data_market_value_missing` is emitted.
  - Freshness predicate evidence: `backend/tests/api/test_broker_sync_freshness.py::test_broker_account_freshness_uses_latest_run_status_for_error_flag` verifies a latest successful sync after an older failed sync reports `has_error is False`.
  - OpenAPI evidence: `backend/tests/api/test_broker_sync_foundation.py::test_openapi_dashboard_schemas_expose_broker_snapshots_not_market_quotes` verifies allowlisted broker freshness / portfolio summary fields and no market quote fields while preserving broker-sync `last_*` timestamps.
  - Manual-only evidence: `backend/tests/api/test_manual_portfolio_summary.py` verifies manual-only portfolio summary works without broker sync, SnapTrade registration, or broker account sync.
  - Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/regression/test_portfolio_summary_regressions.py tests/api/test_manual_portfolio_summary.py tests/api/test_broker_sync_freshness.py tests/api/test_broker_sync_foundation.py tests/services/test_portfolio_warnings.py tests/unit/test_broker_sync_statuses.py tests/api/test_portfolio.py tests/api/test_portfolio_summary.py tests/api/test_portfolio_dashboard_backend.py tests/services/test_portfolio_summary.py` -> `33 passed in 0.75s`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `186 passed, 1 deselected in 1.60s`.
  - Alembic result: `cd backend && ./.venv/bin/alembic current` -> `0011_provider_credentials (head)`.
  - Alembic result: `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
  - Residual risk: per-source freshness rollups, freshness response granularity, human age strings, and sync summary warning counts remain deliberately deferred.
- Status: `done`

## Phase 9 - Manual Input and CSV Fallback

### P9-T1 - Manual Entry Fallback

- Task id: `P9-T1`
- Title: keep manual entry available
- Objective: Preserve manual user/account/cash/position entry as a fallback when SnapTrade is unavailable or intentionally disabled.
- Files expected to change:
  - `backend/app/api/routes/portfolio.py`
  - `backend/tests/api/test_manual_portfolio_entry.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Changed files: `backend/tests/api/test_manual_portfolio_entry.py` and `docs/shared/implementation_plan.md`.
  - `backend/app/api/routes/portfolio.py` was listed as a possible route touchpoint for symmetry with manual entry routes, but the existing route implementation already used the internal storage primitives and required no edits.
  - Verified manual cash, stock, and option entry use the same internal storage and summary path without any broker connection/account rows or provider credentials.
  - Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/api/test_manual_portfolio_entry.py tests/api/test_manual_portfolio_summary.py` -> `2 passed in 0.27s`.
- Status: `done`

### P9-T2 - Fidelity CSV Import Backup

- Task id: `P9-T2`
- Title: simple CSV import backup
- Objective: Add CSV import backup for positions/transactions when API sync is unavailable.
- Files expected to change:
  - `backend/app/services/broker_import/fidelity_csv.py`
  - `backend/app/api/routes/imports.py`
  - `backend/app/main.py`
  - `backend/tests/services/test_fidelity_csv_import.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Changed files: `backend/app/services/broker_import/fidelity_csv.py`, `backend/app/api/routes/imports.py`, `backend/app/main.py`, `backend/tests/services/test_fidelity_csv_import.py`, and `docs/shared/implementation_plan.md`.
  - Added preview-only Fidelity CSV parsing for synthetic positions and transactions CSV content. The route returns parsed rows and validation warnings without storing broker files or credentials.
  - Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/test_fidelity_csv_import.py` -> `4 passed in 0.01s`.
- Status: `done`

### P9-T3 - Synthetic CSV Fixtures

- Task id: `P9-T3`
- Title: synthetic fixtures only
- Objective: Add safe synthetic CSV fixtures and documentation for fallback import tests.
- Files expected to change:
  - `backend/tests/fixtures/fidelity_positions_demo.csv`
  - `backend/tests/fixtures/fidelity_transactions_demo.csv`
  - `backend/tests/README.md`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Changed files: `backend/tests/fixtures/fidelity_positions_demo.csv`, `backend/tests/fixtures/fidelity_transactions_demo.csv`, `backend/tests/README.md`, and `docs/shared/implementation_plan.md`.
  - Added small synthetic CSV samples using demo symbols only and documented that real broker CSVs must never be committed.
  - Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/test_fidelity_csv_import.py` -> `4 passed in 0.01s`.
- Status: `done`

### P9-T4 - Fallback Tests

- Task id: `P9-T4`
- Title: do not block SnapTrade progress
- Objective: Verify manual and CSV fallback paths do not block the SnapTrade-first architecture.
- Files expected to change:
  - `backend/tests/api/test_portfolio_fallbacks.py`
  - `backend/tests/services/test_import_fallbacks.py`
  - `docs/shared/implementation_plan.md`
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
- Verification notes:
  - Changed files: `backend/tests/api/test_portfolio_fallbacks.py`, `backend/tests/services/test_import_fallbacks.py`, and `docs/shared/implementation_plan.md`.
  - Verified manual fallback and CSV preview fallback work without SnapTrade registration, broker sync, provider credentials, scraping, or real broker files.
  - Focused Phase 9 test result: `cd backend && ./.venv/bin/python -m pytest tests/api/test_manual_portfolio_entry.py tests/api/test_manual_portfolio_summary.py tests/services/test_fidelity_csv_import.py tests/api/test_portfolio_fallbacks.py tests/services/test_import_fallbacks.py` -> `10 passed in 0.27s`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `195 passed, 1 deselected in 1.44s`.
  - Alembic result: `cd backend && ./.venv/bin/alembic current` -> `0011_provider_credentials (head)`.
  - Alembic result: `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
- Status: `done`

### P9-T5 - Pre-Phase-10 Fallback and Freshness Hygiene

- Task id: `P9-T5`
- Title: pre-Phase-10 fallback and freshness hygiene
- Objective: Tighten Phase 8/9 backend surfaces before market data work starts by fixing CSV preview ownership, CSV preview limits, warning metadata semantics, freshness error predicates, import schema clarity, synthetic fixture tracking, and fallback edge-case tests.
- Migration impact: no new migrations required.
- Files expected to change:
  - `.gitignore`
  - `backend/app/api/routes/imports.py`
  - `backend/app/services/broker_import/fidelity_csv.py`
  - `backend/app/services/broker_import/freshness.py`
  - `backend/app/services/portfolio/warnings.py`
  - `backend/tests/api/test_broker_sync_foundation.py`
  - `backend/tests/api/test_broker_sync_freshness.py`
  - `backend/tests/api/test_manual_portfolio_summary.py`
  - `backend/tests/api/test_portfolio_fallbacks.py`
  - `backend/tests/api/test_snaptrade_import_smoke.py`
  - `backend/tests/services/test_fidelity_csv_import.py`
  - `backend/tests/services/test_portfolio_warnings.py`
  - `backend/tests/unit/test_broker_sync_statuses.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P9-T4`
- Implementation steps:
  1. (I1, T1) Change CSV preview route to `POST /users/{user_id}/accounts/{account_id}/imports/fidelity-csv/preview` and verify the account exists, is not deleted, and belongs to `user_id`; wrong-user access returns 404.
  2. (I2, T7) Change the missing-market-value warning to `freshness_status="not_applicable"` and add a test that combined unknown freshness plus missing market value emits two warnings: one with `freshness_status="unknown"` and one with `freshness_status="not_applicable"`.
  3. (I3, T5) Add CSV preview size guards with `max_length=1_000_000` and `MAX_PARSE_ROWS = 10_000`. Apply the char-length guard at the request schema (`csv_text: str = Field(min_length=1, max_length=1_000_000)`) so oversize payloads are rejected before any parsing. Apply the row-count guard inside `_parse_rows` after `csv.DictReader` consumes the header but before any per-row decimal parsing. The char guard is the primary defense; the row guard is the backup against pathological huge-cell rows.
  4. (I4) Add a P9-T1 verification note clarifying that `backend/app/api/routes/portfolio.py` was listed as a possible route touchpoint for symmetry but required no edit.
  5. (P1, T4) Simplify `has_error` to use connection/account error statuses plus explicit latest-run `partially_succeeded` handling.
  6. (P2, P3, P8) Preserve the existing substring `MARKET_DATA_FIELD_TOKENS = ("quote", "bid", "ask", "market_quote")` policy for `BrokerSyncFreshnessRead` and `PortfolioSummaryRead`. Apply the same substring check plus an exact-set field allowlist to the new `FidelityCsvPreviewRead` and `FidelityCsvPreviewRowRead` structural tests. The substring policy is broader than the original P8-T5 prefix-only wording on purpose: the exact-set allowlist is the primary safety net, the substring check is defense-in-depth, and broker-sync `last_*` timestamps remain allowed because the exact-set allowlist permits them by name.
  7. (P4) Make `FidelityCsvPreviewRowRead.data` match the wire shape as `dict[str, str]` and convert parsed row values to strings at response construction time.
  8. (T2) Add a manual-only fresh-path portfolio summary test that creates manual cash, stock, and option rows with `source="manual"` and `data_freshness_status="fresh"`, every position supplies `market_value`, and `GET /accounts/{account_id}/portfolio` returns `broker_data_warnings == []` (no freshness warning and no `broker_data_market_value_missing` warning). Place in `backend/tests/api/test_manual_portfolio_summary.py`.
  9. (T3) Add an empty-account portfolio summary test that creates a user + manual `Account` with zero cash, stock, and option rows, then `GET /accounts/{account_id}/portfolio`. Assert: `total_cash == "0"`, `stock_position_count == 0`, `stock_market_value == "0"`, `option_position_count == 0`, `long_option_position_count == 0`, `short_option_position_count == 0`, `option_market_value == "0"`, `total_internal_value == "0"`, `data_sources == []`, `data_freshness_statuses == []`, `broker_data_warnings == []`, `cash_as_of is None`, `stock_positions_as_of is None`, `option_positions_as_of is None`, `latest_snapshot_as_of is None`. Place in `backend/tests/api/test_manual_portfolio_summary.py`.
  10. (T4) Add CSV parser edge-case tests in `backend/tests/services/test_fidelity_csv_import.py` using inline strings for BOM headers, Windows `\r\n` line endings, and duplicate symbols. Duplicate symbols must remain as separate preview rows because preview is a parse layer, not a dedup layer.
  11. (T6) Add `backend/tests/api/test_snaptrade_import_smoke.py` with `pytest.mark.smoke`; import `SnapTradeAdapter`, `refresh_snaptrade_connections`, and `sync_broker_account` without real HTTP or DB writes.
  12. (Missed fixture hygiene) Add a `.gitignore` exception for `backend/tests/fixtures/*.csv` so synthetic CSV fixtures can be committed while general `*.csv` remains ignored.
  13. (I2 boundary) Add a negative assertion in `backend/tests/unit/test_broker_sync_statuses.py` that `not_applicable` is not in `DATA_FRESHNESS_STATUSES`, codifying that the sentinel lives only on warnings.
- Acceptance criteria:
  - CSV preview route is user-scoped and returns 404 for wrong-user account access.
  - CSV preview rejects payloads larger than `1_000_000` characters and CSVs over `10_000` rows.
  - Missing-market-value warning uses `freshness_status="not_applicable"`, and combined unknown freshness plus missing market value emits two distinct warnings.
  - Latest successful sync after an older failed run still reports `has_error is False`.
  - Import preview response schema matches the string-only wire shape.
  - OpenAPI tests cover `BrokerSyncFreshnessRead`, `PortfolioSummaryRead`, `FidelityCsvPreviewRead`, and `FidelityCsvPreviewRowRead`.
  - Manual-only fresh and empty-account portfolio summary contracts are pinned.
  - CSV parser handles BOM, Windows line endings, and preserves duplicate symbol rows.
  - SnapTrade import smoke test proves fallback changes do not break primary sync imports.
  - Synthetic CSV fixtures are no longer ignored, while general `*.csv` remains ignored.
  - `git check-ignore backend/tests/fixtures/fidelity_positions_demo.csv` exits non-zero (the synthetic fixture is no longer ignored). `git check-ignore reports/example.csv` (any other location) still exits zero (general `*.csv` remains ignored).
  - All new test files declare `pytestmark` using markers registered in `pytest.ini` (one or more of `unit`, `api`, `db`, `integration`, `regression`, `adapter`, `smoke`, `external`, `slow`). `test_snaptrade_import_smoke.py` declares at minimum `pytest.mark.smoke`.
  - No migrations, no real SnapTrade calls, no `.env` reads, no `../TradingAgents` modifications.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd backend && ./.venv/bin/alembic current`
  - `cd backend && ./.venv/bin/alembic upgrade head`
  - `cd /Users/wulingyun/Desktop/Trading_Agents_Projects/portfolio-options-agent && git check-ignore backend/tests/fixtures/fidelity_positions_demo.csv; echo $?`
  - `cd /Users/wulingyun/Desktop/Trading_Agents_Projects/portfolio-options-agent && git check-ignore reports/example.csv; echo $?`
- Rollback notes:
  - Revert route path/ownership changes, CSV size/row limits, warning sentinel change, freshness predicate cleanup, OpenAPI/import schema tests, fallback edge-case tests, SnapTrade import smoke test, and `.gitignore` fixture exception.
- Deferrals:
  - P5: project-specific CSV exception base deferred until import error hierarchy grows.
  - P6: accounting-style negative parsing deferred until real CSV import hardening.
  - P7: no action; `is_manual` is flipped to `false` by `backend/app/services/accounts.py:find_or_create_synced_account`, which is called by `backend/app/services/broker_import/refresh_connections.py`.
  - P10 market-data import boundary and `freshness_scope="market_quote"` tests deferred until `P10-T1`.
  - P10 precautions: when P10-T1 starts, the three Phase 8/9 review precautions (no `app.services.market_data.*` imports from `app.services.broker_import.*`, exact-set OpenAPI test for `MarketQuoteFreshnessRead` using `freshness_scope: Literal["market_quote"]`, and a top-of-module docstring citing the Phase 8 broker-vs-quote vocabulary) must be folded into the P10-T1 spec before any code lands. Do not fold them into P9-T5.
- Verification notes:
  - Changed files: `.gitignore`, `backend/app/api/routes/imports.py`, `backend/app/services/broker_import/fidelity_csv.py`, `backend/app/services/broker_import/freshness.py`, `backend/app/services/portfolio/warnings.py`, `backend/tests/api/test_broker_sync_foundation.py`, `backend/tests/api/test_broker_sync_freshness.py`, `backend/tests/api/test_manual_portfolio_summary.py`, `backend/tests/api/test_portfolio_fallbacks.py`, `backend/tests/api/test_snaptrade_import_smoke.py`, `backend/tests/services/test_fidelity_csv_import.py`, `backend/tests/services/test_portfolio_warnings.py`, `backend/tests/unit/test_broker_sync_statuses.py`, and `docs/shared/implementation_plan.md`.
  - CSV ownership evidence: `backend/tests/api/test_portfolio_fallbacks.py::test_csv_preview_fallback_returns_404_for_wrong_user_account_access` verifies the user-scoped route returns 404 for wrong-user account access. The ownership test remains in `backend/tests/api/test_portfolio_fallbacks.py`.
  - CSV size evidence: `backend/tests/api/test_portfolio_fallbacks.py::test_csv_preview_fallback_rejects_oversized_payload_before_parsing` verifies the `1_000_000` character request guard; `backend/tests/services/test_fidelity_csv_import.py::test_preview_fidelity_csv_rejects_more_than_max_preview_rows` verifies the `MAX_PARSE_ROWS = 10_000` parser guard.
  - Warning sentinel evidence: `backend/tests/services/test_portfolio_warnings.py::test_missing_market_value_warning_is_explicit` verifies `freshness_status == "not_applicable"`; `backend/tests/api/test_manual_portfolio_summary.py::test_unknown_freshness_and_missing_market_value_emit_distinct_warning_statuses` verifies the combined unknown freshness plus missing market value case.
  - Freshness predicate evidence: `backend/tests/api/test_broker_sync_freshness.py::test_broker_account_freshness_uses_latest_run_status_for_error_flag` verifies latest success after older failure reports `has_error is False`; `backend/tests/api/test_broker_sync_freshness.py::test_broker_account_freshness_flags_latest_partial_success_as_error` verifies latest partial success reports `has_error is True`.
  - OpenAPI evidence: `backend/tests/api/test_broker_sync_foundation.py::test_openapi_dashboard_schemas_expose_broker_snapshots_not_market_quotes` and `backend/tests/api/test_broker_sync_foundation.py::test_openapi_fidelity_csv_preview_schemas_are_explicit_and_not_market_quotes` verify structural allowlists for broker freshness, portfolio summary, and CSV preview schemas.
  - Manual summary evidence: `backend/tests/api/test_manual_portfolio_summary.py::test_manual_only_fresh_portfolio_summary_has_no_broker_data_warnings` and `backend/tests/api/test_manual_portfolio_summary.py::test_empty_manual_account_portfolio_summary_has_stable_zero_shape` pin the fresh and empty-account contracts.
  - CSV parser evidence: `backend/tests/services/test_fidelity_csv_import.py::test_preview_fidelity_csv_handles_utf8_bom_header`, `test_preview_fidelity_csv_handles_windows_line_endings`, and `test_preview_fidelity_csv_preserves_duplicate_symbol_rows` verify BOM, CRLF, and duplicate-symbol behavior.
  - SnapTrade smoke evidence: `backend/tests/api/test_snaptrade_import_smoke.py::test_snaptrade_primary_sync_modules_import_without_real_provider_calls` verifies primary SnapTrade sync modules import without real provider calls.
  - Boundary evidence: `backend/tests/unit/test_broker_sync_statuses.py::test_warning_only_not_applicable_status_is_not_broker_data_freshness_status` verifies `not_applicable` remains warning-only and is not a broker freshness status.
  - P9-T1 drift note: `backend/app/api/routes/portfolio.py` was listed in P9-T1 as a possible route touchpoint but required no edits because existing manual routes already used internal storage primitives.
  - P7 deferral citation: `backend/app/services/accounts.py:find_or_create_synced_account` flips `is_manual` to `false`, and `backend/app/services/broker_import/refresh_connections.py` calls that helper during broker account ingestion.
  - Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/api/test_portfolio_fallbacks.py tests/api/test_manual_portfolio_summary.py tests/services/test_fidelity_csv_import.py tests/services/test_portfolio_warnings.py tests/api/test_broker_sync_foundation.py tests/api/test_broker_sync_freshness.py tests/unit/test_broker_sync_statuses.py tests/api/test_snaptrade_import_smoke.py` -> `43 passed in 0.58s`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `208 passed, 1 deselected in 1.60s`.
  - Alembic result: `cd backend && ./.venv/bin/alembic current` -> `0011_provider_credentials (head)`.
  - Alembic result: `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
  - Gitignore result: `git check-ignore backend/tests/fixtures/fidelity_positions_demo.csv; echo $?` -> `1`.
  - Gitignore result: `git check-ignore reports/example.csv; echo $?` -> `reports/example.csv` and `0`.
  - Diff hygiene result: `git diff --check` completed with no output.
  - Residual risk: project-specific CSV exception hierarchy, accounting-style negative parsing, and Phase 10 market-data boundary tests remain deliberately deferred.
- Status: `done`

## Phase 10 - Thin Agent/Report Foundation

Phase goal: create durable report and agent history before TradingAgents integration, LLM calls, market data providers, or frontend agent work. This phase is intentionally thin: deterministic/template markdown only, synthetic tests only, and no external calls.

### P10-T1 - report_threads table

- Task id: `P10-T1`
- Title: report_threads table
- Objective: Add the top-level report thread record used by report history and future agent workspaces.
- Files expected to change:
  - `backend/app/models/report_thread.py`
  - `backend/app/models/__init__.py`
  - `backend/alembic/versions/*`
  - `backend/tests/db/test_report_threads.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P9-T5`
- Implementation steps:
  1. Add `report_threads` with user/account/report metadata, status, title, timestamps, and `deleted_at`.
  2. Treat `deleted_at` as a minimal soft-delete placeholder only.
  3. Do not implement restore or permanent-delete behavior in this task.
- Acceptance criteria:
  - `report_threads.deleted_at` exists and defaults to `NULL`.
  - A report thread can be created and queried in synthetic tests.
  - No LLM calls, TradingAgents calls, external APIs, or frontend code.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd backend && ./.venv/bin/alembic current`
  - `cd backend && ./.venv/bin/alembic upgrade head`
- Rollback notes:
  - Revert the model, migration, tests, and plan notes.
- Verification notes:
  - Implemented `ReportThread` SQLAlchemy model with user ownership, optional account link, title, report type, status, timestamps, and `deleted_at` soft-delete placeholder.
  - Added Alembic migration `0012_create_report_threads` with indexes for account lookup, deleted state, user/status, and user/created ordering.
  - Registered `ReportThread` in model metadata and added test cleanup ordering in `backend/tests/conftest.py`.
  - Added synthetic DB tests confirming create/query behavior, default `report_type="portfolio_report"`, default `status="draft"`, nullable `account_id`, timestamps, and `deleted_at is None`.
  - Changed files: `backend/app/models/report_thread.py`, `backend/app/models/__init__.py`, `backend/alembic/versions/0012_create_report_threads.py`, `backend/tests/conftest.py`, `backend/tests/db/test_report_threads.py`, and `docs/shared/implementation_plan.md`.
  - Migration prep result: `cd backend && ./.venv/bin/alembic upgrade head` -> upgraded `0011_provider_credentials` to `0012_create_report_threads`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `210 passed, 1 deselected in 2.71s`.
  - Alembic result: `cd backend && ./.venv/bin/alembic current` -> `0012_create_report_threads (head)`.
  - Alembic result: `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
  - Diff hygiene result: `git diff --check` completed with no output.
  - Residual risk: full report restore/permanent delete behavior is intentionally deferred; this task only adds the `deleted_at` placeholder.
- Status: `done`

### P10-T2 - report_messages table

- Task id: `P10-T2`
- Title: report_messages table
- Objective: Store durable AI-style report history messages without requiring any LLM integration.
- Files expected to change:
  - `backend/app/models/report_message.py`
  - `backend/app/models/__init__.py`
  - `backend/alembic/versions/*`
  - `backend/tests/db/test_report_messages.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P10-T1`
- Implementation steps:
  1. Add `report_messages` linked to `report_threads`.
  2. Support message types such as `user_input`, `system_event`, `agent_output`, `tool_output`, `error`, `retry_notice`, `final_report`, and `markdown_report`.
  3. Store markdown/text content and safe structured metadata only.
- Acceptance criteria:
  - Messages belong to a report thread.
  - Message ordering is deterministic.
  - Synthetic tests cover create/read behavior.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd backend && ./.venv/bin/alembic current`
  - `cd backend && ./.venv/bin/alembic upgrade head`
- Rollback notes:
  - Revert the model, migration, tests, and plan notes.
- Verification notes:
  - Implemented `ReportMessage` SQLAlchemy model linked to `ReportThread` with sender type, message type, markdown content, JSON content, deterministic sequence, visibility, timestamps, and `deleted_at` soft-delete placeholder.
  - Added Alembic migration `0013_create_report_messages` with `thread_id` foreign key, unique `(thread_id, sequence)` ordering constraint, and indexes for thread lookup, message type, and deleted state.
  - Registered `ReportMessage` in model metadata and added test cleanup ordering in `backend/tests/conftest.py`.
  - Added synthetic DB tests confirming thread ownership, deterministic sequence ordering, supported message types such as `user_input` and `markdown_report`, JSON content persistence, default `visibility="private"`, timestamps, and `deleted_at is None`.
  - Changed files: `backend/app/models/report_message.py`, `backend/app/models/__init__.py`, `backend/alembic/versions/0013_create_report_messages.py`, `backend/tests/conftest.py`, `backend/tests/db/test_report_messages.py`, and `docs/shared/implementation_plan.md`.
  - Migration prep result: `cd backend && ./.venv/bin/alembic upgrade head` -> upgraded `0012_create_report_threads` to `0013_create_report_messages`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `212 passed, 1 deselected in 2.39s`.
  - Alembic result: `cd backend && ./.venv/bin/alembic current` -> `0013_create_report_messages (head)`.
  - Alembic result: `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
  - Diff hygiene result: `git diff --check` completed with no output.
  - Residual risk: report APIs and message schemas are intentionally deferred to later Phase 10 tasks; this task only adds the persistence primitive.
- Status: `done`

### P10-T3 - agent_runs table

- Task id: `P10-T3`
- Title: agent_runs table
- Objective: Track each deterministic or future LLM-assisted analysis run with input/output traceability.
- Files expected to change:
  - `backend/app/models/agent_run.py`
  - `backend/app/models/__init__.py`
  - `backend/alembic/versions/*`
  - `backend/tests/db/test_agent_runs.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P10-T2`
- Implementation steps:
  1. Add `agent_runs` linked to user, optional account, and optional report thread.
  2. Include `input_snapshot_json`, `output_snapshot_json`, `calculation_version`, and `data_freshness_snapshot`.
  3. Include status fields for `queued`, `running`, `waiting_retry`, `failed`, `cancelled`, `completed`, and `partially_completed`.
  4. Do not add LLM provider calls or TradingAgents imports.
- Acceptance criteria:
  - Runs preserve input/output snapshots and freshness context.
  - A run can be created and linked to a report thread.
  - Tests use synthetic snapshots only.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd backend && ./.venv/bin/alembic current`
  - `cd backend && ./.venv/bin/alembic upgrade head`
- Rollback notes:
  - Revert the model, migration, tests, and plan notes.
- Verification notes:
  - Implemented `AgentRun` SQLAlchemy model linked to user, optional account, and optional report thread.
  - Added traceability fields `input_snapshot_json`, `output_snapshot_json`, `calculation_version`, and `data_freshness_snapshot`, plus run type, status, provider/model placeholders, token/cost budgets, run timestamps, error JSON, and timestamps.
  - Added Alembic migration `0014_create_agent_runs` with nullable account/report-thread foreign keys, user foreign key, JSONB snapshot fields, and indexes for status, user/account, report thread, and user/created ordering.
  - Registered `AgentRun` in model metadata and added test cleanup ordering in `backend/tests/conftest.py`.
  - Added synthetic DB tests confirming report-thread linkage, account linkage, snapshot persistence, calculation version persistence, freshness snapshot persistence, default `run_type="portfolio_analysis"`, and default `status="queued"`.
  - Changed files: `backend/app/models/agent_run.py`, `backend/app/models/__init__.py`, `backend/alembic/versions/0014_create_agent_runs.py`, `backend/tests/conftest.py`, `backend/tests/db/test_agent_runs.py`, and `docs/shared/implementation_plan.md`.
  - Migration prep result: `cd backend && ./.venv/bin/alembic upgrade head` -> upgraded `0013_create_report_messages` to `0014_create_agent_runs`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `214 passed, 1 deselected in 2.05s`.
  - Alembic result: `cd backend && ./.venv/bin/alembic current` -> `0014_create_agent_runs (head)`.
  - Alembic result: `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
  - Diff hygiene result: `git diff --check` completed with no output.
  - Residual risk: agent step persistence, schemas, services, APIs, and any LLM/TradingAgents execution remain intentionally deferred to later Phase 10 tasks.
- Status: `done`

### P10-T4 - agent_steps table

- Task id: `P10-T4`
- Title: agent_steps table
- Objective: Store checkpointable step-level traces for custom agents and future TradingAgents output mapping.
- Files expected to change:
  - `backend/app/models/agent_step.py`
  - `backend/app/models/__init__.py`
  - `backend/alembic/versions/*`
  - `backend/tests/db/test_agent_steps.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P10-T3`
- Implementation steps:
  1. Add `agent_steps` linked to `agent_runs`.
  2. Include step ordering, key/type/status, `input_snapshot_json`, `output_snapshot_json`, `calculation_version`, and `data_freshness_snapshot`.
  3. Add token/cost fields as nullable placeholders for future LLM work.
  4. Do not add LLM calls or TradingAgents imports.
- Acceptance criteria:
  - Steps are ordered within a run.
  - Steps can store deterministic inputs and outputs.
  - Tests verify traceability fields.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd backend && ./.venv/bin/alembic current`
  - `cd backend && ./.venv/bin/alembic upgrade head`
- Rollback notes:
  - Revert the model, migration, tests, and plan notes.
- Verification notes:
  - Implemented `AgentStep` SQLAlchemy model linked to `AgentRun`.
  - Added ordered step fields `step_order`, `step_key`, `step_type`, and `status`, plus `input_snapshot_json`, `output_snapshot_json`, `calculation_version`, and `data_freshness_snapshot`.
  - Added nullable future LLM/cost placeholders `tokens_in`, `tokens_out`, and `estimated_cost`, without adding any LLM provider calls.
  - Added Alembic migration `0015_create_agent_steps` with unique `(agent_run_id, step_order)` and indexes for run lookup, run/status, and step key.
  - Added synthetic DB tests confirming step ordering, traceability fields, defaults, and cost placeholders.
  - Verification shared with P10-T8: `cd backend && ./.venv/bin/python -m pytest` -> `228 passed, 1 deselected in 2.53s`; Alembic current -> `0015_create_agent_steps (head)`; Alembic upgrade head completed successfully; `git diff --check` completed with no output.
- Status: `done`

### P10-T5 - report and agent schemas

- Task id: `P10-T5`
- Title: report and agent schemas
- Objective: Add Pydantic contracts for report threads, report messages, agent runs, and agent steps.
- Files expected to change:
  - `backend/app/schemas/reports.py`
  - `backend/app/schemas/agent_runs.py`
  - `backend/tests/unit/test_report_agent_schemas.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P10-T4`
- Implementation steps:
  1. Add create/read schemas for report threads and messages.
  2. Add create/read schemas for agent runs and steps.
  3. Keep schemas free of real account data, API keys, and provider secrets.
- Acceptance criteria:
  - Schemas expose snapshot fields and `deleted_at` where appropriate.
  - Schemas do not expose secret fields.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Revert schema and tests.
- Verification notes:
  - Added `backend/app/schemas/reports.py` with create/read/detail schemas for report threads and report messages.
  - Added `backend/app/schemas/agent_runs.py` with create/read schemas for agent runs and agent steps.
  - Schemas expose snapshot/version/freshness fields and `deleted_at` where appropriate.
  - Added unit tests confirming report schemas, agent traceability schemas, completion-time validation, and absence of secret fields such as `secret_ref`, `encrypted_secret_ref`, `api_key`, and `access_token`.
  - Verification shared with P10-T8: `cd backend && ./.venv/bin/python -m pytest` -> `228 passed, 1 deselected in 2.53s`; `git diff --check` completed with no output.
- Status: `done`

### P10-T6 - report APIs: list, create, detail

- Task id: `P10-T6`
- Title: report APIs
- Objective: Add minimal backend routes for report history placeholders before frontend work.
- Files expected to change:
  - `backend/app/api/routes/reports.py`
  - `backend/app/main.py`
  - `backend/app/services/reports/*`
  - `backend/tests/api/test_reports.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P10-T5`
- Implementation steps:
  1. Add routes to create a report thread, list report threads, and fetch report detail.
  2. Return report messages with the detail response.
  3. Do not implement restore or permanent delete.
- Acceptance criteria:
  - Report APIs work with synthetic data.
  - List/detail routes support future frontend report history placeholders.
  - No LLM calls, TradingAgents calls, or external APIs.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Revert report routes, services, tests, and route registration.
- Verification notes:
  - Added `backend/app/services/reports/crud.py` for report-thread create/list/detail helpers, message listing, next-sequence calculation, and message persistence.
  - Added `backend/app/api/routes/reports.py` with `POST /users/{user_id}/reports`, `GET /users/{user_id}/reports`, and `GET /users/{user_id}/reports/{thread_id}`.
  - Registered report routes in `backend/app/main.py`.
  - Added API tests confirming create/list/detail behavior, message inclusion in detail responses, missing-user 404s, account ownership checks, and wrong-user 404s.
  - No restore or permanent-delete behavior was added.
  - Verification shared with P10-T8: `cd backend && ./.venv/bin/python -m pytest` -> `228 passed, 1 deselected in 2.53s`; `git diff --check` completed with no output.
- Status: `done`

### P10-T7 - basic markdown report output

- Task id: `P10-T7`
- Title: basic markdown report output
- Objective: Produce deterministic/template markdown reports from existing structured portfolio data.
- Files expected to change:
  - `backend/app/services/reports/markdown.py`
  - `backend/tests/services/test_markdown_reports.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P10-T6`
- Implementation steps:
  1. Add a deterministic markdown renderer for portfolio summary and broker freshness context.
  2. Persist the output as a `markdown_report` or `final_report` message.
  3. Do not call LLMs, TradingAgents, market data APIs, or broker APIs.
- Acceptance criteria:
  - Markdown report output is generated from synthetic structured inputs.
  - Output distinguishes deterministic values from future narrative text.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Revert markdown report service and tests.
- Verification notes:
  - Added `backend/app/services/reports/markdown.py` with deterministic/template markdown rendering for structured portfolio summary and broker freshness inputs.
  - Added persistence helper that stores the rendered output as a `markdown_report` report message with `content_json.generator="deterministic_template"`.
  - Markdown copy explicitly states that it does not include LLM output, TradingAgents research, market data API calls, or trade execution.
  - Added service tests confirming deterministic output content, safety boundary language, and persisted markdown report message shape.
  - Verification shared with P10-T8: `cd backend && ./.venv/bin/python -m pytest` -> `228 passed, 1 deselected in 2.53s`; `git diff --check` completed with no output.
- Status: `done`

### P10-T8 - tests

- Task id: `P10-T8`
- Title: tests
- Objective: Complete Phase 10 coverage for report/agent persistence and deterministic markdown output.
- Files expected to change:
  - `backend/tests/api/test_reports.py`
  - `backend/tests/db/test_report_threads.py`
  - `backend/tests/db/test_report_messages.py`
  - `backend/tests/db/test_agent_runs.py`
  - `backend/tests/db/test_agent_steps.py`
  - `backend/tests/services/test_markdown_reports.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P10-T7`
- Implementation steps:
  1. Add API, DB, and service tests for the complete thin report/agent foundation.
  2. Confirm default tests use synthetic data only.
  3. Confirm no LLM, TradingAgents, market data, or external broker calls occur.
- Acceptance criteria:
  - Phase 10 is covered by deterministic tests.
  - Default pytest still excludes `external` and `slow`.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd backend && ./.venv/bin/alembic current`
  - `cd backend && ./.venv/bin/alembic upgrade head`
- Rollback notes:
  - Revert added tests and any related plan notes.
- Verification notes:
  - Completed Phase 10 coverage across DB, schema, API, and markdown service layers.
  - Added/updated tests: `backend/tests/db/test_report_threads.py`, `backend/tests/db/test_report_messages.py`, `backend/tests/db/test_agent_runs.py`, `backend/tests/db/test_agent_steps.py`, `backend/tests/unit/test_report_agent_schemas.py`, `backend/tests/api/test_reports.py`, and `backend/tests/services/test_markdown_reports.py`.
  - Confirmed default pytest excludes `external` and `slow`: `pytest.ini` still uses `addopts = -ra -m "not external and not slow"` and the full run reported `1 deselected`.
  - Full test result: `cd backend && ./.venv/bin/python -m pytest` -> `228 passed, 1 deselected in 2.53s`.
  - Alembic result: `cd backend && ./.venv/bin/alembic current` -> `0015_create_agent_steps (head)`.
  - Alembic result: `cd backend && ./.venv/bin/alembic upgrade head` completed successfully.
  - Diff hygiene result: `git diff --check` completed with no output.
  - No LLM calls, TradingAgents calls, market data API calls, broker API calls, frontend code, or external services were added.
- Status: `done`

## Phase 11 - Frontend Dashboard Shell A

Phase goal: implement the first React/Vite dashboard cockpit on top of existing backend data. Intentionally thin — no market quote UI beyond a "not available yet" placeholder.

### Task summary

| Task   | Title                              | Status |
|--------|------------------------------------|--------|
| P11-T1 | React/Vite dashboard shell         | done   |
| P11-T2 | User/account selector              | done   |
| P11-T3 | Portfolio summary view             | done   |
| P11-T4 | Cash/stock/option positions views  | done   |
| P11-T5 | Broker freshness and warnings panel| done   |
| P11-T6 | Report history placeholder         | done   |

### Key files created/changed

- `frontend/package.json`, `vite.config.ts`, `tsconfig.json`, `tsconfig.node.json`, `.eslintrc.cjs`, `index.html`
- `frontend/src/main.tsx`, `frontend/src/App.tsx`
- `frontend/src/styles/globals.css` — design tokens (dark cockpit palette)
- `frontend/src/components/layout/AppShell.tsx`, `TopBar.tsx`, `Sidebar.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/types/api.ts` — TypeScript types mirroring backend Pydantic schemas
- `frontend/src/api/client.ts`, `users.ts`, `accounts.ts`, `portfolio.ts`, `reports.ts`
- `frontend/src/hooks/useUsers.ts`, `useAccounts.ts`, `usePortfolioSummary.ts`, `usePositions.ts`, `useReports.ts`
- `frontend/src/context/AccountContext.tsx` (provider), `context/useAccountContext.ts` (hook — split for react-refresh compatibility)
- `frontend/src/components/account/AccountSelector.tsx`
- `frontend/src/components/portfolio/PortfolioSummaryCard.tsx`
- `frontend/src/components/positions/PositionsTabs.tsx`, `CashPositionsView.tsx`, `StockPositionsView.tsx`, `OptionPositionsView.tsx`
- `frontend/src/components/freshness/BrokerFreshnessBar.tsx`, `PortfolioWarningsPanel.tsx`
- `frontend/src/components/reports/ReportHistoryPlaceholder.tsx`
- `frontend/src/components/shared/StateViews.tsx`, `Timestamp.tsx`, `SectionCard.tsx`
- `frontend/README.md`

### Acceptance criteria met

- Dashboard shell starts at `http://localhost:5173` without production auth.
- User/account selector (in-memory state only, no localStorage).
- Portfolio summary fetches `GET /accounts/{id}/portfolio`, labels values as book value not market price.
- Cash/stock/option positions: each view has loading/error/empty states. Null market_value shown as "○ n/a" not zero.
- Broker freshness bar: 4 distinct states (synced/stale/unknown/error/reauth), icon+text+color (not color-only). Labeled "BROKER SYNC · broker data only · market prices separate".
- Portfolio warnings panel: surfaces broker_data_warnings. Hidden when list is empty.
- Report history placeholder: wired to `GET /users/{id}/reports`. Empty state explains future agentic reports.
- Freshness chip label: `fresh` state shows "Synced" (not "Live") — broker snapshot only, not real-time.
- No market quote UI, option screener, TradingAgents UI, or trade execution controls.
- No API keys, broker credentials, localStorage/sessionStorage for sensitive data.
- `react-refresh/only-export-components` lint warning resolved by splitting `useAccountContext` into its own file.

### Verification notes

- P11-T1: TypeScript strict mode in `tsconfig.json`. Vite proxy to `http://localhost:8000`. Security grep: no API keys, broker URLs, localStorage, or guaranteed-return language.
- P11-T2: `AccountContext` uses in-memory state. "dev" badge labels selector as local MVP mode.
- P11-T3: `PortfolioSummaryCard` fetches portfolio summary. Values labeled "book value · not market price". Per-field timestamps shown.
- P11-T4: `PositionsTabs` tab switcher. `market_value = null` → "○ n/a". Footnotes: "no trades are placed", "market prices not available".
- P11-T5: `BrokerFreshnessBar` always visible when account selected. `PortfolioWarningsPanel` invisible when clean.
- P11-T6: Thread list sorted newest-first. "agentic copilot" badge. No message viewer or agent controls.
- Phase 11 fixups: unused `Timestamp` import removed from `OptionPositionsView.tsx`. Hook split (`useAccountContext`) resolves lint warning. "Live" → "Synced" rename across all four freshness chips. `frontend/README.md` phase table updated to all ✓ done.
- `GET /option-contracts/{id}` backend gap noted in `docs/shared/deferred_items.md` (contract columns fall back to "—" silently if route is missing).

### P11-T7 - Broker Connection UI (incremental extension)

Files created:
- `frontend/src/pages/BrokerConnectionPage.tsx` — `/broker` route; page header, safety panel, no-user guard, connection list, market quote notice
- `frontend/src/components/broker/SafetyNoticePanel.tsx` — always-visible amber panel with all 4 required safety messages
- `frontend/src/components/broker/ConnectFlowPanel.tsx` — register → portal URL → await user → refresh-connections flow
- `frontend/src/components/broker/BrokerConnectionList.tsx` — one card per `BrokerConnectionPublicRead` with status chips and account rows
- `frontend/src/components/broker/BrokerAccountRow.tsx` — per-account sync trigger, polling via `SyncRunStatus`, "View Portfolio" nav
- `frontend/src/components/broker/SyncRunStatus.tsx` — polls `GET /broker-sync-runs/{id}` every 2.5 s; stops at terminal state; shows summary
- `frontend/src/api/brokerSync.ts` — all 8 broker sync API methods
- `frontend/src/hooks/useBrokerConnections.ts` — fetches connections + accounts in parallel; exposes `reload()`
- `frontend/src/context/accountContextDef.ts` — context object + `AccountContextValue` type (three-file split for react-refresh compatibility)

Files changed:
- `frontend/src/App.tsx` — BrowserRouter + Routes (`/` and `/broker`)
- `frontend/src/components/layout/Sidebar.tsx` — NavLink-based navigation; Broker entry at `/broker`
- `frontend/src/types/api.ts` — added 10 broker sync types
- `frontend/src/api/client.ts` — `post()` body made optional (`body?: unknown`)
- `frontend/src/context/AccountContext.tsx` — now exports only `AccountProvider` (component); imports context from `accountContextDef.ts`
- `frontend/src/context/useAccountContext.ts` — imports from `accountContextDef.ts` (not `AccountContext.tsx`)
- `frontend/package.json` — added `react-router-dom`

Safety boundary verification:
- No API keys, broker credentials, or secrets in any frontend file.
- No `localStorage`/`sessionStorage` for sensitive data.
- Portal URL rendered as `<a target="_blank" rel="noopener noreferrer">` — never in an iframe.
- Safety notice panel is non-dismissible; visible on every state of the page.
- No trade-execution controls, order tickets, or guaranteed-return language.
- All network calls route through `/api` proxy → FastAPI backend.

Build verification:
- `npm run typecheck` → 0 errors
- `npm run lint` → 0 warnings (0 problems)
- `npm run build` → 71 modules, built successfully

Backend gaps (for Codex):
- `GET /option-contracts/{id}` — OptionPositionsView lazy-fetches contract details; not confirmed to exist. Noted in `docs/shared/deferred_items.md`.
- `POST /broker-accounts/{id}/sync` 409 conflict response shape: `{ sync_run_id, status }`. Frontend handles this; Codex should verify the JSON body matches `broker_sync.py:158–162`.

- Status: `done`


## Archived From Implementation Plan on 2026-05-20

This section preserves the completed Phase 11 follow-up task and completed Phases 12-15 that were moved out of `docs/shared/implementation_plan.md` so the active plan can stay focused on current and future work.

## Phase 11 Follow-Up - Frontend Dashboard Shell A

Status: P11-T1 through P11-T7 `done` and verified (history in `docs/shared/completed_phases_log.md`).
P11-T8 (pre-push security hardening) `done`.

Scope delivered: React/Vite shell, user/account selector, portfolio summary,
cash/stock/option positions views, broker freshness bar and warnings panel,
report history placeholder, broker connection UI at `/broker` (P11-T7, read-only SnapTrade flow).

Out of scope (deferred): market quote UI, option screener, TradingAgents UI, trade execution UI.

### P11-T8 - Pre-Push SnapTrade Local Security Hardening

- Task id: `P11-T8`
- Title: Pre-Push SnapTrade Local Security Hardening
- Status: `done`
- Objective: Make the local read-only SnapTrade/Fidelity integration safe to commit and push:
  no unauthenticated real-data exposure, no provider identifiers/payloads/secrets reaching the
  frontend or logs, no destructive tooling in the runtime image, standards-based secret encryption.
- Dependencies: P11-T7 (done). No new SnapTrade calls to implement or test.
- Migration impact: Slice E (AEAD secret envelope) changes stored-secret format and requires
  migration `0016_expand_encrypted_secret_ref` because the Fernet envelope exceeds the old
  `String(255)` column. Existing local secret becomes undecryptable → one-time local
  re-register via the normal flow. No production data exists.
- Files expected to change: `docker-compose.yml`; new `.dockerignore` ×3; `frontend/.gitignore`;
  `backend/scripts/manual/delete_snaptrade_user.py`; `backend/app/api/routes/*.py` + new
  `backend/app/core/access_guard.py`; `backend/app/services/broker_import/secrets.py`;
  `backend/app/services/broker_import/providers/snaptrade_sdk_client.py`;
  `backend/app/services/broker_import/snaptrade_connection.py`;
  `backend/alembic/versions/0016_expand_encrypted_secret_ref.py`;
  `backend/app/schemas/broker_sync_api.py`; `backend/app/schemas/broker_account.py`;
  `frontend/src/components/broker/*`; `frontend/src/types/api.ts`; `frontend/src/api/brokerSync.ts`;
  `docs/shared/implementation_plan.md`; `frontend/README.md`; new synthetic tests.
- Implementation steps (ordered slices, lowest blast radius first):
  - Slice A: loopback Docker ports; `.dockerignore` ×3; `frontend/.gitignore`; sanitize + isolate manual script.
  - Slice B: strip `snaptrade_user_id` / `provider_account_id` / raw payloads from public schemas + FE types.
  - Slice C: sanitize SnapTrade SDK exceptions; UI message allowlist.
  - Slice D: local-dev access guard on all real-data routes.
  - Slice E: replace custom crypto with vetted AEAD; versioned envelope.
  - Slice F: decouple app-UUID from SnapTrade userId; read-only portal test; FE terminal-status fix.
- Acceptance criteria: published ports bound to 127.0.0.1; real-data routes require local token;
  no API response carries provider identifiers/payloads; SDK errors yield generic messages
  (no `str(exc)`); secret encryption uses a vetted library; app-user UUID ≠ SnapTrade userId;
  portal always `connection_type="read"` (tested); FE treats `succeeded`/`partially_succeeded`/
  `failed`/`cancelled` as terminal and stops polling; manual script prints no provider IDs/raw exc
  and is excluded from the backend image; no real brokerage values anywhere in repo.
- Tests to run: `cd backend && pytest` (synthetic/mocked only); `cd frontend && npm run typecheck
  && npm run lint && npm run build`; `docker compose config`.
- Rollback notes: all changes are local source/config; revert via git. Slice E: if a stored secret
  cannot decrypt, re-run the normal register flow locally (no prod data; no data loss). No Alembic
  rollback unless the envelope exceeds 255 chars (then revert that migration too).
- Deferrals: UI error allowlist polish (M3), freshness vocabulary cosmetics (L1),
  compose `--reload` review (L2), real multi-user authn/z (out of scope — this is
  a local-dev gate only).
- Verification notes (2026-05-16):
  - Implemented Slice B: public broker schemas and frontend types no longer expose
    `snaptrade_user_id`, `provider_account_id`, `provider_request_id`, raw payloads, or raw metadata.
  - Implemented Slice C: SnapTrade SDK exception wrappers return generic provider-operation
    messages and do not echo raw upstream exception text.
  - Implemented Slice D: all application API routers except `/health`/OpenAPI require
    `X-Local-Access-Token`; Vite proxy injects the header server-side from
    `LOCAL_DEV_ACCESS_TOKEN`.
  - Implemented Slice E: `encrypted_secret_ref` now stores a versioned `Fernet` envelope
    using `cryptography`; no plaintext fallback key remains.
  - Implemented Slice F: registration uses an opaque `poa_*` SnapTrade user ref instead of the
    local app user UUID; SnapTrade user id + user secret are stored inside the encrypted envelope;
    connection portal requests remain `connection_type="read"` with test coverage; frontend sync
    polling treats `succeeded`, `partially_succeeded`, `failed`, and `cancelled` as terminal.
  - Additional safety fix: SnapTrade SDK account mapping no longer falls back to provider account
    number for `display_name`.
  - Added migration `0016_expand_encrypted_secret_ref` so Fernet envelopes fit in
    `provider_credentials_metadata.encrypted_secret_ref`.
  - Fixed broker freshness latest-run ordering to use `coalesce(completed_at, created_at)`.
  - Backend tests ran against an isolated synthetic database `portfolio_options_agent_test`
    using synthetic credentials, not the real local app database:
    `233 passed, 1 deselected in 5.26s`.
  - Frontend verification: `npm run typecheck`, `npm run lint`, and `npm run build` all passed.
  - Alembic verification on the isolated synthetic database:
    `alembic upgrade head` passed and `alembic current` returned
    `0016_expand_encrypted_secret_ref (head)`.
  - `git diff --check` passed.
  - Docker Compose verification note: `docker compose config` was intentionally not printed
    because it can expand environment values. Runtime checks used `docker compose ps`, loopback
    port bindings in `docker-compose.yml`, and isolated synthetic DB verification instead.

## Phase 12 - Market Data Contracts, Snapshots, and Manual Provider

Phase goal: define generic market data contracts for stock and option quotes, option-chain snapshots, provider capabilities, quote freshness, and actionability. This phase must remain strategy-agnostic: it supports future CSP, covered-call, hedge, collar, spread, and long-option workflows, but it must not hardcode wheel strategy assumptions. It includes a narrow frontend companion slice after backend contracts are stable; it does not add real provider integrations or option-chain browsing.

### P12-T1 - Market Data Domain Models

- Task id: `P12-T1`
- Title: Market Data Domain Models
- Objective: Define strategy-agnostic market data domain models for stock quotes, option contract identity, option quote snapshots, option chain snapshots, provider capabilities, quote request context, data mode, freshness, and actionability.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/models.py`
  - `backend/tests/services/market_data/test_domain_models.py`
  - `docs/codex-b-architecture/architecture.md`
  - `docs/shared/current_roadmap.md`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P11-T8`
- Implementation steps:
  1. Add top-of-module documentation explaining broker-vs-quote freshness separation.
  2. Define `DataMode`, `FreshnessStatus`, `ActionabilityStatus`, and `ContractSupportStatus` values.
  3. Define immutable dataclasses for `StockQuoteSnapshot`, `UnderlyingQuoteSnapshot`, `OptionContractIdentity`, `OptionQuoteSnapshot`, `OptionChainSnapshot`, `ProviderCapabilities`, and `QuoteRequestContext`.
  4. Make option identity explicit: OCC symbol when available, normalized identity of underlying + expiration + strike + call/put + multiplier, and provider symbol/contract id as provider-specific metadata.
  5. Include support flags for adjusted contracts, mini options, index options, weeklies, and unsupported/manual-review contracts.
  6. Do not add provider adapters, database tables, formulas, strategy evaluators, or frontend code.
- Acceptance criteria:
  - Market data models are separate from broker sync models and import no broker sync modules.
  - Option quote and chain snapshots are immutable domain objects suitable for later report reproducibility.
  - Market data models contain no CSP, covered-call, wheel, or personal-threshold assumptions.
  - No real provider calls, API keys, migrations, or external services are introduced.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_domain_models.py`
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove market data domain models and tests.
- Verification notes:
  - Refined the roadmap so Phase 12 is strategy-agnostic market data contracts, Phase 13 is generic options/risk services, and wheel-specific CSP/covered-call evaluators move to the new Phase 14 strategy evaluator framework.
  - Added `backend/app/services/market_data/models.py` with immutable domain models for stock quotes, underlying quotes, option contract identity, option quote snapshots, option chain snapshots, provider capabilities, and quote request context.
  - Added `backend/app/services/market_data/__init__.py` exports and top-level documentation for broker-vs-market freshness separation.
  - Added `backend/tests/services/market_data/test_domain_models.py` covering vocabulary, option identity, manual-review flags, quote freshness scope, chain validation, provider capabilities, request context normalization, and invalid-value rejection.
  - Verified no `broker_import`, CSP, covered-call, wheel, personal threshold, SnapTrade, or Fidelity coupling exists in `backend/app/services/market_data` or its tests.
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_domain_models.py` -> `8 passed in 0.03s`.
  - `cd backend && ./.venv/bin/python -m pytest` -> `166 passed, 92 skipped, 1 deselected in 0.45s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - `git diff --check` passed.
  - No migrations, real provider calls, API keys, external services, frontend code, or TradingAgents changes were introduced.
- Status: `done`

### P12-T2 - Provider Interfaces

- Task id: `P12-T2`
- Title: Provider Interfaces
- Objective: Define provider-agnostic `MarketDataProvider`, `OptionDataProvider`, and `GreeksProvider` protocols with capability discovery and no provider-specific assumptions.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/interfaces.py`
  - `backend/tests/services/market_data/test_interfaces.py`
  - `backend/tests/unit/test_module_boundaries.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P12-T1`
- Implementation steps:
  1. Define stock quote and intraday bar methods on `MarketDataProvider`.
  2. Define expiration, option chain, and option snapshot methods on `OptionDataProvider`.
  3. Define optional IV/Greeks calculation method on `GreeksProvider`.
  4. Add provider capability discovery using `ProviderCapabilities`.
  5. Add an import-boundary test: `app.services.market_data.*` must not import from `app.services.broker_import.*`.
- Acceptance criteria:
  - Interfaces are separate from broker sync.
  - No real provider calls by default.
  - No option screener or strategy behavior is implemented.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove market data interface files/tests.
- Verification notes:
  - Added `backend/app/services/market_data/interfaces.py` with provider-agnostic `MarketDataProvider`, `OptionDataProvider`, and `GreeksProvider` protocols.
  - Exported the interfaces from `backend/app/services/market_data/__init__.py`.
  - Added `backend/tests/services/market_data/test_interfaces.py` with fake providers covering capability discovery, stock quotes, underlying quotes, intraday quote/bar-like snapshots, option expirations, option quote snapshots, option chain snapshots, and optional Greeks enrichment.
  - Added `backend/tests/unit/test_module_boundaries.py` to assert `app.services.market_data.*` does not import broker sync modules.
  - Verified no market-data service imports broker sync modules and no market-data interface exposes trade/order or strategy-screening methods; matching strings appear only in negative/boundary tests.
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_interfaces.py tests/unit/test_module_boundaries.py` -> `5 passed in 0.05s`.
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_domain_models.py` -> `8 passed in 0.03s`.
  - `cd backend && ./.venv/bin/python -m pytest` -> `171 passed, 92 skipped, 1 deselected in 0.41s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - `git diff --check` passed.
  - No provider implementations, real provider calls, API keys, migrations, external services, frontend code, option screener behavior, or strategy evaluators were introduced.
- Status: `done`

### P12-T3 - Quote Freshness and Actionability Policy

- Task id: `P12-T3`
- Title: Quote Freshness and Actionability Policy
- Objective: Centralize quote freshness and actionability classification while keeping broker sync freshness separate.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/freshness.py`
  - `backend/tests/services/market_data/test_freshness.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P12-T2`
- Implementation steps:
  1. Implement timestamp/provider-mode based quote freshness classification.
  2. Use `freshness_scope="market_quote"` for market freshness responses.
  3. Classify actionability as `actionable_snapshot`, `analysis_only`, `manual_review_required`, `blocked_stale_quote`, `blocked_unknown_quote`, or `blocked_provider_error`.
  4. Ensure stale, unknown, manual, or EOD-only data cannot be labeled immediately actionable.
- Acceptance criteria:
  - Broker freshness and quote freshness are not collapsed into one timestamp.
  - Stale quote data is never labeled immediately actionable.
  - Actionability policy is strategy-agnostic.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove quote freshness/actionability module/tests.
- Verification notes:
  - Added `backend/app/services/market_data/freshness.py` with `QuoteFreshnessDecision`, quote age calculation, timestamp/data-mode freshness classification, and conservative actionability classification.
  - Exported freshness helpers from `backend/app/services/market_data/__init__.py`.
  - Added `backend/tests/services/market_data/test_freshness.py` for fresh live quotes, delayed/manual/EOD analysis-only quotes, stale/unknown blockers, provider-error blockers, manual-review overrides, and invalid vocabulary rejection.
  - Policy is intentionally conservative: only fresh live market quote snapshots can be `actionable_snapshot`; delayed, manual, EOD-only, stale, unknown, and provider-error data cannot be labeled immediately actionable.
  - Focused market-data test run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data` -> `27 passed in 0.06s`.
  - Full backend test run after P12-T7: `192 passed, 92 skipped, 1 deselected in 0.52s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - No broker freshness fields were reused or collapsed into market quote freshness.
- Status: `done`

### P12-T4 - API-Facing Market Data Schemas

- Task id: `P12-T4`
- Title: API-Facing Market Data Schemas
- Objective: Add API-facing schemas for stock quotes, underlying quotes, option quotes, option chains, provider status, freshness, and actionability.
- Files expected to change:
  - `backend/app/schemas/market_data.py`
  - `backend/tests/unit/test_market_data_schemas.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P12-T3`
- Implementation steps:
  1. Define stock quote, underlying quote, option quote, option chain, and provider status response schemas.
  2. Include provider, timestamp, data mode, freshness status, actionability status, and freshness scope.
  3. Add exact-set schema tests for market quote freshness schemas. OpenAPI route tests are deferred until a public market-data route exists.
  4. Keep broker holdings/cash fields out of market quote schemas.
- Acceptance criteria:
  - Market schemas distinguish quote freshness from broker freshness.
  - No broker holdings, broker account ids, cash balances, or private account fields appear in market quote schemas.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Revert market data schemas and tests.
- Verification notes:
  - Added `backend/app/schemas/market_data.py` with Pydantic schemas for quote freshness, provider capabilities, provider status, option contract identity, stock quotes, underlying quotes, option quotes, and option chains.
  - Added `backend/tests/unit/test_market_data_schemas.py` with exact field-set assertions and forbidden broker/cash/private-field assertions.
  - Verified schemas preserve `freshness_scope="market_quote"` and validate from immutable domain objects.
  - No public market-data router was introduced in this task; OpenAPI route-level tests remain deferred until a market-data API route is intentionally added.
  - Focused schema/freshness run: `cd backend && ./.venv/bin/python -m pytest tests/unit/test_market_data_schemas.py tests/services/market_data/test_freshness.py` -> `11 passed in 0.05s`.
  - Full backend test run after P12-T7: `192 passed, 92 skipped, 1 deselected in 0.52s`.
  - No broker holdings, broker account ids, cash balances, secret fields, raw payloads, or private account fields appear in market quote schemas.
- Status: `done`

### P12-T5 - Manual/Mock Provider

- Task id: `P12-T5`
- Title: Manual/Mock Provider
- Objective: Add a deterministic provider for manually supplied or synthetic quote and option-chain snapshots.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/manual_provider.py`
  - `backend/tests/services/market_data/test_manual_provider.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P12-T4`
- Implementation steps:
  1. Implement provider using explicit synthetic stock quote, underlying quote, option quote, option chain, and Greeks inputs.
  2. Support manual, delayed, stale, EOD-only, and unknown modes without network calls.
  3. Mark freshness and actionability based on supplied quote timestamps and data mode.
  4. Avoid API keys, network access, and provider-specific assumptions.
- Acceptance criteria:
  - Market data tests run without external providers.
  - Manual/mock quotes can feed future deterministic option/risk tests.
  - No real provider integrations are introduced.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove manual provider and tests.
- Verification notes:
  - Added `backend/app/services/market_data/manual_provider.py` with deterministic `ManualMarketDataProvider`, `ManualMarketDataNotFoundError`, `build_manual_stock_quote`, and `build_manual_option_quote`.
  - Exported manual provider helpers from `backend/app/services/market_data/__init__.py`.
  - Added `backend/tests/services/market_data/test_manual_provider.py` covering provider protocol conformance, explicit stock/underlying/option quote retrieval, option chain construction from explicit quotes, delayed/stale/EOD/unknown modes, and safe missing-data errors.
  - Manual/mock provider uses explicit in-memory synthetic inputs only; no network clients, API keys, SDK imports, or provider-specific assumptions were added.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_manual_provider.py tests/unit/test_market_data_schemas.py tests/services/market_data/test_freshness.py` -> `15 passed in 0.06s`.
  - Full backend test run after P12-T7: `192 passed, 92 skipped, 1 deselected in 0.52s`.
- Status: `done`

### P12-T6 - Snapshot and Report Reproducibility Policy

- Task id: `P12-T6`
- Title: Snapshot and Report Reproducibility Policy
- Objective: Define how current quote/chain cache, selected candidate snapshots, and report input snapshots will be handled later without building a full historical options warehouse.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/snapshots.py`
  - `backend/tests/services/market_data/test_snapshots.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P12-T5`
- Implementation steps:
  1. Define policy objects or helpers for current chain cache vs selected candidate snapshot vs report input snapshot.
  2. Define future `quote_snapshot_id` and `chain_snapshot_id` usage for deterministic reports and agent runs.
  3. Add tests proving old report inputs should reference saved snapshots rather than current quotes.
  4. Do not add migrations or full historical options storage yet.
- Acceptance criteria:
  - Reports and strategy evaluations have a clear path to reproducible market inputs.
  - No full historical options warehouse is implemented.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove snapshot policy helpers/tests.
- Verification notes:
  - Added `backend/app/services/market_data/snapshots.py` with lightweight snapshot reference helpers for stock quote snapshots, option quote snapshots, option chain snapshots, and frozen report input snapshots.
  - Exported snapshot policy helpers from `backend/app/services/market_data/__init__.py`.
  - Added `backend/tests/services/market_data/test_snapshots.py` proving stable snapshot metadata, chain stable keys, report inputs using saved snapshot references, rejection of current-cache references for report inputs, and non-empty snapshot ids.
  - No database tables, migrations, historical options warehouse, or current quote lookup behavior were introduced.
  - Focused market-data run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data` -> `27 passed in 0.06s`.
  - Full backend test run after P12-T7: `192 passed, 92 skipped, 1 deselected in 0.52s`.
- Status: `done`

### P12-T7 - Mocked Market Data Tests

- Task id: `P12-T7`
- Title: Mocked Market Data Tests
- Objective: Cover domain models, provider interfaces, contract identity, manual/mock provider behavior, freshness, actionability, and module boundaries.
- Files expected to change:
  - `backend/tests/services/market_data/*`
  - `backend/tests/unit/test_module_boundaries.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P12-T6`
- Implementation steps:
  1. Add provider contract tests.
  2. Add quote freshness and actionability tests.
  3. Add option contract identity tests, including unsupported/adjusted/manual-review cases.
  4. Add manual provider tests.
  5. Confirm no external provider calls run by default.
- Acceptance criteria:
  - Market data layer is safe to use without real credentials.
  - Market data layer remains strategy-agnostic and separate from broker sync.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove market data tests and fixtures.
- Verification notes:
  - Market data tests now cover domain models, provider interfaces, quote freshness/actionability, manual/mock provider behavior, snapshot reference policy, API-facing schemas, and module boundaries.
  - Added a module-boundary guard to ensure `app.services.market_data.*` imports no broker sync modules, network clients, or real provider SDKs such as `requests`, `httpx`, `yfinance`, `tradier`, `alpaca`, `polygon`, or `snaptrade`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data tests/unit/test_market_data_schemas.py tests/unit/test_module_boundaries.py` -> `34 passed in 0.06s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `192 passed, 92 skipped, 1 deselected in 0.52s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - `git diff --check` passed.
  - No external provider calls, real credentials, broker data, frontend code, option-chain browser, option screener, trading UI, or strategy evaluators were introduced.
- Status: `done`

### P12-T8 - Claude review of market data contracts

- Task id: `P12-T8`
- Title: Claude review of market data contracts
- Objective: Ask Claude Sonnet to review the completed Phase 12 backend contract for frontend usability, data freshness clarity, accessibility implications, and finance-safety copy before UI work starts.
- Files expected to change:
  - `backend/app/services/market_data/freshness.py`
  - `backend/app/services/market_data/manual_provider.py`
  - `backend/app/services/market_data/snapshots.py`
  - `backend/tests/services/market_data/test_freshness.py`
  - `backend/tests/services/market_data/test_manual_provider.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P12-T7`
- Implementation steps:
  1. Generate a focused Claude handoff prompt with files limited to market data schemas, provider models, freshness logic, tests, and the relevant plan section.
  2. Require Claude to use `frontend-design` and `finance-dashboard-ux-review`.
  3. Codex adjudicates findings before any frontend implementation.
- Acceptance criteria:
  - Frontend implications are reviewed before adding market data UI.
  - Any accepted backend contract fixes land before P12-T9.
- Tests to run:
  - Documentation/review task only; no tests unless contract fixes are accepted.
- Rollback notes:
  - Remove review notes from the plan if superseded.
- Verification notes:
  - Claude review verdict: PASS, no blockers. Codex adjudicated three findings before frontend P12-T9.
  - I1 decision: accept. Manual/mock providers must not mint `actionable_snapshot`; `build_manual_stock_quote` and `build_manual_option_quote` now reject data modes outside `ManualMarketDataProvider` capabilities, including `live`.
  - I1 evidence: `backend/tests/services/market_data/test_manual_provider.py` now asserts manual builder outputs never have `actionability_status == "actionable_snapshot"` and that `data_mode="live"` raises a safe `ValueError`.
  - I2 decision: partial accept. No new freshness enum was added; `freshness_status` remains quote-recency-oriented while `data_mode` carries cached/indicative semantics. Added a contract docstring in `backend/app/services/market_data/freshness.py` requiring UIs and downstream services to render freshness together with `data_mode` and `actionability_status`.
  - I2 evidence: `backend/tests/services/market_data/test_freshness.py` now asserts recent `cached` and `indicative` quotes are `analysis_only` even when their recency freshness is `fresh`.
  - I3 decision: accept as contract-clarity/documentation. `backend/app/services/market_data/snapshots.py` now states snapshot references store metadata only and each `snapshot_id` must resolve to an immutable stored quote/chain payload for true report reproducibility.
  - I3 Phase 13 prerequisite: before deterministic risk reports rely on market quote snapshots, Phase 13 or a prerequisite hardening task must add immutable stored quote/chain payload storage or explicitly store complete market input snapshots in the report input snapshot.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_manual_provider.py tests/services/market_data/test_freshness.py tests/services/market_data/test_snapshots.py` -> `18 passed in 0.05s`.
  - Full backend run after fixes: `cd backend && ./.venv/bin/python -m pytest` -> `195 passed, 92 skipped, 1 deselected in 0.59s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - No real provider calls, network calls, migrations, frontend code, option screeners, trading UI, or wheel assumptions were introduced.
- Status: `done`

### P12-T9 - Frontend market data status slice

- Task id: `P12-T9`
- Title: Frontend market data status slice
- Objective: Add a thin read-only frontend surface for market data availability and quote freshness using only the Phase 12 manual/mock contract.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/README.md`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P12-T8`
- Implementation steps:
  1. Add a small market data status panel or placeholder view that makes quote data availability explicit.
  2. Show `freshness_scope="market_quote"` separately from broker portfolio freshness.
  3. Use only manual/mock provider responses; no real provider API calls.
  4. Keep option screener, option-chain browsing, TradingAgents UI, and trade execution UI out of scope.
  5. Ask Claude Sonnet to implement or design this slice, then have Codex review security and API-contract alignment.
- Acceptance criteria:
  - UI distinguishes market quote freshness from broker sync freshness.
  - UI does not imply live/intraday quotes unless the backend says so.
  - No API keys, broker credentials, provider secrets, or account data are stored in browser storage.
  - Frontend typecheck, lint, and build pass.
- Tests to run:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Revert the frontend market status slice and related docs.
- Status: `done`
- Verification notes (2026-05-17):
  - Added `frontend/src/types/marketData.ts` mirroring `market_data.py`
    (`DataMode`, `FreshnessStatus`, `ActionabilityStatus`,
    `ProviderCapabilitiesRead`, `MarketDataProviderStatusRead`).
  - Added `MarketDataStatusPanel` + `MarketDataPage` at route `/market-data`,
    plus a sidebar nav item (collapsed-aware).
  - Static, contract-faithful manual/mock sample only — no fetch, no real
    provider call, no browser storage. Sample uses `data_mode="manual"`,
    `freshness_status="manual"`, `actionability_status="analysis_only"`
    (manual provider cannot mint `actionable_snapshot`, per Codex adjudication).
  - `freshness_status` is never rendered alone — always clustered with
    `data_mode` and `actionability_status`.
  - `freshness_scope="market_quote"` labelled and explicitly separated from
    broker portfolio sync freshness (separation notice on the page).
  - Conservative copy only: "provider not connected yet", "manual/mock inputs
    only", "do not treat as live market pricing", "broker holdings/cash from
    broker sync; market quotes separate". No live/intraday/guaranteed/trade copy.
  - `npm run typecheck`, `npm run lint` (--max-warnings 0), `npm run build` all
    passed. localStorage remains limited to `poa-appearance` /
    `poa-sidebar-collapsed` (no new storage added).

### P12-T10 - Codex integration review for Phase 12 vertical slice

- Task id: `P12-T10`
- Title: Codex integration review for Phase 12 vertical slice
- Objective: Review backend + frontend together after P12-T9 to verify the market data contract, UI copy, and freshness boundary are safe before Phase 13 starts.
- Files expected to change:
  - `docs/shared/implementation_plan.md`
  - `frontend/src/components/marketdata/MarketDataStatusPanel.tsx` (only if review finds a small contract-copy/sample mismatch)
- Dependencies: `P12-T9`
- Implementation steps:
  1. Run backend and frontend tests.
  2. Inspect OpenAPI/frontend types for market quote fields and freshness scope.
  3. Confirm broker freshness and market quote freshness are not collapsed.
  4. Update verification notes.
- Acceptance criteria:
  - Phase 12 ships as a small vertical slice, not a backend-only foundation.
  - Phase 13 can consume manual/mock market inputs safely.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Revert integration notes or reopen P12-T9 if issues are found.
- Status: `done`

Verification notes:

- Codex integration review verdict: PASS. P12-T9 remains a thin frontend market-data status slice and does not start option-chain browsing, screening, trading UI, real providers, or live quote claims.
- Files changed during P12-T10:
  - `frontend/src/components/marketdata/MarketDataStatusPanel.tsx`
  - `docs/shared/implementation_plan.md`
- Review finding and fix:
  - Found one small contract-polish mismatch: the static `MarketDataProviderStatusRead.checked_at` sample was a prose string even though the backend schema exposes `checked_at: datetime`.
  - Fixed `SAMPLE_STATUS.checked_at` to an ISO timestamp string (`2026-05-18T15:00:00Z`) while keeping the panel static and mock/manual-only.
- Backend/frontend contract review:
  - `frontend/src/types/marketData.ts` mirrors the backend market-data status vocabulary and keeps `freshness_scope: "market_quote"`.
  - `frontend/src/components/marketdata/MarketDataStatusPanel.tsx` renders `data_mode`, `freshness_status`, and `actionability_status` together and never renders freshness status alone.
  - `frontend/src/pages/MarketDataPage.tsx` explicitly states that broker holdings/cash come from broker sync and market quotes are a separate, not-yet-connected source.
  - The frontend market-data slice performs no network calls, adds no browser storage, and uses only static manual/mock sample data.
- Safety boundary review:
  - Broker portfolio freshness and market quote freshness remain separate (`broker_portfolio` vs. `market_quote`).
  - No real SnapTrade, market data provider, LLM, or TradingAgents calls were made.
  - No `.env` or secret files were read.
  - No trade/order/cancel/disconnect UI, option screener, guaranteed-return wording, or live-market-price implication was introduced.
- Tests run:
  - `cd backend && ./.venv/bin/python -m pytest`
    - Result: `195 passed, 92 skipped, 1 deselected in 0.53s`
    - Skips are the expected guarded database tests because the configured database is unavailable or not marked safe for destructive tests in this environment.
  - `cd frontend && npm run typecheck`
    - Result: passed (`tsc --noEmit`)
  - `cd frontend && npm run lint`
    - Result: passed (`eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0`)
  - `cd frontend && npm run build`
    - Result: passed (`77 modules transformed`, built in `469ms`)
- Acceptance criteria evidence:
  - Small vertical slice: backend market-data contracts/manual provider plus a static frontend market-data status page are complete; no speculative provider or screener surface was added.
  - Phase 13 can consume manual/mock market inputs safely: backend market-data tests cover domain models, provider interfaces, freshness/actionability, snapshots, schemas, module boundaries, and manual provider behavior; frontend copy preserves the manual/mock analysis-only boundary.
- Residual risk:
  - Phase 13 deterministic risk reports must still freeze market input payloads or add stored immutable quote/chain payloads before reports depend on market data.
  - Real market data provider integration remains deferred; Phase 12 intentionally makes zero real provider calls.

## Phase 13 - Generic Options Metrics and Portfolio Risk Engine

Phase goal: implement reusable deterministic option metrics and portfolio risk services before strategy evaluators or custom agents explain them. This phase is not a wheel-strategy phase. Python calculates all metrics; LLMs may explain structured results later but must not invent metrics. Strategy-specific CSP, covered-call, collar, spread, hedge, or wheel lifecycle logic belongs in the strategy evaluator layer after these generic services are stable.

Phase 13 prerequisite: deterministic risk reports that rely on market data must consume immutable market input snapshots. Before report outputs depend on quote/chain data, add stored quote/chain payload support or embed complete frozen quote/chain payloads in the report input snapshot; metadata-only `snapshot_id` references are not sufficient by themselves for reproducibility.

### P13-T1 - option formulas

- Task id: `P13-T1`
- Title: option formulas
- Objective: Implement deterministic formulas for premium yield, annualized ROI, breakeven, downside buffer, bid-ask spread percentage, and premium capture.
- Files expected to change:
  - `backend/app/services/options/formulas.py`
  - `backend/tests/services/options/test_formulas.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P12-T10`
- Implementation steps:
  1. Add pure-Python Decimal-based formulas.
  2. Document inputs and units.
  3. Add edge-case tests for zero/invalid inputs.
- Acceptance criteria:
  - Formula outputs are deterministic and covered by unit tests.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove formulas and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/options/formulas.py` as a pure-Python,
  Decimal-only formula module. No database, API route, market data provider,
  broker sync service, LLM, TradingAgents, or frontend code was touched.
- Formulas implemented:
  - `premium_yield(premium, capital_at_risk)`
  - `annualized_roi(return_amount, capital_at_risk, days_held)`
  - `breakeven_after_credit(reference_price, credit)`
  - `downside_buffer(reference_price, breakeven_price)`
  - `bid_ask_spread_percentage(bid, ask)`
  - `premium_capture(initial_credit, current_debit_to_close)`
- Units are documented in function docstrings. Returned percentages are raw
  Decimal ratios; presentation layers decide rounding and percent formatting.
- Added `backend/tests/services/options/test_formulas.py` with deterministic
  unit coverage for normal cases and invalid zero/negative edge cases.
- Tests run:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/options/test_formulas.py`
    - Result: `19 passed in 0.02s`
  - `cd backend && ./.venv/bin/python -m pytest`
    - Result: `214 passed, 92 skipped, 1 deselected in 0.49s`
    - Skips are the expected guarded database tests because the configured
      database is unavailable or not marked safe for destructive tests in this
      environment.
- Claude handoff:
  - No frontend/UI work is needed for P13-T1 alone. The next Claude-owned work
    should wait until a reviewable risk output surface exists later in Phase 13
    (for example after collateral, assignment/allocation, and risk-rule outputs
    are stable enough for a thin risk-review UI slice).

### P13-T2 - collateral and free cash

- Task id: `P13-T2`
- Title: collateral and free cash
- Objective: Calculate generic option collateral usage, free cash, and cash reserve impact for account-level risk review.
- Files expected to change:
  - `backend/app/services/risk/collateral.py`
  - `backend/tests/services/risk/test_collateral.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P13-T1`
- Implementation steps:
  1. Calculate collateral usage from account positions and strategy-neutral collateral inputs.
  2. Distinguish total cash, reserved collateral, and free cash.
  3. Keep account values synthetic in tests.
- Acceptance criteria:
  - Cash/collateral outputs are deterministic and account scoped.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove collateral service and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/collateral.py` as a deterministic,
  strategy-neutral collateral module.
- Added `CollateralRequirement`, `CollateralSummary`, and
  `calculate_collateral_summary(...)`.
- The service distinguishes `total_cash`, `existing_reserved_cash`,
  `option_collateral_required`, `total_reserved_cash`, `free_cash`, and
  `collateral_utilization`.
- Negative `free_cash` is allowed as a deterministic risk signal instead of
  being clamped.
- Added `backend/tests/services/risk/test_collateral.py` with synthetic unit
  coverage for normal calculations and invalid inputs.
- Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk/test_collateral.py` -> `8 passed in 0.02s`.

### P13-T3 - assignment and exercise scenario

- Task id: `P13-T3`
- Title: assignment and exercise scenario
- Objective: Project cash, holdings, concentration, and allocation after selected option assignment or exercise scenarios.
- Files expected to change:
  - `backend/app/services/risk/assignment.py`
  - `backend/tests/services/risk/test_assignment.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P13-T2`
- Implementation steps:
  1. Project assigned/exercised shares and cash impact from structured scenario inputs.
  2. Calculate projected allocation and concentration.
  3. Emit structured scenario outputs.
- Acceptance criteria:
  - Assignment projections do not depend on LLMs.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove assignment service and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/assignment.py` as a deterministic
  assignment/exercise scenario projection module.
- Added support for `short_put_assignment`, `short_call_assignment`,
  `long_call_exercise`, and `long_put_exercise`.
- The projection emits share delta, cash delta, projected cash, projected total
  value, projected holdings, and largest-position concentration.
- The service rejects scenarios that would create negative projected long-share
  quantities.
- Added `backend/tests/services/risk/test_assignment.py` with synthetic unit
  coverage for short put assignment, short call assignment, long option
  exercise actions, and invalid inputs.
- Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk/test_assignment.py tests/services/risk/test_collateral.py` -> `19 passed in 0.03s`.

### P13-T4 - allocation impact service

- Task id: `P13-T4`
- Title: allocation impact service
- Objective: Calculate projected allocation drift, concentration, and exposure impact from generic portfolio or option scenarios.
- Files expected to change:
  - `backend/app/services/risk/allocation.py`
  - `backend/tests/services/risk/test_allocation.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P13-T3`
- Implementation steps:
  1. Calculate target allocation drift and concentration.
  2. Support projected post-scenario allocation inputs.
  3. Keep account allocation rules synthetic/config-driven in tests.
- Acceptance criteria:
  - Allocation impact outputs are deterministic and strategy-agnostic.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove allocation impact service and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/allocation.py` as a deterministic,
  strategy-agnostic allocation and concentration module.
- Added `AllocationPosition`, `AllocationTarget`, `AllocationImpactItem`,
  `AllocationImpact`, and `calculate_allocation_impact(...)`.
- The service calculates total value, actual weights, optional target drift,
  absolute drift, and largest-position concentration.
- Added `backend/tests/services/risk/test_allocation.py` with synthetic unit
  coverage for target drift, missing targets, empty/zero-value portfolios, and
  invalid inputs.
- Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk/test_allocation.py tests/services/risk/test_assignment.py tests/services/risk/test_collateral.py` -> `27 passed in 0.05s`.

### P13-T5 - risk rule engine

- Task id: `P13-T5`
- Title: risk rule engine
- Objective: Evaluate deterministic risk rule violations from option metrics, collateral, assignment/exercise scenarios, allocation impact, quote freshness, and broker freshness.
- Files expected to change:
  - `backend/app/services/risk/violations.py`
  - `backend/tests/services/risk/test_violations.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P13-T4`
- Implementation steps:
  1. Emit `risk_rule_violations` as deterministic structured outputs.
  2. Use severity values `info`, `warning`, `violation`, and `blocker`.
  3. Keep strategy thresholds configurable or synthetic; do not hardcode private thresholds.
- Acceptance criteria:
  - Risk-rule violations are structured, deterministic, and severity tagged.
  - LLMs are not used to create or modify violations.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove risk rule engine and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/violations.py` as a deterministic
  risk-rule violation engine.
- Added `RiskRuleViolation`, `RiskThresholdRule`,
  `evaluate_threshold_rules(...)`, `evaluate_market_actionability(...)`, and
  `evaluate_broker_freshness(...)`.
- Severity vocabulary is structured as `info`, `warning`, `violation`, and
  `blocker`.
- Missing required metrics emit blocker violations instead of silently passing.
- Broker freshness and market quote actionability remain distinct input sources.
- Added `backend/tests/services/risk/test_violations.py` with synthetic unit
  coverage for threshold rules, missing metrics, market actionability, broker
  freshness, and invalid inputs.
- Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk/test_violations.py tests/services/risk/test_allocation.py tests/services/risk/test_assignment.py tests/services/risk/test_collateral.py` -> `48 passed in 0.05s`.

### P13-T6 - deterministic risk report

- Task id: `P13-T6`
- Title: deterministic risk report
- Objective: Combine portfolio summary, market inputs, option formulas, collateral, assignment/exercise scenarios, allocation impact, and violations into a deterministic risk report.
- Files expected to change:
  - `backend/app/services/risk/report.py`
  - `backend/tests/services/risk/test_report.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P13-T5`
- Implementation steps:
  1. Compose deterministic report sections from structured service outputs.
  2. Persist or hand off to Phase 10 report history where appropriate.
  3. Keep narrative explanation template-based for now.
- Acceptance criteria:
  - A deterministic risk report can be generated with synthetic inputs.
  - Report identifies risk-rule violations without LLM invention.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove deterministic risk report service and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/report.py` as a template-based
  deterministic risk report composer.
- Added `RiskReportSection`, `DeterministicRiskReport`,
  `build_deterministic_risk_report(...)`, and
  `render_risk_report_markdown(...)`.
- The report combines option metrics, collateral summary, assignment/exercise
  scenario projections, allocation impact, risk-rule violations, calculation
  version, generated timestamp, and an input snapshot reference.
- Markdown output is conservative and explicitly says it comes from
  deterministic Python services only; no LLM narrative is generated.
- Persistence to Phase 10 report history is not wired yet; the service returns
  structured output and markdown for later API/UI integration.
- Added `backend/tests/services/risk/test_report.py` with synthetic unit
  coverage for composed sections, markdown output, violation display, no-
  violation state, and required-field validation.
- Focused risk-service test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk` -> `52 passed in 0.05s`.
- Full backend test result after P13-T2 through P13-T6:
  `cd backend && ./.venv/bin/python -m pytest` -> `266 passed, 92 skipped, 1 deselected in 0.53s`.
  Skips are the expected guarded database tests because the configured database
  is unavailable or not marked safe for destructive tests in this environment.
- Claude handoff:
  - Backend deterministic risk contracts are now ready for P13-T7 review before
    any P13-T8 frontend risk-review slice begins.

### P13-T7 - Claude review of generic risk contracts

- Task id: `P13-T7`
- Title: Claude review of generic risk contracts
- Objective: Ask Claude Sonnet or Opus, depending on risk level, to review generic deterministic risk output schemas and frontend implications before building the risk UI slice.
- Files expected to change:
  - `docs/shared/implementation_plan.md`
  - Accepted-fix files from Claude review, if any, before P13-T8:
    - `backend/app/schemas/risk.py`
    - `backend/app/services/options/formulas.py`
    - `backend/app/services/risk/allocation.py`
    - `backend/app/services/risk/assignment.py`
    - `backend/app/services/risk/collateral.py`
    - `backend/app/services/risk/report.py`
    - `backend/app/services/risk/violations.py`
    - `backend/tests/services/options/test_formulas.py`
    - `backend/tests/services/risk/test_allocation.py`
    - `backend/tests/services/risk/test_assignment.py`
    - `backend/tests/services/risk/test_collateral.py`
    - `backend/tests/services/risk/test_report.py`
    - `backend/tests/unit/test_risk_schemas.py`
- Dependencies: `P13-T6`
- Implementation steps:
  1. Generate a focused Claude handoff prompt limited to deterministic option/risk services, schemas, tests, and this plan section.
  2. Use Opus only if the review concerns financial calculation semantics, collateral, assignment exposure, or long/short liability handling.
  3. Require review output to separate blockers, important issues, deferrals, and suggested changes for Codex.
  4. Codex adjudicates findings before UI work starts.
- Acceptance criteria:
  - Deterministic outputs are reviewed before UI presentation.
  - Any accepted backend correctness fixes land before P13-T8.
- Tests to run:
  - Documentation/review task only; no tests unless fixes are accepted.
- Rollback notes:
  - Remove review notes if superseded.
- Status: `done`

Verification notes (2026-05-17):

- Opus review raised two blockers (B1: unbounded report contract / no
  broker-secret guard; B2: no deterministic aggregate severity) and seven
  important finance-semantics issues. Codex accepted and fixed all of them.
- B1 resolved: added `backend/app/schemas/risk.py` read schemas with a
  broker/cash/secret/raw-payload forbidden-key guard at both the domain
  (`RiskReportSection`) and schema layers; `input_snapshot` is now typed
  `ReportMarketDataSnapshot | None` instead of `Mapping[str, object]`;
  rendered markdown and the public Read schema no longer expose `account_id`.
- B2 resolved: deterministic `highest_severity` / `has_blocker` added and
  tested using the `info<warning<violation<blocker` ordering.
- Important issues resolved: split downside vs upside breakeven helpers;
  documented annualized ROI as simple/non-compounded/not a forecast;
  documented zero-cash collateral semantics and surfaced free cash;
  documented naked short-call assignment as an MVP scope boundary;
  relabeled assignment vs allocation weight denominators; added
  missing-target allocation drift rows; documented the broker-vs-market
  severity asymmetry.
- Tests: focused `84 passed`; full `279 passed, 92 skipped, 1 deselected`;
  `git diff --check` passed.
- Opus re-review verdict: PASS — contract is safe for a read-only frontend.
  P13-T8 may proceed.
- Deferred (track, not P13-T8 blockers): consolidate the duplicated
  forbidden-key constant (currently in `schemas/risk.py`, `risk/report.py`,
  and `tests/unit/test_risk_schemas.py`) into one shared source before a
  real risk API route is added; the report-fact guard is key-name based,
  so the future route assembling `option_metrics` must be audited so
  broker-sourced values cannot be injected under benign metric keys.

Verification notes:

- Claude P13-T7 review verdict: BLOCKED at the P13-T7 -> P13-T8 gate. Backend
  commit/correctness was acceptable, but the risk report contract was not yet
  safe to expose to frontend.
- Codex adjudication and decisions:
  - B1 accepted. Risk report output needed a constrained read contract and a
    broker/private-data guard. Added `backend/app/schemas/risk.py` with explicit
    read schemas for risk reports, sections, violations, and typed market-data
    snapshot references. Changed deterministic reports to use
    `ReportMarketDataSnapshot | None` instead of unbounded
    `Mapping[str, object]`. Added report fact-key guards against broker,
    cash, secret, and raw-provider fields.
  - B2 accepted. The frontend should not derive severity precedence. Added
    deterministic `highest_severity` and `has_blocker` to
    `DeterministicRiskReport`, populated them in report building, rendered them
    in markdown, and covered blocker precedence in tests.
  - Annualized ROI finding accepted. Documented it as simple, non-compounded
    linear extrapolation and not a forecast. Added negative-return coverage.
  - Breakeven direction finding accepted. Constrained
    `breakeven_after_credit` to downside/credit-reduces-cost use and added
    `upside_breakeven_after_credit` for upper-boundary use. Added a
    counterexample test showing the two directions differ.
  - Zero-cash collateral utilization finding partially accepted. Kept
    `collateral_utilization == 0` when `total_cash == 0` because the percentage
    denominator is undefined, but documented and tested that `free_cash < 0`
    plus `total_reserved_cash` are the authoritative over-commitment signals.
  - Naked short-call assignment finding accepted as a scope boundary. The MVP
    assignment engine models long-share holdings only; a short-call assignment
    that would create short stock raises instead of modeling margin/short-stock
    behavior. Added explicit docs and test coverage.
  - Valuation/weight semantics finding accepted. Documented that assignment
    projections reprice only the scenario underlying while other holdings keep
    supplied values; assignment concentration weights include projected cash,
    while allocation impact weights exclude cash unless cash is supplied as a
    position. Report fact labels now distinguish these denominators.
  - Missing-target allocation finding accepted. Allocation impact now emits
    zero-position drift items for targets that have no matching position, so
    under-allocation is visible.
  - Broker-vs-market severity asymmetry finding accepted. Added a module
    docstring explaining why market quote stale/unknown/provider-error states
    block actionable risk analysis while stale/cached broker data is warning
    unless the broker state is error/reauth-required.
  - Deferred: the engine does not yet self-emit informational findings, and
    markdown still renders Decimals with default string formatting. These are
    presentation/report-polish concerns and do not block the schema/safety gate.
- Code/tests changed for accepted items:
  - `backend/app/schemas/risk.py`
  - `backend/app/services/options/formulas.py`
  - `backend/app/services/risk/allocation.py`
  - `backend/app/services/risk/assignment.py`
  - `backend/app/services/risk/collateral.py`
  - `backend/app/services/risk/report.py`
  - `backend/app/services/risk/violations.py`
  - `backend/tests/services/options/test_formulas.py`
  - `backend/tests/services/risk/test_allocation.py`
  - `backend/tests/services/risk/test_assignment.py`
  - `backend/tests/services/risk/test_collateral.py`
  - `backend/tests/services/risk/test_report.py`
  - `backend/tests/unit/test_risk_schemas.py`
- Tests run:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/options/test_formulas.py tests/services/risk tests/unit/test_risk_schemas.py`
    - Result: `84 passed in 0.14s`
  - `cd backend && ./.venv/bin/python -m pytest`
    - Result: `279 passed, 92 skipped, 1 deselected in 0.65s`
    - Skips are the expected guarded database tests because the configured
      database is unavailable or not marked safe for destructive tests in this
      environment.
- Gate status:
  - RESOLVED. The Opus re-review (see "Opus re-review verdict: PASS" above)
    confirmed the deterministic risk report contract is safe for a read-only
    frontend. The earlier BLOCKED gate is cleared; P13-T8 proceeded.

### P13-T8 - Frontend generic risk review slice

- Task id: `P13-T8`
- Title: Frontend generic risk review slice
- Objective: Add a read-only frontend view for deterministic option metrics, collateral, assignment/exercise scenarios, allocation impact, and risk-rule violations.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/README.md`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P13-T7`
- Implementation steps:
  1. Ask Claude Sonnet to design and implement the risk review slice using `frontend-design` and `finance-dashboard-ux-review`.
  2. Display deterministic outputs as calculated facts, not LLM advice.
  3. Show `risk_rule_violations` by severity: `info`, `warning`, `violation`, `blocker`.
  4. Include loading, empty, missing-market-data, stale-quote, and broker-stale states.
  5. Do not add buy/sell/order/execute controls or guaranteed-return language.
- Acceptance criteria:
  - Users can inspect generic deterministic risk outputs without agent, TradingAgents, or strategy evaluator integration.
  - UI distinguishes deterministic calculations from future LLM-generated explanation.
  - No trade execution UI or broker action UI is introduced.
  - Frontend typecheck, lint, and build pass.
- Tests to run:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Revert the frontend risk review slice and related docs.
- Status: `done`
- Verification notes (2026-05-18):
  - Frontend-only, stubbed slice. There is NO backend risk HTTP route; the UI
    is built against the typed contract using a synthetic in-memory stub
    (`frontend/src/api/riskReview.ts`). No real SnapTrade/Fidelity/market-data/
    LLM/TradingAgents APIs are called; no browser storage; no `.env`/DB access.
  - Files changed:
    - `frontend/src/types/api.ts` — exact mirror of `backend/app/schemas/risk.py`
      (Decimal→string; omits `account_id`/forbidden broker-private keys).
    - `frontend/src/api/riskReview.ts` (new, synthetic stub).
    - `frontend/src/hooks/useRiskReview.ts` (new).
    - `frontend/src/components/risk/RiskReviewPanel.tsx` (new).
    - `frontend/src/pages/RiskReviewPage.tsx` (new).
    - `frontend/src/App.tsx`, `frontend/src/components/layout/Sidebar.tsx`
      (route `/risk` + nav).
  - Codex BLOCKED fixes applied: (B1) generic stub now uses
    `collateral_method: "short_option_cash_reserve"` — no CSP/wheel/covered-call
    strategy wording or UI; (B2) option-chain snapshot `stable_key` now uses
    underlying:expiration semantics (`XYZ:2026-06-19`), distinct from the
    per-contract quote key.
  - Severity is driven solely by backend `has_blocker`/`highest_severity`
    (never recomputed); violations grouped by severity with icon+text;
    deterministic facts rendered verbatim; `annualized_roi` carries the
    "simple annualized — not a forecast, not guaranteed" caveat; market-quote
    provenance shown distinctly from broker freshness; states covered
    (loading/empty/error/missing-market/stale-quote/broker-stale).
  - Build/tests:
    - `cd frontend && npm run typecheck` — passed (0 errors).
    - `cd frontend && npm run lint` — passed (0 warnings, --max-warnings 0).
    - `cd frontend && npm run build` — passed (`index-BxKXnQ5M.js`).
    - `cd backend && ./.venv/bin/python -m pytest` — `279 passed, 92 skipped,
      1 deselected` (unchanged; no backend edits in this task).
  - No interactive browser click-through was performed by Claude (no dev
    server/display in that environment); state coverage was verified via the
    scenario switcher code paths and build, not a visual session.
  - Codex P13-T9 re-review passed on 2026-05-18. Browser click-through was
    intentionally not performed during re-review to avoid opening pages that may
    render real brokerage data; source review plus typecheck/lint/build/backend
    tests passed.

### P13-T9 - Codex integration review for Phase 13 vertical slice

- Task id: `P13-T9`
- Title: Codex integration review for Phase 13 vertical slice
- Objective: Verify backend deterministic risk outputs and the frontend risk review slice align before strategy evaluators are added.
- Files expected to change:
  - `docs/shared/implementation_plan.md`
- Dependencies: `P13-T8`
- Implementation steps:
  1. Run backend and frontend tests.
  2. Confirm frontend fields map directly to deterministic backend outputs.
  3. Confirm no LLM text, strategy recommendation, TradingAgents output, or trade execution affordance is mixed into deterministic risk UI.
  4. Update verification notes.
- Acceptance criteria:
  - Phase 13 ships as a small vertical generic risk-review slice.
  - Strategy evaluators can consume reviewed deterministic outputs in Phase 14.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Reopen P13-T8 if integration issues are found.
- Status: `done`

Verification notes (2026-05-18):

- Codex integration review verdict: PASS.
- Contract fidelity:
  - `frontend/src/types/api.ts` risk types map to
    `backend/app/schemas/risk.py` read schemas:
    `DeterministicRiskReportRead`, `RiskReportSectionRead`,
    `RiskRuleViolationRead`, and `MarketDataSnapshotReferenceRead`.
  - Decimal values are represented as JSON strings in frontend types, and
    section facts allow `string | number | null` for the backend
    `Decimal | str | int | None` shape.
  - Risk-specific client types do not reintroduce `account_id` or other
    broker/private keys that the backend risk schema intentionally omits.
- Frontend safety and deterministic framing:
  - Overall severity is driven by backend `has_blocker` and
    `highest_severity`; the frontend does not re-rank or recompute aggregate
    severity.
  - Risk-rule violations are grouped by literal severity with icon and text,
    not color alone.
  - Deterministic facts are labelled as Python calculation output, separated
    from any future LLM text, and annualized ROI includes the explicit
    "simple annualized — not a forecast, not guaranteed" caveat.
  - Market quote provenance is shown with `freshness_scope="market_quote"` and
    remains separate from broker portfolio freshness.
  - No buy/sell/order/execute/disconnect controls, strategy recommendations,
    TradingAgents output, or real API calls were introduced.
- P13-T8 blocker fixes confirmed:
  - `frontend/src/api/riskReview.ts` uses generic
    `collateral_method: "short_option_cash_reserve"` instead of CSP/wheel
    strategy wording.
  - Option-chain snapshot references use underlying:expiration semantics
    (`XYZ:2026-06-19`) rather than the per-contract quote key.
- Tests run:
  - `cd frontend && npm run typecheck` — passed (0 errors).
  - `cd frontend && npm run lint` — passed (0 warnings, `--max-warnings 0`).
  - `cd frontend && npm run build` — passed (`81 modules transformed`, built in
    `365ms`, output bundle `index-BxKXnQ5M.js`).
  - `cd backend && ./.venv/bin/python -m pytest` — `279 passed, 92 skipped,
    1 deselected in 0.51s`.
  - Skips are the expected guarded database tests because the configured
    database is unavailable or not marked safe for destructive tests in this
    environment.
- Browser click-through was intentionally not performed in this review pass to
  avoid opening pages that may render real brokerage data. A future visual QA
  pass can use synthetic/local-safe state only.
- Deferred:
  - Consolidate the duplicated forbidden-key constant before a real risk API
    route is added.
  - Audit the future route that assembles risk report facts so broker-sourced
    values cannot be injected under benign metric keys.

## Phase 14 - Trade Intent Review Foundation

Phase goal: introduce `TradeIntent` as the core abstraction for proposed manual stock, ETF, and options trades. This phase should broaden the product from options-income review to a portfolio-aware trade review pipeline. It must not add order execution, broker order routes, strategy recommendations, or real provider calls.

### P14-T1 - TradeIntent domain models

- Task id: `P14-T1`
- Title: TradeIntent domain models
- Objective: Define strategy-neutral intent models for proposed stock, ETF, and options trades.
- Files expected to change:
  - `backend/app/services/trade_review/models.py`
  - `backend/tests/services/trade_review/test_models.py`
  - `docs/codex-b-architecture/architecture.md`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P13-T9`
- Implementation steps:
  1. Define `TradeIntent` with shared id, user/account references, asset class, intent type, assumptions, notes, calculation version, and data freshness snapshot.
  2. Define `StockTradeIntent`, `ETFTradeIntent`, `OptionStrategyIntent`, and `OptionLeg`.
  3. Support stock buy, stock sell/trim, ETF review, long call, long put, CSP, and covered-call intents without making any one strategy the schema foundation.
  4. Keep models deterministic and serializable for reports/journals.
- Acceptance criteria:
  - One intent foundation can represent stocks, ETFs, and options.
  - No `covered_call_candidates`, `csp_candidates`, `wheel_positions`, or `premium_income_strategy` core tables/models are introduced.
  - No broker execution/order behavior.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove trade-review model files/tests and plan notes.
- Status: `done`
- Verification notes:
  - Added `backend/app/services/trade_review/models.py` with strategy-neutral `TradeIntent`, `StockTradeIntent`, `ETFTradeIntent`, `OptionStrategyIntent`, and `OptionLeg` contracts.
  - Models serialize to JSON-safe report snapshots and represent stock, ETF, long call, long put, cash-secured put, covered-call, and custom option intents without introducing strategy-specific core tables.
  - Added `backend/app/services/trade_review/__init__.py` exports and `backend/tests/services/trade_review/test_models.py`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review` -> `15 passed in 0.04s`.

### P14-T2 - PortfolioContextBuilder and MarketSnapshotResolver

- Task id: `P14-T2`
- Title: Portfolio context and market snapshot resolution
- Objective: Resolve the portfolio and market inputs needed to review a trade intent without sending sensitive brokerage data to LLMs.
- Files expected to change:
  - `backend/app/services/trade_review/context.py`
  - `backend/app/services/trade_review/snapshots.py`
  - `backend/tests/services/trade_review/test_context.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P14-T1`
- Implementation steps:
  1. Define `PortfolioContextBuilder` inputs/outputs using existing portfolio summaries and positions.
  2. Define `MarketSnapshotResolver` inputs/outputs using Phase 12 market-data snapshots.
  3. Preserve broker freshness and market quote freshness separately.
  4. Return structured context for deterministic services only; do not create LLM prompts in this phase.
- Acceptance criteria:
  - Context and market snapshot outputs are explicit, typed, and freshness-aware.
  - Sensitive provider identifiers, account numbers, raw payloads, and secrets are not included.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove context/snapshot resolver files/tests.
- Status: `done`
- Verification notes:
  - Added `backend/app/services/trade_review/context.py` with sanitized `PortfolioContextBuilder`, cash context, stock position context, option position context, and portfolio review context.
  - Added `backend/app/services/trade_review/snapshots.py` with `MarketSnapshotResolver` and `TradeReviewMarketSnapshot` using Phase 12 market-data snapshot references.
  - Context preserves broker freshness and market quote freshness separately and omits raw provider payloads, account numbers, provider ids, source refs, and secrets.
  - Added `backend/tests/services/trade_review/test_context.py` and `backend/tests/services/trade_review/test_trade_review_snapshots.py`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review` -> `15 passed in 0.04s`.

### P14-T3 - TradeIntentValidator

- Task id: `P14-T3`
- Title: TradeIntentValidator
- Objective: Validate trade intents before deterministic review.
- Files expected to change:
  - `backend/app/services/trade_review/validation.py`
  - `backend/tests/services/trade_review/test_validation.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P14-T2`
- Implementation steps:
  1. Validate supported asset class, action, quantity, option leg shape, expiration, strike, multiplier, and price assumptions.
  2. Emit structured validation warnings/blockers instead of prose-only failures.
  3. Keep unsupported contracts and ambiguous intents as manual-review-required states.
- Acceptance criteria:
  - Invalid or ambiguous intents do not reach the deterministic review engine as actionable.
  - Validation output uses structured severity and codes.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove validator files/tests.
- Status: `done`
- Verification notes:
  - Added `backend/app/services/trade_review/validation.py` with `TradeIntentValidator`, structured finding codes, severities, manual-review flags, and blocker flags.
  - Validator covers stock/ETF missing price assumptions, option premium assumptions, expired options, manual-review contracts, and strategy-shape mismatches without adding recommendation or execution language.
  - Added `backend/tests/services/trade_review/test_validation.py`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review` -> `15 passed in 0.04s`.

### P14-T4 - Journal and report-history links

- Task id: `P14-T4`
- Title: Trade review journal links
- Objective: Link trade intents to report history and future journal entries without adding full journal UI yet.
- Files expected to change:
  - `backend/app/services/trade_review/journal.py`
  - `backend/tests/services/trade_review/test_journal_links.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P14-T3`
- Implementation steps:
  1. Define how reviewed trade intents reference report threads/messages.
  2. Define a future `JournalService` boundary for user notes and post-review tracking.
  3. Do not add broker activity sync, order tracking, or realized P&L history.
- Acceptance criteria:
  - A deterministic review can be traced to the intent and report history.
  - Journal linkage is read-only/audit-oriented, not execution-oriented.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove journal link files/tests.
- Status: `done`
- Verification notes:
  - Added `backend/app/services/trade_review/journal.py` with `TradeReviewReportLink`, `JournalServiceBoundary`, and `link_trade_review_to_report`.
  - Journal linkage is audit-oriented and read-only; full journal notes, broker activity sync, order tracking, realized P&L, and lifecycle reconstruction remain deferred.
  - Added `backend/tests/services/trade_review/test_journal_links.py`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review` -> `15 passed in 0.04s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `294 passed, 92 skipped, 1 deselected in 0.61s`.

### P14-T7 - TradeIntent snapshot and validation hardening

- Task id: `P14-T7`
- Title: TradeIntent snapshot and validation hardening
- Objective: Resolve Phase 14 review findings before Phase 15 consumes trade-review snapshots.
- Files expected to change:
  - `backend/app/services/trade_review/models.py`
  - `backend/app/services/trade_review/validation.py`
  - `backend/tests/services/trade_review/test_models.py`
  - `backend/tests/services/trade_review/test_context.py`
  - `backend/tests/services/trade_review/test_validation.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P14-T4`
- Implementation steps:
  1. Replace unbounded freshness snapshots with typed broker/market freshness fields and guard snapshot/assumption dictionaries against broker/private/secret keys.
  2. Rename stock/ETF `limit_price` to `price_assumption` to keep the model review-oriented rather than order-ticket-oriented.
  3. Add deterministic validation aggregates such as `highest_severity` and `is_clean`; clarify that `can_reach_deterministic_review` only means not blocked.
  4. Add structural forbidden-field tests for trade-review context dataclasses.
  5. Make option strike positive at the model layer and document validation severity as pre-review readiness, distinct from Phase 13 risk-rule severity.
- Acceptance criteria:
  - TradeIntent snapshots cannot persist forbidden broker/private/secret keys through assumptions or freshness snapshots.
  - Stock/ETF intent vocabulary uses price assumptions, not order-ticket limit-price language.
  - Downstream UI can distinguish clean, warning/manual-review, and blocked validation states without recomputing severity.
  - Context dataclasses remain structurally disjoint from forbidden broker/private fields.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review`
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Revert trade-review model/validator/test hardening and restore P14-T1 through P14-T4 contracts.
- Status: `done`
- Verification notes:
  - Accepted Claude findings before Phase 15: unbounded snapshot dicts, weak context privacy test, ambiguous validation aggregate naming, order-ticket-like `limit_price`, validation/risk severity vocabulary clarity, alias placement, positive strike validation, and mutable snapshot-copy risk.
  - Added `TradeIntentFreshnessSnapshot` with explicit broker portfolio and market quote freshness fields, plus recursive forbidden-key guards for freshness notes and assumptions.
  - Reused the Phase 13 forbidden report fact key set and extended it for trade-review snapshots with account-number, SnapTrade, user-secret, consumer-key, token, API-key, and portal-url keys.
  - Renamed stock/ETF `limit_price` to `price_assumption` in models, validator, and tests.
  - Added `highest_severity` and `is_clean` to `TradeIntentValidationResult`; documented that `can_reach_deterministic_review` means not blocked, not clean.
  - Made option strike positive at the model layer and kept unsupported/manual-review option contracts explicit.
  - Added structural context dataclass field-set tests to keep context outputs disjoint from broker/private/provider/raw-payload fields while still allowing internal `account_id` and cash values needed for deterministic review.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review` -> `20 passed in 0.06s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `299 passed, 92 skipped, 1 deselected in 0.71s`.

### P14-T5 - Claude review of TradeIntent contracts

- Task id: `P14-T5`
- Title: Claude review of TradeIntent contracts
- Objective: Review frontend implications, finance-safety language, and product scope before building the deterministic trade review engine.
- Files expected to change:
  - `docs/shared/implementation_plan.md`
- Dependencies: `P14-T7`
- Implementation steps:
  1. Generate a focused Claude handoff prompt limited to TradeIntent models, context/snapshot contracts, validator outputs, and this plan section.
  2. Use Sonnet for UX/copy review; use Opus only for high-risk financial semantics disputes.
  3. Codex adjudicates findings before Phase 15 starts.
- Acceptance criteria:
  - TradeIntent contracts support stock, ETF, and options review without wheel/CSP/covered-call overfitting.
  - Any accepted fixes land before Phase 15.
- Tests to run:
  - Documentation/review task only; no tests unless fixes are accepted.
- Rollback notes:
  - Remove review notes if superseded.
- Status: `done`
- Verification notes:
  - Opus re-review verdict: PASS. Phase 14 trade-intent contracts are safe for Phase 15 to consume and persist.
  - All five Important review items were resolved before closing this gate: typed `TradeIntentFreshnessSnapshot` plus recursive forbidden-key guards; structural context-field privacy tests; `highest_severity` / `is_clean` plus clarified `can_reach_deterministic_review`; `limit_price` renamed to `price_assumption`; validation-vs-risk severity vocabulary documented as distinct readiness vs risk-rule concerns.
  - Deferred items from the review were largely addressed: `MappingSnapshot` is defined before use, and option strikes are positive at the model layer.
  - Two residual polish items from Opus were accepted and handled in this closeout: guarded snapshot mappings now deep-copy nested values before persistence snapshots can be produced, and the forbidden broker/private key set now lives in `backend/app/services/privacy.py` instead of coupling trade-review models to `risk.report`.
  - P14-T1 through P14-T4 and P14-T7 remain done; the physical placement of P14-T7 before P14-T5/P14-T6 is cosmetic and the dependency graph remains coherent.

### P14-T6 - Codex integration review for Phase 14

- Task id: `P14-T6`
- Title: Codex integration review for Phase 14
- Objective: Verify TradeIntent foundation contracts before deterministic trade review services are added.
- Files expected to change:
  - `docs/shared/implementation_plan.md`
- Dependencies: `P14-T5`
- Implementation steps:
  1. Run backend tests.
  2. Confirm TradeIntent, context, snapshot, validation, and journal-link contracts are strategy-neutral.
  3. Confirm no order execution, broker action, or advice wording was introduced.
- Acceptance criteria:
  - Phase 14 can support stock, ETF, and options trade review in Phase 15.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Reopen P14-T5 if integration issues are found.
- Status: `done`
- Verification notes:
  - Codex integration review found no Phase 14 contract regressions; Phase 15 may start.
  - Strategy-neutrality confirmed: Phase 14 supports stock, ETF, and option trade intents, including long call, long put, cash-secured put, covered call, and custom option strategies, without introducing `covered_call_candidates`, `csp_candidates`, `wheel_positions`, or `premium_income_strategy` core models.
  - No order-execution, broker-action, automatic-trading, or advice/recommendation wording was introduced in the trade-review service contracts.
  - Broker-portfolio freshness and market-quote freshness remain typed and separate through `TradeIntentFreshnessSnapshot` and `TradeReviewMarketSnapshot`; context dataclasses remain structurally disjoint from forbidden broker/private/provider/raw-payload fields.
  - Added `backend/app/services/privacy.py` as the shared forbidden-key boundary and updated risk report plus trade-review context tests to use it.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review` -> `22 passed in 0.05s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `301 passed, 92 skipped, 1 deselected in 0.58s`; DB-backed tests skipped because the configured database was unavailable or not marked safe for destructive tests.

## Phase 15 - Deterministic Trade Review Engine MVP

Phase goal: run one deterministic review pipeline for proposed stock, ETF, and options trades. Covered calls and cash-secured puts are early high-value workflows, but not the product identity. Long calls and long puts are included early because many retail options users are buyers, not only premium sellers.

### P15-T1 - PayoffScenarioEngine

- Task id: `P15-T1`
- Title: PayoffScenarioEngine
- Objective: Compute generic payoff/scenario outputs for stock, ETF, and option-leg intents.
- Files expected to change:
  - `backend/app/services/trade_review/payoff.py`
  - `backend/tests/services/trade_review/test_payoff.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P14-T6`
- Implementation steps:
  1. Support stock/ETF price-change scenarios.
  2. Support long call, long put, short put, and short call single-leg scenarios using generic option-leg math.
  3. Keep multi-leg support extensible without building a full optimizer.
- Acceptance criteria:
  - Payoff outputs are deterministic and strategy-neutral.
  - No "best trade" or recommendation logic.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove payoff engine files/tests.
- Status: `done`
- Verification notes:
  - Added `backend/app/services/trade_review/payoff.py` with `PayoffScenarioEngine`, `PriceScenario`, `PayoffReview`, and scenario point outputs for stock, ETF, and option-leg intents.
  - Stock/ETF scenarios compare future prices against `price_assumption`; option scenarios use intrinsic value and premium assumptions for long/short calls and puts.
  - Multi-leg support is additive and extensible; no optimizer, best-trade, or recommendation logic was introduced.
  - Added `backend/tests/services/trade_review/test_payoff.py`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review tests/services/strategies` -> `40 passed in 0.20s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `319 passed, 92 skipped, 1 deselected in 1.18s`; DB-backed tests skipped because the configured database was unavailable or not marked safe for destructive tests.

### P15-T2 - PortfolioImpactEngine

- Task id: `P15-T2`
- Title: PortfolioImpactEngine
- Objective: Calculate cash impact, collateral impact, assignment/exercise exposure, and allocation/concentration impact for a reviewed trade intent.
- Files expected to change:
  - `backend/app/services/trade_review/portfolio_impact.py`
  - `backend/tests/services/trade_review/test_portfolio_impact.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P15-T1`
- Implementation steps:
  1. Consume portfolio context, market snapshots, and payoff outputs.
  2. Compute cash, reserved collateral, projected exposure, and concentration deltas.
  3. Preserve broker freshness and market quote freshness separately.
- Acceptance criteria:
  - Impact outputs are structured and report-ready.
  - Cash/collateral effects are explicit for both option sellers and option buyers.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove portfolio impact engine files/tests.
- Status: `done`
- Verification notes:
  - Added `backend/app/services/trade_review/portfolio_impact.py` with `PortfolioImpactEngine` and structured impact outputs for cash delta, premium cash delta, collateral delta, projected free cash, assignment/exercise share deltas, concentration symbol/value delta, and freshness flags.
  - Cash and collateral effects are explicit for option buyers and sellers; short put collateral is modelled as strike * multiplier * contracts while short call assignment is exposed as share obligation, not margin.
  - Broker portfolio freshness, market quote freshness, and market quote manual-review state remain separate on the impact output.
  - Added `backend/tests/services/trade_review/test_portfolio_impact.py`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review tests/services/strategies` -> `40 passed in 0.20s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `319 passed, 92 skipped, 1 deselected in 1.18s`; DB-backed tests skipped because the configured database was unavailable or not marked safe for destructive tests.

### P15-T3 - RiskRuleEngine integration for trade review

- Task id: `P15-T3`
- Title: RiskRuleEngine integration for trade review
- Objective: Apply deterministic risk rules to trade-review outputs.
- Files expected to change:
  - `backend/app/services/trade_review/risk.py`
  - `backend/tests/services/trade_review/test_risk.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P15-T2`
- Implementation steps:
  1. Convert validation, payoff, portfolio impact, broker freshness, and market freshness results into `risk_rule_violations`.
  2. Support severity: `info`, `warning`, `violation`, `blocker`.
  3. Treat stale/unknown market quote inputs conservatively.
- Acceptance criteria:
  - Risk output is deterministic and frontend-ready.
  - No LLM-generated risk metrics.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove trade-review risk files/tests.
- Status: `done`
- Verification notes:
  - Added `backend/app/services/trade_review/risk.py` with `TradeReviewRiskEngine` and deterministic `TradeReviewRiskResult`.
  - Validation findings, broker freshness, market quote freshness/actionability, missing/manual-review market snapshots, negative projected free cash, and missing cash context for collateral convert into structured `RiskRuleViolation` outputs.
  - Severity remains deterministic and frontend-ready through `highest_severity` and `has_blocker`; no LLM-generated risk metrics were introduced.
  - Added `backend/tests/services/trade_review/test_risk.py`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review tests/services/strategies` -> `40 passed in 0.20s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `319 passed, 92 skipped, 1 deselected in 1.18s`; DB-backed tests skipped because the configured database was unavailable or not marked safe for destructive tests.

### P15-T4 - StrategyEvaluator wrappers

- Task id: `P15-T4`
- Title: StrategyEvaluator wrappers
- Objective: Add thin wrappers around the generic trade-review pipeline for early workflows.
- Files expected to change:
  - `backend/app/services/strategies/interfaces.py`
  - `backend/app/services/strategies/stock_review.py`
  - `backend/app/services/strategies/etf_review.py`
  - `backend/app/services/strategies/options_single_leg.py`
  - `backend/tests/services/strategies/test_trade_review_wrappers.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P15-T3`
- Implementation steps:
  1. Define `StrategyEvaluator.evaluate(intent, portfolio_context, market_snapshot) -> StrategyReview`.
  2. Add `StockBuyReviewEvaluator`, `StockSellTrimReviewEvaluator`, `ETFReviewEvaluator`, `LongCallReviewEvaluator`, `LongPutReviewEvaluator`, `CashSecuredPutEvaluator`, and `CoveredCallEvaluator`.
  3. Keep CSP and covered call as wrappers, not core schema foundations.
- Acceptance criteria:
  - Early evaluators share the same `TradeIntent` pipeline.
  - Wheel lifecycle is not implemented here.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove strategy wrapper files/tests.
- Status: `done`
- Verification notes:
  - Added `backend/app/services/strategies/` with `StrategyEvaluator`, `StrategyReview`, shared base evaluator, and thin wrappers for stock buy, stock sell/trim, ETF review, long call, long put, cash-secured put, and covered call.
  - Wrappers all call the same deterministic trade-review pipeline: validation, payoff, portfolio impact, risk, and report generation.
  - CSP and covered call remain wrappers only; no wheel lifecycle, strategy-specific core tables, or options-income product boundary was introduced.
  - Added `backend/tests/services/strategies/test_trade_review_wrappers.py`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review tests/services/strategies` -> `40 passed in 0.20s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `319 passed, 92 skipped, 1 deselected in 1.18s`; DB-backed tests skipped because the configured database was unavailable or not marked safe for destructive tests.

### P15-T5 - deterministic trade review report

- Task id: `P15-T5`
- Title: deterministic trade review report
- Objective: Generate a versioned deterministic report from trade intent, context, market snapshot, payoff, portfolio impact, and risk-rule outputs.
- Files expected to change:
  - `backend/app/services/trade_review/report.py`
  - `backend/tests/services/trade_review/test_trade_review_report.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P15-T4`
- Implementation steps:
  1. Include calculation versioning and data freshness snapshot.
  2. Persist or link report output through existing report history contracts.
  3. Use review/scenario wording, not advice or recommendation wording.
- Acceptance criteria:
  - Deterministic report is reproducible from structured inputs.
  - No "you should buy/sell", guaranteed-return, or execution language.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove trade review report files/tests.
- Status: `done`
- Verification notes:
  - Added `backend/app/services/trade_review/report.py` with `TradeReviewReport`, `build_trade_review_report`, and conservative deterministic markdown rendering.
  - Report includes calculation version, intent snapshot, data freshness snapshot, validation, payoff, portfolio impact, risk-rule outputs, highest severity, blocker state, market snapshot references, and an optional report-history link.
  - Markdown uses review/scenario-analysis language and explicitly says the report does not recommend, place, route, or manage trades.
  - Added `backend/tests/services/trade_review/test_trade_review_report.py`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review tests/services/strategies` -> `40 passed in 0.20s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `319 passed, 92 skipped, 1 deselected in 1.18s`; DB-backed tests skipped because the configured database was unavailable or not marked safe for destructive tests.

### P15-T6 - Claude review of deterministic trade review contracts

- Task id: `P15-T6`
- Title: Claude review of deterministic trade review contracts
- Objective: Review trade-review outputs and frontend implications before a UI slice.
- Files expected to change:
  - `backend/app/services/trade_review/report.py` (accepted boundary fix)
  - `backend/app/services/trade_review/__init__.py` (accepted boundary export)
  - `backend/tests/services/trade_review/test_trade_review_report.py` (accepted boundary test)
  - `docs/shared/implementation_plan.md`
- Dependencies: `P15-T5`
- Implementation steps:
  1. Generate a focused Claude handoff prompt limited to trade review outputs, report shape, tests, and this plan section.
  2. Use `finance-dashboard-ux-review` and `implementation-plan-review`.
  3. Codex adjudicates findings before frontend work.
- Acceptance criteria:
  - Trade-review contracts are safe to expose in a read-only frontend.
- Tests to run:
  - Documentation/review task only; no tests unless fixes are accepted.
- Rollback notes:
  - Remove review notes if superseded.
- Status: `done`
- Verification notes:
  - Claude review verdict: `PASS`; no blockers for the Phase 15 deterministic engine MVP.
  - Accepted Important #1 as a pre-Phase-16 gate: agent/LLM paths need a redacted projection of trade-review reports so raw account ids and owner cash values are not sent to agents by default. Implemented `TradeReviewAgentProjection`, `AgentSafePortfolioImpact`, and `to_agent_safe_projection` in `backend/app/services/trade_review/report.py`; exported them from `backend/app/services/trade_review/__init__.py`.
  - Added `backend/tests/services/trade_review/test_trade_review_report.py::test_agent_safe_projection_redacts_account_ids_and_absolute_cash_values`, which asserts the projection omits `user_id`, `account_id`, forbidden report fact keys, account UUID strings, `cash_delta`, `projected_free_cash`, and the owner-facing projected free cash value.
  - Partially accepted Important #2: covered-call/CSP portfolio-aware coverage and existing-collateral netting are not modelled deeply enough for a frontend workspace. This does not block Phase 16 agent orchestration because the engine remains generic/backend-only, but before Phase 18 the UI must either receive coverage-aware outputs or prominently caveat that coverage/collateral netting is not modelled.
  - Accepted Important #3 as a pre-Phase-18 contract task: add a typed sanitized trade-review read schema and forbidden-field test before exposing trade-review reports through a real frontend/API surface. The current Phase 15 service objects remain engine-internal.
  - Deferred polish: deduplicate minor report implementation details, cosmetic indentation, sell/trim payoff wording placement in frontend, and import-boundary expansion for `app.services.trade_review.*` / `app.services.strategies.*`.
  - Focused run after the accepted fix: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review tests/services/strategies` -> `41 passed in 0.16s`.
  - Full backend run after the accepted fix: `cd backend && ./.venv/bin/python -m pytest` -> `320 passed, 92 skipped, 1 deselected in 1.26s`; DB-backed tests skipped because the configured database was unavailable or not marked safe for destructive tests.

### P15-T7 - Codex integration review for Phase 15

- Task id: `P15-T7`
- Title: Codex integration review for Phase 15
- Objective: Verify deterministic trade-review outputs before custom agents and frontend workspace work.
- Files expected to change:
  - `docs/shared/implementation_plan.md`
- Dependencies: `P15-T6`
- Implementation steps:
  1. Run backend tests.
  2. Confirm outputs cover stock, ETF, long call, long put, CSP, and covered-call intents.
  3. Confirm no wheel-only, options-income-only, or execution semantics were introduced.
- Acceptance criteria:
  - Phase 15 ships a generic deterministic trade-review engine.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Reopen P15-T6 if integration issues are found.
- Status: `done`
- Verification notes:
  - Confirmed Phase 15 remains a generic deterministic trade-review engine: stock buy, stock sell/trim, ETF review, long call, long put, cash-secured put, and covered-call wrappers all share the same `TradeIntent` pipeline.
  - Confirmed no wheel-only, options-income-only, order-execution, broker-action, automatic-trading, real-provider, TradingAgents, LLM, API route, migration, or frontend code was introduced.
  - Confirmed broker-portfolio freshness and market-quote freshness remain separate in `PortfolioImpact` and the agent-safe projection.
  - Confirmed the accepted pre-Phase-16 boundary exists: `to_agent_safe_projection` strips account identifiers and owner-facing cash values before structured outputs can flow into agents by default.
  - Phase 16 may start. Phase 18 remains blocked on the typed trade-review read schema and covered-call/CSP coverage/collateral caveat or modelling fix.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review tests/services/strategies` -> `41 passed in 0.16s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `320 passed, 92 skipped, 1 deselected in 1.26s`; DB-backed tests skipped because the configured database was unavailable or not marked safe for destructive tests.
