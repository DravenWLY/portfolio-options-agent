# Codex Working Context

Use this file as the short implementation context before starting work.

## Current Active Phase

Phase 12 - Market Data Contracts and Manual Provider.

Goal: define provider-agnostic quote and option-chain interfaces, keeping broker freshness strictly separate from market quote freshness. Introduce a manual/mock provider — no real market API calls by default.

## Current Backend Foundation

Implemented:

- FastAPI backend.
- PostgreSQL, SQLAlchemy, Alembic.
- Users and accounts.
- Internal portfolio storage for cash, stock positions, option contracts, and option positions.
- Portfolio summary and broker freshness.
- SnapTrade-first read-only broker sync foundation, mock-first.
- Manual input and Fidelity CSV preview fallback.
- Report/agent persistence foundation with:
  - `report_threads`
  - `report_messages`
  - `agent_runs`
  - `agent_steps`
  - report create/list/detail APIs
  - deterministic markdown report output

## Implementation Rules

- Work one task at a time.
- Read only the current task section from `docs/implementation_plan.md`.
- Do not load `docs/completed_phases_log.md` unless historical verification details are required.
- Do not read `.env` or private configs.
- Do not modify `../TradingAgents`.
- Do not add real account data, API keys, broker CSVs, or private strategy thresholds.
- Treat real SnapTrade/Fidelity brokerage data as out of scope for agent inspection by default.
- Do not query local DB/API/browser screens/logs if they may expose real balances, holdings, transactions, account identifiers, provider account IDs, raw provider payloads, SnapTrade user IDs, user secrets, portal URLs, or generated reports.
- If real brokerage data seems necessary, stop and ask for explicit narrow permission; prefer redacted or synthetic output.
- Run relevant tests before marking a task done.
- Update the current task verification notes.
- Do not commit automatically unless the user asks.

## Default Backend Commands

```bash
cd backend && ./.venv/bin/python -m pytest
cd backend && ./.venv/bin/alembic current
cd backend && ./.venv/bin/alembic upgrade head
```

## Completed Frontend Foundation (Phase 11)

Phase 11 delivered the full dashboard shell. All P11-T1 through P11-T7 are done.

Delivered:
- React/Vite shell, user/account selector, portfolio summary.
- Cash/stock/option positions views.
- Broker freshness bar and warnings panel.
- Report history placeholder.
- Broker connection UI at `/broker` (P11-T7) — read-only SnapTrade/Fidelity flow using only existing backend endpoints.

Not included (deferred to later phases): market quote UI, option screener, TradingAgents UI, trade execution UI.

## Phase 12 Scope

- `backend/app/services/market_data/` — MarketDataProvider and OptionDataProvider interfaces.
- Quote freshness model (`freshness_scope="market_quote"`, separate from broker freshness).
- Market quote response models.
- Manual/mock provider (deterministic, no real API calls).
- Mocked market data tests.
- Import-boundary test: market_data must not import from broker_import.

Not in Phase 12: real provider integrations, frontend market quote UI, option screener, TradingAgents.
