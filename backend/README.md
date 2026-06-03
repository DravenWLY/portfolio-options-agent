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
pip install -e ".[dev]"     # editable install + test/dev tooling (pytest, httpx)
uvicorn app.main:app --reload
```

Dependencies are declared in `pyproject.toml` (PEP 621). Install variants:

- `pip install .` — core runtime only (lean, offline, mock-default).
- `pip install -e ".[dev]"` — editable + test/dev tooling.
- `pip install ".[live-llm]"` — adds the optional, backend-only live LLM provider
  SDKs (`google-generativeai`, `openai`); only needed to run a real live-provider
  smoke. See `docs/claude-e-agentic/LLM_PROVIDER_SMOKE_TEST.md`.

`uv.lock` is the reproducibility lockfile for backend dependencies. When
`pyproject.toml` changes, regenerate it from `backend/`:

```bash
uv lock
```

The backend Docker image exports locked core runtime dependencies from
`uv.lock` with `uv export --frozen --no-dev --no-emit-project`, then installs the
project itself without re-resolving dependencies. The default image does not
install the `live-llm` extra; live-provider SDKs remain local opt-in only.

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
