# Codex C Backend Working Context

Use this file as the short backend implementation context before starting work. The previous generic agent-context folder was removed; role-specific briefs now live under agent folders.

## Current Active Phase

Phase 16 - Custom Portfolio-Aware Agent Orchestrator.

Goal: build workflow-first, deterministic-first agents that consume structured trade-review outputs and optionally ask an LLM to explain, summarize, or debate already-computed facts.

Important near-term architecture concern: before agents produce polished account-specific outputs, broker portfolio snapshot freshness/actionability should be explicit. Fresh market quotes plus stale broker holdings can create confidently wrong cash, collateral, coverage, assignment, concentration, or allocation conclusions.

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

## Phase 16 Scope

- Custom agents consume structured deterministic outputs; they do not compute metrics from scratch.
- LLM boundary remains mocked by default.
- Use Phase 15's agent-safe projection for trade-review outputs by default.
- No private brokerage data is sent to LLMs by default.
- TradingAgents remains out of the fast path.

Not in Phase 16: TradingAgents integration, frontend trade-review workspace, real market provider integration, broker order execution, automatic trading, or trade execution UI.
