# Codex C Backend Working Context

Use this file as the short backend implementation context before starting work. The previous generic agent-context folder was removed; role-specific briefs now live under agent folders.

## Current Active Phase

Phase 17 - TradingAgents/Public Research Evidence Adapter.

Phase 17 goal: add optional public ticker/company research evidence plumbing without making TradingAgents the portfolio-aware decision engine.

Important architecture concern: Phase 17 must remain optional, async, public-evidence-only, and absent from the fast deterministic trade-review path. Do not send raw holdings, account values, cash, broker account ids, provider ids, trade journal entries, account-specific thresholds, or other private portfolio context to TradingAgents/public evidence roles by default.

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

## Phase 17 Scope

- Detect optional TradingAgents availability lazily; app features must work without it installed.
- Define public ticker/company research interfaces and mocked parsers only.
- Keep account-level portfolio, collateral, option-risk, actionability, and final conclusions owned by app services and Phase 16 orchestrator outputs.
- Send only sanitized public research context where possible.
- Do not import TradingAgents during FastAPI startup.

Not in Phase 17: frontend trade-review workspace, real market provider integration, broker order execution, automatic trading, trade execution UI, or private portfolio context in public evidence prompts/cache keys.
