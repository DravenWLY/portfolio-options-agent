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
  - `docs/implementation_plan.md`
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
  - `docs/implementation_plan.md`
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
  - `docs/implementation_plan.md`
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
  - `docs/implementation_plan.md`
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
- Verification notes:
  - Changed files: `backend/app/schemas/portfolio.py`, `backend/app/services/portfolio/summary.py`, `backend/tests/api/test_portfolio.py`, `backend/tests/api/test_portfolio_summary.py`, `backend/tests/services/test_portfolio_summary.py`, and `docs/implementation_plan.md`.
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
  - `docs/implementation_plan.md`
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
  - Changed files: `backend/app/api/routes/broker_sync.py`, `backend/app/schemas/broker_sync_api.py`, `backend/app/services/broker_import/freshness.py`, `backend/tests/api/test_broker_sync_freshness.py`, and `docs/implementation_plan.md`.
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
- Verification notes:
  - Changed files: `backend/app/schemas/portfolio.py`, `backend/app/services/portfolio/summary.py`, `backend/app/services/portfolio/warnings.py`, `backend/tests/api/test_portfolio.py`, `backend/tests/api/test_portfolio_summary.py`, `backend/tests/services/test_portfolio_summary.py`, `backend/tests/services/test_portfolio_warnings.py`, and `docs/implementation_plan.md`.
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
- Verification notes:
  - Changed files: `backend/tests/api/test_portfolio_dashboard_backend.py`, `backend/tests/services/test_portfolio_warnings.py`, and `docs/implementation_plan.md`.
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
  - `docs/implementation_plan.md`
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
  - Changed files: `backend/app/api/routes/broker_sync.py`, `backend/app/services/broker_import/freshness.py`, `backend/app/services/portfolio/warnings.py`, `backend/app/services/portfolio/summary.py`, `backend/app/schemas/portfolio.py`, `backend/tests/regression/test_portfolio_summary_regressions.py`, `backend/tests/api/test_broker_sync_freshness.py`, `backend/tests/api/test_broker_sync_foundation.py`, `backend/tests/api/test_manual_portfolio_summary.py`, `backend/tests/api/test_portfolio.py`, `backend/tests/api/test_portfolio_dashboard_backend.py`, `backend/tests/services/test_portfolio_summary.py`, `backend/tests/services/test_portfolio_warnings.py`, `backend/tests/unit/test_broker_sync_statuses.py`, and `docs/implementation_plan.md`.
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
- Verification notes:
  - Changed files: `backend/tests/api/test_manual_portfolio_entry.py` and `docs/implementation_plan.md`.
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
- Verification notes:
  - Changed files: `backend/app/services/broker_import/fidelity_csv.py`, `backend/app/api/routes/imports.py`, `backend/app/main.py`, `backend/tests/services/test_fidelity_csv_import.py`, and `docs/implementation_plan.md`.
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
- Verification notes:
  - Changed files: `backend/tests/fixtures/fidelity_positions_demo.csv`, `backend/tests/fixtures/fidelity_transactions_demo.csv`, `backend/tests/README.md`, and `docs/implementation_plan.md`.
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
- Verification notes:
  - Changed files: `backend/tests/api/test_portfolio_fallbacks.py`, `backend/tests/services/test_import_fallbacks.py`, and `docs/implementation_plan.md`.
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
  - `docs/implementation_plan.md`
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
  - Changed files: `.gitignore`, `backend/app/api/routes/imports.py`, `backend/app/services/broker_import/fidelity_csv.py`, `backend/app/services/broker_import/freshness.py`, `backend/app/services/portfolio/warnings.py`, `backend/tests/api/test_broker_sync_foundation.py`, `backend/tests/api/test_broker_sync_freshness.py`, `backend/tests/api/test_manual_portfolio_summary.py`, `backend/tests/api/test_portfolio_fallbacks.py`, `backend/tests/api/test_snaptrade_import_smoke.py`, `backend/tests/services/test_fidelity_csv_import.py`, `backend/tests/services/test_portfolio_warnings.py`, `backend/tests/unit/test_broker_sync_statuses.py`, and `docs/implementation_plan.md`.
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
  - `docs/implementation_plan.md`
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
  - Changed files: `backend/app/models/report_thread.py`, `backend/app/models/__init__.py`, `backend/alembic/versions/0012_create_report_threads.py`, `backend/tests/conftest.py`, `backend/tests/db/test_report_threads.py`, and `docs/implementation_plan.md`.
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
  - `docs/implementation_plan.md`
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
  - Changed files: `backend/app/models/report_message.py`, `backend/app/models/__init__.py`, `backend/alembic/versions/0013_create_report_messages.py`, `backend/tests/conftest.py`, `backend/tests/db/test_report_messages.py`, and `docs/implementation_plan.md`.
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
  - `docs/implementation_plan.md`
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
  - Changed files: `backend/app/models/agent_run.py`, `backend/app/models/__init__.py`, `backend/alembic/versions/0014_create_agent_runs.py`, `backend/tests/conftest.py`, `backend/tests/db/test_agent_runs.py`, and `docs/implementation_plan.md`.
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
  - `docs/implementation_plan.md`
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
  - `docs/implementation_plan.md`
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
  - `docs/implementation_plan.md`
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
  - `docs/implementation_plan.md`
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
  - `docs/implementation_plan.md`
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
- `GET /option-contracts/{id}` backend gap noted in `docs/deferred_items.md` (contract columns fall back to "—" silently if route is missing).

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
- `GET /option-contracts/{id}` — OptionPositionsView lazy-fetches contract details; not confirmed to exist. Noted in `docs/deferred_items.md`.
- `POST /broker-accounts/{id}/sync` 409 conflict response shape: `{ sync_run_id, status }`. Frontend handles this; Codex should verify the JSON body matches `broker_sync.py:158–162`.

- Status: `done`

