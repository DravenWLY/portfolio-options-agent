# Backend

FastAPI backend for `portfolio-options-agent`.

## Current Status

The backend currently includes:

- FastAPI health check endpoint.
- PostgreSQL configuration through Docker Compose.
- SQLAlchemy session setup.
- Alembic migrations for users, accounts, cash balances, stock positions, option contracts, and option positions.
- Basic users/accounts API routes.
- Internal portfolio storage routes for cash, stock/ETF positions, option positions, and portfolio summary.

Broker sync, market data providers, deterministic option/risk engines, TradingAgents integration, and frontend application code are not implemented yet.

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Local PostgreSQL

From the repository root:

```bash
docker compose up -d postgres
docker compose ps postgres
```

Stop the database:

```bash
docker compose stop postgres
```

Remove the database container and local development volume:

```bash
docker compose down -v
```

The backend uses PostgreSQL for local development. Keep `.env` private and use `.env.example` only for placeholder variable names.

## Database Migrations

From the `backend/` directory:

```bash
./.venv/bin/alembic upgrade head
./.venv/bin/alembic current
```

Use downgrade commands only when intentionally testing or rolling back local development schema changes.

## Test

```bash
./.venv/bin/python -m pytest
```
