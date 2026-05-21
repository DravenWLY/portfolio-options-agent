# Phase 18A Frontend Readiness Contract

Status: architecture handoff
Owner: Codex B - Architecture / Systems / Integration
Last updated: 2026-05-20

## Decision

Phase 18A may begin from completed Phase 16 outputs, but only in this order:

1. Codex C adds a typed, sanitized trade-review workspace read contract with synthetic tests and forbidden-field checks.
2. Claude A implements the first visible Trade Review Workspace against that contract.
3. Claude B reviews frontend safety, stale-data clarity, privacy leakage, and implementation quality before the workspace is treated as product-ready.

Recommendation: **PASS** to start Codex C backend readiness work for Phase 18A. **BLOCK** Claude A frontend implementation until the safe read contract exists and passes forbidden-field tests.

Phase 17 deep implementation is temporarily frozen. TradingAgents/Public Research Evidence remains optional later evidence and must not block Phase 18A.

## Purpose

Phase 18A should prove the core product value: a portfolio-aware pre-trade review workspace for manual investors using deterministic calculations, completed Phase 16 agent/orchestrator outputs, and clear freshness/actionability boundaries.

It must not wait for TradingAgents research/debate evidence, real market-data provider integration, or streaming quotes. Manual/mock market data is acceptable for local MVP as long as the UI clearly labels analysis-only, manual, delayed, stale, or unavailable states.

## Allowed MVP Trade Flows

Phase 18A may expose only these proposed manual trade reviews:

- Stock/ETF buy.
- Stock/ETF sell or trim.
- Covered call.
- Cash-secured put.

Long calls, long puts, multi-leg strategies, wheel lifecycle workflows, option-chain browsing, screening, and automated recommendations remain out of the first product surface.

## Minimum Codex C Backend Support

Codex C should implement the smallest backend slice that lets Claude A build against stable fields:

1. Add a frontend-safe read schema, likely `backend/app/schemas/trade_review_workspace.py`.
2. Add a mapper/projection service, likely `backend/app/services/trade_review/frontend_read.py`, that converts deterministic trade-review report data, `PortfolioActionabilityDecision`, and Phase 16 orchestration outputs into the read schema.
3. Add recursive forbidden-field tests covering every response shape.
4. Add synthetic tests for all allowed flows: stock/ETF buy, stock/ETF sell/trim, covered call, and cash-secured put.
5. Add either a small preview/read endpoint or a documented typed fixture route only if it follows existing API patterns cleanly. A likely first endpoint is `POST /api/trade-reviews/preview`; it must not call brokers, real market providers, LLMs, or TradingAgents.
6. Add a visible modelling caveat field for covered-call coverage and CSP collateral unless coverage/collateral netting is fully modelled.

The backend should not add TradingAgents integration, real market-provider calls, DB migrations, broker order actions, or frontend code in this slice.

## Sanitized Read Schema Expectations

The frontend should consume one stable response shape, not raw internal report, portfolio, agent-run, or broker schemas.

Suggested top-level shape:

```text
TradeReviewWorkspaceRead
- review_reference: string
- generated_at: datetime
- calculation_version: string
- supported_flow: stock_buy | stock_sell_trim | etf_buy | etf_sell_trim | covered_call | cash_secured_put
- trade_intent_summary: TradeIntentSummaryRead
- actionability: ReviewActionabilityRead
- deterministic_review: DeterministicTradeReviewRead
- agent_orchestration: Phase16OrchestrationSummaryRead
- report_output: AnalysisOnlyReportRead | null
- caveats: CaveatRead[]
```

`trade_intent_summary` may include only the user-entered proposed intent:

- asset class: `stock`, `etf`, or `option`;
- action or strategy type;
- symbol or underlying symbol;
- proposed quantity/contracts;
- price, strike, premium, expiration, option type, and leg action where applicable;
- support status and unsupported/manual-review reason.

It must not include account ids, broker ids, provider ids, raw option-provider contract ids, raw holdings, current position quantities, cash balances, account values, or trade journal text.

`actionability` must include:

- `review_actionability_status`;
- `language_tier`;
- `can_run_deterministic_review`;
- `can_run_agent_explanation`;
- `requires_user_confirmation`;
- `reasons[]` with code, scope, severity, and safe message;
- separate `broker_snapshot` and `market_quotes` metadata;
- optional `user_confirmation` metadata.

Accepted `review_actionability_status` values remain:

- `normal_review`
- `analysis_only`
- `manual_confirmation_required`
- `blocked_stale_broker_snapshot`
- `blocked_stale_market_quote`
- `blocked_unknown_freshness`
- `blocked_provider_error`

`deterministic_review` should expose structured sections:

- `portfolio_impact`: symbol/underlying affected, exposure direction, exposure value delta if safe, and notes.
- `cash_collateral_impact`: estimated cash change, premium cash change, collateral requirement/change, and free-cash status as a category such as `sufficient`, `insufficient`, `unknown`, or `not_modelled`; do not expose raw current cash or raw free cash.
- `concentration_allocation_impact`: concentration symbol, concentration value delta where safe, allocation/concentration category, and caveats; do not expose total account value or full holdings.
- `options_exposure`: assignment share delta, exercise share delta, call-away share delta, collateral method, coverage/collateral model status, and notes.
- `risk_rule_violations`: code, severity, message, source, metric label, actual display if safe, and threshold label or policy name; do not expose account-specific threshold values by default.
- `missing_data_warnings`: missing broker, market, option, coverage, collateral, quote, Greek/IV, or freshness inputs.
- `scenario_payoff_summary`: scenario labels, underlying assumptions, and scenario P/L if safe; no recommendations.

`agent_orchestration` should be a summary only:

- workflow version;
- stage order/statuses;
- review actionability status;
- source agent names;
- whether report composition ran;
- unavailable/gated reasons for research, LLM, real market provider, or report composition.

It must not expose raw agent step payloads, raw prompts, raw private context envelopes, provider payloads, or account identifiers.

`report_output` may include analysis-only deterministic markdown only if it is generated from the safe read schema or passes the same forbidden-field and prohibited-language checks. The first UI should prefer structured sections over raw markdown rendering.

## Forbidden Fields

These fields, including nested variants, must never appear in the frontend trade-review read contract:

- `account_id`
- `broker_account_id`
- `broker_connection_id`
- `provider_account_id`
- `provider_connection_id`
- `provider_contract_id`
- `provider_authorization_id`
- `account_number`
- `broker_account_number`
- `provider_account_number`
- `snaptrade_user_id`
- `provider_user_id`
- `user_secret`
- `secret_ref`
- `encrypted_secret_ref`
- `consumer_key`
- `access_token`
- `api_key`
- `portal_url`
- `raw_payload`
- `raw_metadata`
- `raw_provider_payload`
- `raw_holdings`
- `raw_positions`
- `positions`
- `holdings`
- `cash`
- `cash_balance`
- `cash_balances`
- `total_cash`
- `available_cash`
- `free_cash`
- `buying_power`
- `reserved_collateral_cash`
- `account_value`
- `account_values`
- `total_account_value`
- `total_internal_value`
- `trade_journal_entries`
- `strategy_settings`
- `account_specific_thresholds`

Allowed derived outputs include proposed trade quantities, proposed trade assumptions, estimated cash change, estimated premium change, estimated collateral change, assignment/exercise/call-away share deltas, and safe risk messages. Do not expose raw current holdings, raw current cash, raw account value, provider account identifiers, or provider raw payloads to make those derived outputs possible.

## Frontend / Backend Boundary

Backend owns:

- validation of supported trade flows;
- deterministic finance calculations;
- broker snapshot freshness;
- market quote freshness;
- actionability status;
- Phase 16 orchestration summaries;
- forbidden-field and prohibited-language checks;
- all broker, market-provider, LLM, and TradingAgents access.

Frontend owns:

- trade intent form state for the four allowed flows;
- read-only rendering of backend response fields;
- loading, empty, error, unavailable, stale, blocked, and manual-confirmation-required states;
- visual separation of deterministic facts, actionability/freshness guardrails, optional agent explanation, and future public research evidence;
- read-only/manual-decision-support language.

Frontend must not:

- invent response fields before backend contract exists;
- compute or recompute financial metrics;
- call brokers, SnapTrade, market providers, LLM providers, or TradingAgents directly;
- store portfolio/review data in localStorage or sessionStorage;
- render order tickets, order buttons, order cancellation, broker disconnect/delete, or execution-like controls.

## Claude B Review Gate

Claude B should review the completed Codex C backend contract before Claude A starts, or review the completed Claude A frontend before Codex B integration sign-off, depending on task sequencing.

Review checkpoints:

- Frontend safety language: no "you should buy/sell", "safe to trade", "ready to trade", or guaranteed-return wording.
- No execution controls: no order ticket, place/submit/send order, cancel order, broker disconnect/delete, or broker credential UI.
- Stale-data clarity: broker snapshot freshness and market quote freshness are visually separate; actionability status is clear.
- Private-data leakage: read response and frontend state omit forbidden fields recursively.
- UX clarity: deterministic facts, agent explanation, and future research evidence are visually separate.
- Implementation quality: typed API client, loading/error/empty states, no speculative fields, no metric recomputation in frontend.

## Codex C Handoff Prompt

You are Codex C, Backend Implementation agent for `portfolio-options-agent`.

Task: Phase 18A backend frontend-readiness contract for the first Trade Review Workspace.

Do not inspect `.env`, secrets, real brokerage data, local DB contents, broker exports, generated reports, screenshots, or logs. Do not modify `../TradingAgents`. Do not add TradingAgents integration, real market-provider calls, broker actions, DB migrations, frontend code, or commits unless explicitly asked.

Read:

1. `AGENTS.md`
2. `docs/shared/current_roadmap.md`
3. `docs/shared/TASKS.md`
4. `docs/shared/implementation_plan.md` Phase 18A
5. `docs/codex-b-architecture/PHASE_18A_FRONTEND_READINESS_CONTRACT.md`
6. `backend/app/schemas/actionability.py`
7. `backend/app/services/trade_review/*`
8. `backend/app/services/agents/orchestrator.py`
9. related synthetic tests under `backend/tests/services/trade_review/` and `backend/tests/services/agents/`

Goal:

Add the minimum backend contract/support needed before Claude A builds the first visible Trade Review Workspace: a typed sanitized read schema and mapper for deterministic trade-review plus Phase 16 actionability/orchestration outputs.

Non-goals:

- No frontend implementation.
- No TradingAgents/Public Research Evidence work.
- No real market-data provider integration.
- No broker order placement/cancellation/disconnect/delete.
- No broker scraping, Fidelity credential storage, or MFA bypass.
- No LLM-generated metrics or advice.
- No raw brokerage/private fields in response schemas or tests.

Expected work:

- Add a safe read schema, likely `backend/app/schemas/trade_review_workspace.py`.
- Add a mapper/projection service, likely `backend/app/services/trade_review/frontend_read.py`.
- Cover the four Phase 18A flows: stock/ETF buy, stock/ETF sell or trim, covered call, cash-secured put.
- Include actionability fields with separate broker snapshot and market quote metadata.
- Include deterministic sections for trade intent summary, portfolio impact, cash/collateral impact, concentration/allocation impact, options exposure, risk-rule violations, missing/stale data warnings, and analysis-only report output.
- Add recursive forbidden-field tests and prohibited-language checks.
- Add a small preview/read endpoint only if it fits existing route patterns; otherwise stop after schema/mapper/tests and update the plan.

Tests:

- Focused tests for the new schema/mapper.
- Existing trade-review/actionability/agent tests.
- Full backend `./.venv/bin/python -m pytest` if practical.

Recommendation expected at completion: PASS to Claude B backend-contract review if forbidden-field tests pass and no unsupported provider/TradingAgents/frontend work was added.

## Claude A Handoff Prompt

You are Claude A, Frontend UI/UX agent for `portfolio-options-agent`.

Task: Phase 18A first visible Trade Review Workspace.

Do not inspect `.env`, secrets, real brokerage data, local DB contents, broker exports, generated reports, screenshots, or logs. Do not modify backend, database migrations, `../TradingAgents`, or broker/provider code. Do not add broker order actions or execution controls.

Start only after Codex C has delivered the Phase 18A sanitized backend read contract and Claude B/Codex B have cleared it for frontend consumption.

Read:

1. `AGENTS.md`
2. `docs/shared/current_roadmap.md`
3. `docs/shared/TASKS.md`
4. `docs/shared/implementation_plan.md` Phase 18A
5. `docs/codex-b-architecture/PHASE_18A_FRONTEND_READINESS_CONTRACT.md`
6. frontend README and current frontend routes/components
7. the backend safe read schema and any generated/handwritten frontend type mirror

Goal:

Build a read-only Trade Review Workspace for the four MVP flows: stock/ETF buy, stock/ETF sell or trim, covered call, and cash-secured put. The workspace should use completed Phase 16 deterministic/actionability outputs and must clearly separate deterministic facts, broker freshness, market quote freshness, actionability status, and analysis-only report output.

Non-goals:

- No TradingAgents research/debate UI in Phase 18A.
- No option-chain browser, screener, market-data terminal, or strategy recommendation surface.
- No broker order placement, cancellation, execution, broker disconnect/delete, broker scraping, credential storage, or MFA bypass.
- No "you should buy/sell", "safe to trade", "ready to trade", or guaranteed-return language.
- No frontend financial metric computation beyond displaying backend fields.
- No storing portfolio/review data in localStorage/sessionStorage.

Frontend boundary:

- Use only the sanitized backend read contract.
- Do not invent API fields.
- Mirror backend types in `frontend/src/types/api.ts` or a focused `tradeReview` type module.
- Add loading, empty, error, stale, blocked, analysis-only, and manual-confirmation-required states.
- Display broker snapshot freshness and market quote freshness separately.
- Use visible caveats for incomplete coverage/collateral modelling.

Checks:

- `cd frontend && npm run typecheck`
- `cd frontend && npm run lint` if available
- `cd frontend && npm run build`

Expected output: changed frontend files, tests/checks run, screenshots only with synthetic data if explicitly requested, and a PASS/BLOCKED note for Claude B/Codex B review.
