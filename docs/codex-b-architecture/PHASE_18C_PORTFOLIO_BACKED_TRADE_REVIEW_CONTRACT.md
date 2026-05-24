# Phase 18C Portfolio-Backed Trade Review Contract

Status: architecture handoff
Owner: Codex B - Architecture / Systems / Integration
Last updated: 2026-05-21

## Decision

Codex A PM decision: **PASS** to start Phase 18C - Real Portfolio-Backed Trade Review Workspace.

Phase 18C should connect the visible Trade Review Workspace to a backend-owned, sanitized portfolio context instead of only the Phase 18A/18B synthetic preview. Phase 17 remains frozen. TradingAgents, public research evidence, LLM explanation, and real market-data provider integration stay out of this slice.

Recommended sequence:

1. Codex B defines this contract and plan.
2. Codex C implements the minimum backend portfolio-backed review path.
3. Codex B reviews the backend contract before Claude A builds against it.
4. Claude A integrates the frontend workspace.
5. Claude B reviews safety, stale-data clarity, and UX.
6. Codex B performs final architecture/integration signoff.

## Purpose

Phase 18C crosses the next product value line:

> Review this proposed manual trade against my current portfolio context, with clear stale-data warnings, deterministic risk/cash/collateral impact, and analysis-only output.

The phase should prove that app-owned portfolio context can feed deterministic pre-trade review safely, without exposing raw private brokerage data to the frontend and without implying trade execution, advice, or quote-current certainty.

## Scope

Phase 18C may use:

- existing sanitized portfolio snapshot or manual portfolio context;
- existing actionability policy;
- deterministic trade-review outputs;
- broker snapshot freshness status;
- market quote freshness, missing-quote, or market-data-unavailable status as a separate concept;
- visible covered-call/CSP caveat fields where coverage/collateral netting is incomplete.

Allowed trade-review flows remain:

- stock/ETF buy;
- stock/ETF sell or trim;
- covered call;
- cash-secured put.

Phase 18C should keep `POST /trade-reviews/preview` as the synthetic/manual demo endpoint. Portfolio-backed review should be a distinct backend path, likely `POST /trade-reviews/portfolio-preview`, so callers and frontend state can distinguish synthetic preview from portfolio-backed deterministic review.

## Non-Goals

Phase 18C must not include:

- TradingAgents integration;
- LLM explanation;
- public research/news evidence;
- real market-data provider integration;
- option-chain browsing;
- screeners;
- broker order placement or cancellation;
- broker destructive actions;
- broker scraping;
- credential storage;
- MFA bypass;
- automated recommendations;
- "you should buy/sell" language;
- guaranteed-return language.

## Backend Contract

Codex C should provide the minimum backend contract needed for a safe portfolio-backed workspace.

Expected endpoint shape:

```text
POST /trade-reviews/portfolio-preview
```

Expected request shape:

```text
TradeReviewPortfolioPreviewRequest
- supported_flow: SupportedTradeReviewFlow
- trade intent fields matching TradeReviewWorkspacePreviewRequest
- portfolio_context_selection: PortfolioContextSelectionRequest
```

`PortfolioContextSelectionRequest` should be backend-owned and safe:

```text
PortfolioContextSelectionRequest
- mode: latest_available | selected_context
- context_reference: string | null
```

Rules:

- `context_reference` must be an opaque app-generated reference, not `account_id`, `broker_account_id`, `provider_account_id`, `provider_connection_id`, or any raw provider id.
- If a safe context-reference system is not already available, the first backend slice may support only `mode=latest_available` and return a clear unavailable state when no sanitized/manual context exists.
- The request must not accept client-supplied broker freshness, market freshness, provider status, actionability status, cash balances, account values, holdings, positions, thresholds, or raw provider payloads.
- User confirmation/manual acknowledgement may be added only if it is server-validated and cannot upgrade stale/manual provider data to `normal_review`.

Expected response:

Reuse and extend `TradeReviewWorkspaceRead` rather than creating a parallel frontend model.

Add a safe portfolio context summary if needed:

```text
PortfolioContextSummaryRead
- context_reference: string
- context_source: snaptrade | manual | csv
- selection_mode: latest_available | selected_context
- summary_as_of: datetime | null
- latest_snapshot_as_of: datetime | null
- broker_snapshot: BrokerSnapshotMetadata
- stock_position_count: int
- option_position_count: int
- cash_state: available | unavailable | not_exposed
- label: string | null
```

Allowed summary fields are counts, source/provenance, as-of timestamps, safe labels, and freshness metadata. Do not expose raw holdings, raw positions, quantities held, cash balances, buying power, account values, account ids, broker/provider ids, raw payloads, trade journal entries, or account-specific thresholds.

`TradeReviewWorkspaceRead.actionability` remains authoritative for review readiness and must continue to preserve separate:

- `broker_snapshot`
- `market_quotes`

Market quotes must not be inferred from broker freshness. If real market data is unavailable in Phase 18C, the backend should emit `market_data_unavailable`, `manual_confirmation_required`, `analysis_only`, or a blocked stale/unknown market quote status through the existing actionability vocabulary and safe reasons.

## Backend Processing Boundary

Backend may use private app-owned `PortfolioReviewContext` internally to calculate deterministic review outputs. That private context must be reduced to the existing agent-safe projection and frontend-safe read schema before crossing the API boundary.

Backend owns:

- resolving the selected sanitized/manual portfolio context;
- deriving broker snapshot freshness from server-owned metadata;
- deriving market quote freshness or market-data-unavailable status from server-owned metadata;
- evaluating actionability;
- building `TradeIntent`;
- running deterministic validation, payoff, portfolio impact, and risk review;
- mapping results through the existing safe frontend read contract;
- recursive forbidden-field and prohibited-language checks.

Frontend owns only:

- selecting from safe context references or using `latest_available`;
- submitting supported trade intents;
- rendering the backend response read-only.

## Forbidden Frontend Fields

The Phase 18C frontend contract must recursively reject the existing Phase 18A/18B forbidden key set and any nested variants, including:

- raw holdings;
- raw positions;
- position quantities currently held;
- account values;
- cash balances;
- buying power;
- account ids;
- broker/provider ids;
- provider contract ids;
- provider symbols when they are provider-specific identifiers;
- raw provider payloads;
- raw metadata;
- secrets;
- trade journal entries;
- account-specific thresholds.

Allowed deterministic outputs include proposed trade quantity, proposed trade assumptions, estimated trade cash change, estimated premium cash change, estimated collateral requirement change, safe concentration delta fields, assignment/exercise/call-away deltas, safe risk-rule messages, and caveats.

## Persistence

Compute portfolio-backed preview results on demand for Phase 18C.

Do not add durable trade-review submission, report-history persistence, or agent-run persistence in the first backend slice unless an existing service already does so with safe metadata and the change stays small. If persistence is added later, store only safe actionability metadata, safe read/report references, and existing app-owned report artifacts. Do not persist raw frontend request payloads that contain private data.

## Required Tests

Codex C should add synthetic tests for:

- stock/ETF buy;
- stock/ETF sell or trim;
- covered call;
- cash-secured put;
- no portfolio context available;
- stale broker snapshot with market quote freshness separate;
- missing/unavailable market quotes with broker freshness separate;
- client cannot submit freshness/actionability metadata to force `normal_review`;
- forbidden private fields are absent recursively from response JSON;
- raw/account-specific risk thresholds are omitted;
- context references are opaque and provider/account ids are rejected;
- covered-call and CSP caveats remain present while netting is incomplete.

Tests must not use real broker data, real local DB contents, real provider calls, LLM calls, TradingAgents calls, screenshots, generated reports, or `.env` secrets.

## Claude A Frontend Boundary

Claude A may start only after Codex C implements the backend path and Codex B reviews the schema boundary.

Frontend should:

- let the user choose a safe context reference or use latest available context;
- submit supported trade intents;
- render deterministic review outputs from the backend;
- clearly separate broker snapshot freshness from market quote freshness;
- show stale/missing-data states prominently;
- keep analysis-only language visible;
- preserve covered-call/CSP caveats;
- avoid execution-style UI patterns such as "place trade", "submit order", "confirm order", "buy now", or "sell now".

Frontend must not compute financial metrics, invent fields, store portfolio/review data in browser storage, call brokers/market providers/LLMs/TradingAgents directly, or expose forbidden fields.

## Review Gates

Codex B backend contract review should verify:

- schema boundary and response shape;
- private-data exclusions;
- actionability and freshness semantics;
- server-owned provenance/actionability decisions;
- frontend/backend ownership;
- deterministic-first, read-only scope.

Claude B frontend review should verify:

- no forbidden private fields visible;
- no execution/trading controls;
- stale-data language is clear;
- covered-call/CSP caveats remain visible;
- no recommendation or guaranteed-return wording;
- UI communicates manual trade review, not trade execution.

Codex B final signoff should verify the full seam after Claude A and Claude B complete their slices.

## Codex C Handoff Prompt

You are Codex C, Backend Implementation agent for `portfolio-options-agent`.

Task: Phase 18C - real portfolio-backed Trade Review Workspace backend path.

Do not inspect `.env`, secrets, real brokerage data, local DB contents, broker exports, generated reports, screenshots, or logs. Do not call SnapTrade, Fidelity, market-data providers, LLM APIs, TradingAgents, or external APIs. Do not modify `../TradingAgents`. Do not implement frontend code. Do not commit unless explicitly asked.

Read:

1. `AGENTS.md`
2. `docs/shared/current_roadmap.md`
3. `docs/shared/TASKS.md`
4. `docs/shared/implementation_plan.md` Phase 18C
5. `docs/codex-b-architecture/PHASE_18C_PORTFOLIO_BACKED_TRADE_REVIEW_CONTRACT.md`
6. `docs/codex-b-architecture/PHASE_18A_FRONTEND_READINESS_CONTRACT.md`
7. `backend/app/schemas/trade_review_workspace.py`
8. `backend/app/services/trade_review/frontend_read.py`
9. `backend/app/api/routes/trade_reviews.py`
10. `backend/app/schemas/actionability.py`
11. `backend/app/services/trade_review/actionability.py`
12. `backend/app/services/trade_review/context.py`
13. Related synthetic tests under `backend/tests/services/trade_review/` and `backend/tests/api/test_trade_review_workspace.py`

Goal:

Add the minimum backend path that lets the Trade Review Workspace review a supported trade intent against an existing app-owned sanitized/manual portfolio context, while preserving the Phase 18A/18B frontend-safe read boundary.

Expected work:

- Keep existing `POST /trade-reviews/preview` synthetic/manual.
- Add a distinct portfolio-backed route, likely `POST /trade-reviews/portfolio-preview`.
- Add safe request schema(s) for context selection plus the existing supported trade intent fields.
- Use server-owned portfolio context and freshness metadata. Do not accept client-supplied broker/market freshness, provider status, actionability, cash, holdings, positions, thresholds, or account values.
- Reuse and extend `TradeReviewWorkspaceRead` only as needed with a safe `PortfolioContextSummaryRead`.
- Preserve separate broker snapshot freshness and market quote freshness.
- Return analysis-only or blocked/manual-confirmation states when market data is unavailable, manual, stale, or unknown.
- Preserve covered-call/CSP caveat fields while coverage/collateral netting is incomplete.
- Add recursive forbidden-field and prohibited-language tests.
- Add synthetic endpoint tests for all allowed flows and stale/missing-data states.

Non-goals:

- No TradingAgents integration.
- No LLM explanation.
- No public research/news evidence.
- No real market-data provider integration.
- No option-chain browser or screener.
- No broker order placement/cancellation or destructive broker actions.
- No broker scraping, credential storage, or MFA bypass.
- No frontend implementation.

Tests to run:

- Focused backend tests for the new schema/service/route.
- `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review/test_frontend_read.py tests/api/test_trade_review_workspace.py -q`
- Add any new focused command for the Phase 18C route tests.
- Run broader actionability/agent tests if shared schemas are touched.

Stop when the backend path is ready for Codex B architecture review. Update `docs/shared/implementation_plan.md` P18C-T1 verification notes, but do not mark later tasks done.
