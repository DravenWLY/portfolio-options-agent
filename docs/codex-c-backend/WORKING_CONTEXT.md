# Codex C Backend Working Context

Use this file as the short backend implementation context before starting work. The previous generic agent-context folder was removed; role-specific briefs now live under agent folders.

## Current Active Phase

Phase 18B - Frontend Trade Review Workspace expansion.

Phase 18A is complete and archived. The current backend role is to preserve and extend the sanitized trade-review workspace contract only when Phase 18B needs explicit backend support.

Important architecture concern: Claude A must continue to consume a safe backend contract rather than raw deterministic report, portfolio, broker, or agent-run internals. Deep Phase 17 TradingAgents/Public Research Evidence implementation is temporarily frozen.

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
- Market data contracts and manual/mock provider.
- Generic option/risk services.
- TradeIntent foundation for stock, ETF, and options intents.
- Deterministic trade-review engine with payoff, portfolio impact, risk integration, strategy wrappers, deterministic report, and agent-safe projection.
- Phase 16 deterministic agent components and portfolio-aware agent-team orchestrator with actionability enforcement, context envelopes, run/step mapping, privacy-safe fallbacks, and no TradingAgents/LLM/provider calls by default.
- Phase 18A sanitized trade-review workspace read contract, synthetic preview endpoint, first read-only frontend workspace, and integration review.

## Implementation Rules

- Work one task at a time.
- Read only the current task section from `docs/shared/implementation_plan.md`.
- Do not load `docs/shared/completed_phases_log.md` unless historical verification details are required.
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

Phase 11 delivered the full dashboard shell and local security hardening. All Phase 11 tasks are done.

Delivered:
- React/Vite shell, user/account selector, portfolio summary.
- Cash/stock/option positions views.
- Broker freshness bar and warnings panel.
- Report history placeholder.
- Broker connection UI at `/broker` (P11-T7) — read-only SnapTrade/Fidelity flow using only existing backend endpoints.

Not included (deferred to later phases): market quote UI, option screener, TradingAgents UI, trade execution UI.

## Phase 18B Backend Scope

The default Phase 18B owner is frontend/UX, but backend must handle contract fast-follows before new frontend fields are consumed.

Known backend fast-follow:

- Unify the frontend-read forbidden-field key set in `app/services/privacy.py`.
- Import that shared constant from both the Phase 18A mapper and schema validators.
- Keep synthetic tests proving forbidden private/raw keys remain rejected/omitted.

Not in Phase 18B backend support unless explicitly approved: frontend implementation, TradingAgents/Public Research Evidence work, real market provider integration, broker order execution, broker order cancellation, broker disconnect/delete flows, automatic trading, broker scraping, Fidelity credential storage, MFA bypass, option-chain browser, screener, or private portfolio/raw brokerage exposure.
