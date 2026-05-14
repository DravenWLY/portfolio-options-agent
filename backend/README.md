# Backend

FastAPI backend for `portfolio-options-agent`.

## Current Status

Only a minimal health check endpoint exists.

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

The backend does not connect to PostgreSQL yet. SQLAlchemy and Alembic will be added in later implementation tasks.

## Database Migrations

Alembic is configured, but no business tables exist yet.

From the `backend/` directory:

```bash
alembic upgrade head
```

There are no migration revisions yet, so downgrade has nothing to apply until the first schema migration is created.

## Test

```bash
pytest
```
