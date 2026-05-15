# Backend Testing Guide

This backend uses `pytest` as the main test runner. Tests must be deterministic by default and use synthetic data only.

## Test Categories

- `unit`: Fast tests for pure functions, schemas, models, and deterministic calculations.
- `api`: FastAPI route tests using `TestClient`.
- `db`: Database-backed tests. These should skip cleanly if the local test database is unavailable.
- `migration`: Alembic upgrade/downgrade verification tests.
- `integration`: Cross-layer tests that still avoid real external services unless explicitly marked.
- `adapter`: Contract tests for broker, market-data, LLM, and TradingAgents adapters.
- `regression`: Tests added for fixed bugs so they do not return.
- `external`: Tests that require real external services. These are excluded by default.
- `slow`: Tests that are intentionally slower. These are excluded by default.
- `smoke`: Small high-signal tests for basic application health.

## When to Write Tests

- Write unit tests for deterministic finance calculations, schema validation, provider contracts, and business rules.
- Write API tests for every route that is added or changed.
- Write DB or migration tests for database schema changes and Alembic revisions.
- Write regression tests for every bug fix that changes behavior.
- Write adapter tests with mocked external dependencies by default.

## External Calls

Default tests must not call real brokers, market-data providers, LLM providers, or TradingAgents. Mock those boundaries unless a test is explicitly marked `external` or `integration` and the user has opted into running it.

Tests must not require real OpenAI, Claude, Gemini, Tradier, Alpaca, Fidelity, or broker credentials.

## Synthetic Data Only

Use demo users, demo accounts, fake keys, placeholder symbols, and synthetic reports. Do not use real holdings, real account values, real reports, real broker files, or private strategy thresholds in tests.

## Commands

Run the default test suite:

```bash
cd backend && pytest
```

If global Python plugins interfere with local pytest startup, run the project virtual environment directly:

```bash
cd backend && ./.venv/bin/python -m pytest
```

Run unit tests:

```bash
cd backend && pytest -m unit
```

Run API tests:

```bash
cd backend && pytest -m api
```

Run the default marker expression explicitly:

```bash
cd backend && pytest -m "not external and not slow"
```

Run regression tests:

```bash
cd backend && pytest -m regression
```

Run external tests only if they are intentionally added later, credentials are configured outside the repository, and the user explicitly approves that run:

```bash
cd backend && pytest -m external
```

External broker-provider tests must never read or print `.env`, `.env.*`, broker credentials, API keys, account data, or provider secrets. SnapTrade tests in the default suite must use mocked clients only; any real-provider coverage belongs behind the `external` marker and should stay skipped until a safe external-test plan is approved.
