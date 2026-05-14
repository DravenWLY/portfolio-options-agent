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
  - `docker compose up -d postgres` was attempted, but Docker reported that it could not connect to the Docker daemon at `unix:///Users/wulingyun/.docker/run/docker.sock`.
  - `docker compose --env-file .env.example config` passed, confirming the Compose file renders with safe placeholder values.
  - `pytest` from the ambient Python environment failed before collecting project tests because of a broken global `pydantic_core`/pytest plugin architecture mismatch.
  - `cd backend && ./.venv/bin/python -m pytest` passed: 1 test passed.
  - To finish Docker verification after starting Docker Desktop, run `docker compose up -d postgres` and `docker compose ps postgres` from the repository root.
- Status: `blocked`

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
- Status: `not_started`

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
- Status: `not_started`

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
- Status: `not_started`

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
- Status: `not_started`

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
- Status: `not_started`

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
- Status: `not_started`

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
- Status: `not_started`

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
- Status: `not_started`

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
- Status: `not_started`

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
- Status: `not_started`

## Phase 3 - Portfolio Core

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
- Status: `not_started`

### P3-T2 - Stock Positions

- Task id: `P3-T2`
- Title: stock positions
- Objective: Add manually entered stock/ETF positions.
- Files expected to change:
  - `backend/app/models/stock_position.py`
  - `backend/app/schemas/stock_position.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T1`
- Implementation steps:
  1. Add stock position model.
  2. Add create/update/delete endpoints.
  3. Keep data account-scoped.
- Acceptance criteria:
  - Positions can be managed without broker integration.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove model/schema/routes and migration.
- Status: `not_started`

### P3-T3 - Option Contracts

- Task id: `P3-T3`
- Title: option contracts
- Objective: Normalize option contract identity for positions and quotes.
- Files expected to change:
  - `backend/app/models/option_contract.py`
  - `backend/app/schemas/option_contract.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T2`
- Implementation steps:
  1. Add OCC symbol, underlying, expiration, strike, type, multiplier.
  2. Add uniqueness on OCC symbol.
  3. Add validation tests for basic contract fields.
- Acceptance criteria:
  - Option contracts can be created or resolved idempotently.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove contract model/schema/migration.
- Status: `not_started`

### P3-T4 - Option Positions

- Task id: `P3-T4`
- Title: option positions
- Objective: Add account-scoped option positions linked to option contracts.
- Files expected to change:
  - `backend/app/models/option_position.py`
  - `backend/app/schemas/option_position.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T3`
- Implementation steps:
  1. Add option position model.
  2. Support long/short quantity and status.
  3. Add API for manual option position entry.
- Acceptance criteria:
  - Option positions belong to accounts and contracts.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove option position model/schema/API and migration.
- Status: `not_started`

### P3-T5 - Portfolio Summary Service

- Task id: `P3-T5`
- Title: portfolio summary service
- Objective: Compute a deterministic account portfolio summary from cash, stocks, and options.
- Files expected to change:
  - `backend/app/services/portfolio/summary.py`
  - `backend/app/schemas/portfolio.py`
  - `backend/app/api/routes/portfolio.py`
  - `backend/tests/services/test_portfolio_summary.py`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T4`
- Implementation steps:
  1. Define input/output dataclasses or schemas.
  2. Compute total cash, position values, and basic exposure fields.
  3. Avoid market data dependency until Phase 6.
- Acceptance criteria:
  - Synthetic fixtures produce expected summary values.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove summary service, route changes, and tests.
- Status: `not_started`

### P3-T6 - Portfolio Core Tests

- Task id: `P3-T6`
- Title: portfolio core tests
- Objective: Ensure cash, stock, option, and summary flows work together.
- Files expected to change:
  - `backend/tests/api/test_portfolio.py`
  - `backend/tests/services/test_portfolio_summary.py`
  - `docs/implementation_plan.md`
- Dependencies: `P3-T5`
- Implementation steps:
  1. Add end-to-end API tests for manual portfolio entry.
  2. Add service tests for summary calculations.
  3. Validate account ownership boundaries.
- Acceptance criteria:
  - Portfolio core is covered by API and service tests.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove portfolio tests and fixtures.
- Status: `not_started`

## Phase 4 - Deterministic Option/Risk Engine

### P4-T1 - Option Formulas

- Task id: `P4-T1`
- Title: option formulas
- Objective: Add deterministic option formula utilities for premium yield, annualized ROI, breakeven, spread, downside buffer, and premium capture.
- Files expected to change:
  - `backend/app/services/options/formulas.py`
  - `backend/tests/services/options/test_formulas.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 3 complete.
- Implementation steps:
  1. Add pure functions using `Decimal` where appropriate.
  2. Document assumptions in docstrings.
  3. Add synthetic tests with known expected outputs.
- Acceptance criteria:
  - LLMs are not involved in metric calculation.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove formulas module and tests.
- Status: `not_started`

### P4-T2 - Collateral/Free Cash Calculation

- Task id: `P4-T2`
- Title: collateral/free cash calculation
- Objective: Calculate short-put collateral usage and free cash after collateral.
- Files expected to change:
  - `backend/app/services/risk/collateral.py`
  - `backend/tests/services/risk/test_collateral.py`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T1`
- Implementation steps:
  1. Identify short put positions.
  2. Calculate required collateral from strike, multiplier, and contracts.
  3. Calculate free cash after collateral.
- Acceptance criteria:
  - Synthetic short-put examples produce expected collateral values.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove collateral module and tests.
- Status: `not_started`

### P4-T3 - Covered Call Eligibility

- Task id: `P4-T3`
- Title: covered call eligibility
- Objective: Determine whether stock positions support covered calls.
- Files expected to change:
  - `backend/app/services/options/covered_calls.py`
  - `backend/tests/services/options/test_covered_calls.py`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T1`
- Implementation steps:
  1. Count eligible 100-share lots by symbol.
  2. Account for existing short calls if modeled.
  3. Return deterministic eligibility and warnings.
- Acceptance criteria:
  - Eligibility is computed without LLM involvement.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove covered-call module and tests.
- Status: `not_started`

### P4-T4 - Assignment Scenario

- Task id: `P4-T4`
- Title: assignment scenario
- Objective: Project cash and allocation after hypothetical short-put assignment.
- Files expected to change:
  - `backend/app/services/risk/assignment.py`
  - `backend/app/schemas/assignment.py`
  - `backend/tests/services/risk/test_assignment.py`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T2`
- Implementation steps:
  1. Convert selected short puts into hypothetical stock positions.
  2. Reduce cash by assignment exposure.
  3. Return projected cash and exposures.
- Acceptance criteria:
  - Assignment projections are repeatable and traceable.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove assignment module, schema, and tests.
- Status: `not_started`

### P4-T5 - Deterministic Option/Risk Tests

- Task id: `P4-T5`
- Title: deterministic option/risk tests
- Objective: Add combined tests covering formulas, collateral, covered calls, and assignment scenarios.
- Files expected to change:
  - `backend/tests/services/options/*`
  - `backend/tests/services/risk/*`
  - `docs/implementation_plan.md`
- Dependencies: `P4-T4`
- Implementation steps:
  1. Add synthetic fixtures.
  2. Add regression tests for edge cases.
  3. Ensure no real account values appear in fixtures.
- Acceptance criteria:
  - Deterministic engine behavior is covered before exposing routes.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove combined tests/fixtures.
- Status: `not_started`

## Phase 5 - Reports and Agent Run History

### P5-T1 - report_threads

- Task id: `P5-T1`
- Title: report_threads
- Objective: Add database model for chat-like report thread containers.
- Files expected to change:
  - `backend/app/models/report_thread.py`
  - `backend/app/schemas/report_thread.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: Phase 2 complete.
- Implementation steps:
  1. Add user/account-linked report thread model.
  2. Add status, title, tags, timestamps, and soft delete.
  3. Generate migration.
- Acceptance criteria:
  - Report threads are account/user-scoped and soft deletable.
- Tests to run:
  - `cd backend && pytest`
  - `cd backend && alembic upgrade head`
- Rollback notes:
  - Downgrade migration and remove model/schema.
- Status: `not_started`

### P5-T2 - report_messages

- Task id: `P5-T2`
- Title: report_messages
- Objective: Add ordered report messages for user input, system events, agent output, errors, and final reports.
- Files expected to change:
  - `backend/app/models/report_message.py`
  - `backend/app/schemas/report_message.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T1`
- Implementation steps:
  1. Add thread-linked message model.
  2. Include message type, markdown content, JSON payload, sequence, and soft delete.
  3. Add ordering constraints.
- Acceptance criteria:
  - Messages are ordered and tied to one thread.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove message model/schema/migration.
- Status: `not_started`

### P5-T3 - agent_runs

- Task id: `P5-T3`
- Title: agent_runs
- Objective: Add run metadata for deterministic and LLM-backed analyses.
- Files expected to change:
  - `backend/app/models/agent_run.py`
  - `backend/app/schemas/agent_run.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T1`
- Implementation steps:
  1. Add run type, status, budgets, provider/model summary, and error fields.
  2. Link run to user/account/thread where available.
  3. Generate migration.
- Acceptance criteria:
  - Runs can represent queued/running/completed/failed states.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove run model/schema/migration.
- Status: `not_started`

### P5-T4 - agent_steps

- Task id: `P5-T4`
- Title: agent_steps
- Objective: Add per-step trace records for analysis progress, retries, token usage, and errors.
- Files expected to change:
  - `backend/app/models/agent_step.py`
  - `backend/app/schemas/agent_step.py`
  - `backend/alembic/versions/*`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T3`
- Implementation steps:
  1. Add run-linked ordered steps.
  2. Include input/output JSON snapshots, status, timing, usage, and error data.
  3. Add uniqueness on run/step order.
- Acceptance criteria:
  - Agent run progress can be reconstructed from stored steps.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove step model/schema/migration.
- Status: `not_started`

### P5-T5 - Markdown Report Output

- Task id: `P5-T5`
- Title: markdown report output
- Objective: Generate markdown report content from deterministic report messages.
- Files expected to change:
  - `backend/app/services/reports/markdown.py`
  - `backend/app/api/routes/reports.py`
  - `backend/tests/services/reports/test_markdown.py`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T2`
- Implementation steps:
  1. Add markdown rendering service.
  2. Add export endpoint for markdown.
  3. Use synthetic test report data.
- Acceptance criteria:
  - Markdown export is deterministic and contains no private fixture data.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove markdown service, route, and tests.
- Status: `not_started`

### P5-T6 - Delete/Restore Behavior

- Task id: `P5-T6`
- Title: delete/restore behavior
- Objective: Add soft delete, restore, and permanent delete behavior for report threads.
- Files expected to change:
  - `backend/app/services/reports/deletion.py`
  - `backend/app/api/routes/reports.py`
  - `backend/tests/api/test_report_deletion.py`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T5`
- Implementation steps:
  1. Implement soft delete and restore.
  2. Implement permanent purge for sensitive content.
  3. Add audit-log placeholder or explicit TODO if audit table is not present.
- Acceptance criteria:
  - Deleted reports are hidden by default.
  - Restored reports reappear.
  - Permanent delete removes sensitive content.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove deletion service/route changes/tests.
- Status: `not_started`

### P5-T7 - Reports and Agent Run Tests

- Task id: `P5-T7`
- Title: reports and agent run tests
- Objective: Cover report threads, messages, runs, steps, export, and deletion lifecycle.
- Files expected to change:
  - `backend/tests/api/test_reports.py`
  - `backend/tests/api/test_agent_runs.py`
  - `backend/tests/services/reports/*`
  - `docs/implementation_plan.md`
- Dependencies: `P5-T6`
- Implementation steps:
  1. Add API tests for report lifecycle.
  2. Add service tests for markdown and deletion.
  3. Add run/step status tests.
- Acceptance criteria:
  - Report and run history are test-covered before LLM integration.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove report/agent tests and fixtures.
- Status: `not_started`

## Phase 6 - Market Data Interface

### P6-T1 - MarketDataProvider Interface

- Task id: `P6-T1`
- Title: MarketDataProvider interface
- Objective: Define provider-agnostic stock quote and intraday bar interfaces.
- Files expected to change:
  - `backend/app/services/market_data/interfaces.py`
  - `backend/app/services/market_data/models.py`
  - `backend/tests/services/market_data/test_interfaces.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 1 complete.
- Implementation steps:
  1. Define protocol or abstract base class.
  2. Define quote/bar data structures with provider and timestamps.
  3. Avoid real provider calls.
- Acceptance criteria:
  - Interfaces are importable and testable without network.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove interface/model/test files.
- Status: `not_started`

### P6-T2 - OptionDataProvider Interface

- Task id: `P6-T2`
- Title: OptionDataProvider interface
- Objective: Define option expirations, chain, snapshot, and quote stream interfaces.
- Files expected to change:
  - `backend/app/services/market_data/interfaces.py`
  - `backend/app/services/market_data/models.py`
  - `backend/tests/services/market_data/test_option_interfaces.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T1`
- Implementation steps:
  1. Add option provider protocol.
  2. Define option chain and option quote structures.
  3. Include IV/Greeks fields and freshness metadata.
- Acceptance criteria:
  - Option data models can represent provider-supplied or calculated Greeks.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Revert option interface additions.
- Status: `not_started`

### P6-T3 - ManualProvider

- Task id: `P6-T3`
- Title: ManualProvider
- Objective: Add a provider for manually entered quotes and synthetic tests.
- Files expected to change:
  - `backend/app/services/market_data/manual_provider.py`
  - `backend/tests/services/market_data/test_manual_provider.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T2`
- Implementation steps:
  1. Implement provider using in-memory or explicit input data.
  2. Mark freshness based on supplied timestamps.
  3. Add synthetic tests.
- Acceptance criteria:
  - Deterministic tests can run without network or API keys.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove manual provider and tests.
- Status: `not_started`

### P6-T4 - Low-Cost Fallback Provider

- Task id: `P6-T4`
- Title: YFinance or other low-cost fallback provider
- Objective: Add one low-cost fallback provider behind the interface without treating it as production-grade live OPRA data.
- Files expected to change:
  - `backend/app/services/market_data/yfinance_provider.py`
  - `backend/requirements.txt` or future `backend/pyproject.toml`
  - `backend/tests/services/market_data/test_yfinance_provider.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T3`
- Implementation steps:
  1. Add provider adapter with clear data-mode labels.
  2. Keep network tests mocked by default.
  3. Document limitations and freshness behavior.
- Acceptance criteria:
  - Provider can be mocked in tests.
  - UI/API consumers can see delayed/stale/EOD status.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove provider, dependency, and tests.
- Status: `not_started`

### P6-T5 - Quote Freshness Model

- Task id: `P6-T5`
- Title: quote freshness model
- Objective: Centralize live/delayed/stale/EOD freshness classification.
- Files expected to change:
  - `backend/app/services/market_data/freshness.py`
  - `backend/tests/services/market_data/test_freshness.py`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T1`
- Implementation steps:
  1. Define freshness statuses.
  2. Implement timestamp and provider-mode based classification.
  3. Add edge-case tests.
- Acceptance criteria:
  - Stale data is never labeled immediately actionable.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove freshness module and tests.
- Status: `not_started`

### P6-T6 - Market Data Tests

- Task id: `P6-T6`
- Title: market data tests
- Objective: Add coverage for provider interfaces, manual provider, fallback provider mocks, and freshness logic.
- Files expected to change:
  - `backend/tests/services/market_data/*`
  - `docs/implementation_plan.md`
- Dependencies: `P6-T5`
- Implementation steps:
  1. Add tests for provider contracts.
  2. Add tests for fallback behavior.
  3. Add stale quote warning tests.
- Acceptance criteria:
  - Market data layer is safe to use without real credentials.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove market data tests and fixtures.
- Status: `not_started`

## Phase 7 - TradingAgents Adapter

### P7-T1 - Optional Dependency Detection

- Task id: `P7-T1`
- Title: optional dependency detection
- Objective: Detect whether TradingAgents is installed without requiring it for core app startup.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/versioning.py`
  - `backend/app/services/tradingagents_adapter/exceptions.py`
  - `backend/tests/services/test_tradingagents_detection.py`
  - `docs/implementation_plan.md`
- Dependencies: Phase 1 complete.
- Implementation steps:
  1. Use lazy import detection.
  2. Return version/status without importing at app startup.
  3. Add tests for installed/missing cases with monkeypatch.
- Acceptance criteria:
  - App works when TradingAgents is absent.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove detection modules and tests.
- Status: `not_started`

### P7-T2 - Adapter Interface

- Task id: `P7-T2`
- Title: adapter interface
- Objective: Define app-owned TradingAgents adapter methods and request/result models.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/client.py`
  - `backend/app/services/tradingagents_adapter/models.py`
  - `backend/tests/services/test_tradingagents_adapter_interface.py`
  - `docs/implementation_plan.md`
- Dependencies: `P7-T1`
- Implementation steps:
  1. Define run methods and parsed output models.
  2. Keep TradingAgents imports hidden inside adapter implementation.
  3. Add interface tests.
- Acceptance criteria:
  - Rest of app depends only on adapter models, not upstream internals.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove adapter interface modules and tests.
- Status: `not_started`

### P7-T3 - Missing Dependency Fallback

- Task id: `P7-T3`
- Title: missing dependency fallback
- Objective: Provide clear actionable errors when TradingAgents is not installed.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/client.py`
  - `backend/app/services/tradingagents_adapter/exceptions.py`
  - `backend/tests/services/test_tradingagents_missing.py`
  - `docs/implementation_plan.md`
- Dependencies: `P7-T2`
- Implementation steps:
  1. Raise app-owned exception on missing dependency.
  2. Include local editable install and optional extra instructions.
  3. Confirm deterministic features are unaffected.
- Acceptance criteria:
  - Missing TradingAgents error is understandable and non-fatal to app startup.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Revert fallback exception and tests.
- Status: `not_started`

### P7-T4 - Mocked Adapter Tests

- Task id: `P7-T4`
- Title: mocked adapter tests
- Objective: Test adapter behavior with fake TradingAgents outputs.
- Files expected to change:
  - `backend/tests/services/test_tradingagents_mocked.py`
  - `backend/app/services/tradingagents_adapter/parser.py`
  - `docs/implementation_plan.md`
- Dependencies: `P7-T3`
- Implementation steps:
  1. Create fake final state fixture.
  2. Parse into report-thread draft output.
  3. Verify errors and missing keys are handled.
- Acceptance criteria:
  - Adapter parser works without real LLM calls or API keys.
- Tests to run:
  - `cd backend && pytest`
- Rollback notes:
  - Remove parser and mocked tests.
- Status: `not_started`

### P7-T5 - Later Real Integration

- Task id: `P7-T5`
- Title: later real integration
- Objective: Add optional real TradingAgents run support after mocked adapter is stable.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/client.py`
  - optional dependency configuration
  - `backend/tests/integration/test_tradingagents_real.py`
  - `docs/implementation_plan.md`
- Dependencies: `P7-T4`
- Implementation steps:
  1. Add optional dependency declaration.
  2. Support local editable install.
  3. Run only optional integration tests when dependency and API keys are explicitly available.
  4. Never read or print `.env`.
- Acceptance criteria:
  - Real integration is optional and skipped by default in CI/local tests.
- Tests to run:
  - `cd backend && pytest`
  - Optional integration command to be documented later.
- Rollback notes:
  - Remove optional dependency and real integration path.
- Status: `not_started`

## Phase 8 - Frontend MVP

### P8-T1 - Account Selector

- Task id: `P8-T1`
- Title: account selector
- Objective: Add a local user/account selection screen for MVP navigation.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/package.json`
  - `docs/implementation_plan.md`
- Dependencies: Phase 2 routes available.
- Implementation steps:
  1. Initialize frontend tooling only when this task is approved.
  2. Add account selector UI backed by users/accounts APIs.
  3. Keep auth local/dev only.
- Acceptance criteria:
  - User can select a synthetic/local account.
- Tests to run:
  - frontend test command selected during frontend setup.
- Rollback notes:
  - Remove frontend scaffold and package files if needed.
- Status: `not_started`

### P8-T2 - Account Dashboard

- Task id: `P8-T2`
- Title: account dashboard
- Objective: Display account-level cash, positions, and summary cards.
- Files expected to change:
  - `frontend/src/pages/*`
  - `frontend/src/components/*`
  - `docs/implementation_plan.md`
- Dependencies: `P8-T1`, Phase 3 APIs.
- Implementation steps:
  1. Fetch account portfolio summary.
  2. Display key values and warnings.
  3. Avoid marketing-style UI.
- Acceptance criteria:
  - Dashboard displays synthetic account summary.
- Tests to run:
  - frontend tests and/or Playwright smoke test.
- Rollback notes:
  - Remove dashboard page/components.
- Status: `not_started`

### P8-T3 - Positions Page

- Task id: `P8-T3`
- Title: positions page
- Objective: Add stock/ETF position management UI.
- Files expected to change:
  - `frontend/src/pages/*`
  - `frontend/src/components/*`
  - `docs/implementation_plan.md`
- Dependencies: `P8-T2`
- Implementation steps:
  1. List positions.
  2. Add edit/create/delete forms.
  3. Validate inputs.
- Acceptance criteria:
  - User can manage synthetic/manual positions through UI.
- Tests to run:
  - frontend tests and/or Playwright smoke test.
- Rollback notes:
  - Remove positions UI changes.
- Status: `not_started`

### P8-T4 - Option Positions Page

- Task id: `P8-T4`
- Title: option positions page
- Objective: Add option position entry and review UI.
- Files expected to change:
  - `frontend/src/pages/*`
  - `frontend/src/components/*`
  - `docs/implementation_plan.md`
- Dependencies: `P8-T3`, Phase 3 option APIs.
- Implementation steps:
  1. List option positions.
  2. Add contract/position entry form.
  3. Show collateral-related fields when available.
- Acceptance criteria:
  - User can enter and review synthetic option positions.
- Tests to run:
  - frontend tests and/or Playwright smoke test.
- Rollback notes:
  - Remove option positions UI changes.
- Status: `not_started`

### P8-T5 - Report History Page

- Task id: `P8-T5`
- Title: report history page
- Objective: Add report history list and detail navigation.
- Files expected to change:
  - `frontend/src/pages/*`
  - `frontend/src/components/*`
  - `docs/implementation_plan.md`
- Dependencies: Phase 5 report APIs.
- Implementation steps:
  1. List reports with status and account.
  2. Add filters/search if API supports it.
  3. Add delete/export actions when available.
- Acceptance criteria:
  - User can view old synthetic reports.
- Tests to run:
  - frontend tests and/or Playwright smoke test.
- Rollback notes:
  - Remove report history UI changes.
- Status: `not_started`

### P8-T6 - Agent Run Monitor Page

- Task id: `P8-T6`
- Title: agent run monitor page
- Objective: Add UI for run status, progress, errors, retry notices, token usage, and final report.
- Files expected to change:
  - `frontend/src/pages/*`
  - `frontend/src/components/*`
  - `docs/implementation_plan.md`
- Dependencies: Phase 5 agent run APIs and SSE endpoint.
- Implementation steps:
  1. Connect to run detail API.
  2. Connect to SSE progress stream.
  3. Show current step, errors, usage, and final report.
- Acceptance criteria:
  - User can monitor a synthetic or deterministic analysis run.
- Tests to run:
  - frontend tests and/or Playwright smoke test.
- Rollback notes:
  - Remove run monitor UI changes.
- Status: `not_started`
