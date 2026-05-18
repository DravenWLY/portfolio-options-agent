# Implementation Plan

Active and future implementation tasks only. Completed Phase 1-10 history lives in `docs/completed_phases_log.md`. High-level review context lives in `docs/current_roadmap.md` and `docs/agent_context/`.

Default reading rule: load this file for the current phase and next phase only. Avoid loading `docs/completed_phases_log.md` unless a task explicitly needs historical verification details.

## Incremental Backend-to-Frontend Delivery Rule

The project should now move in small vertical slices instead of long backend-only
or frontend-only stretches. The default loop for each new capability is:

1. **Codex backend contract and service slice** - implement the smallest backend
   contract, service, schema, or deterministic calculation needed for the next
   product capability. Add synthetic tests first-class.
2. **Codex verification and plan update** - run backend tests, update this plan,
   and keep the API/data freshness boundary explicit.
3. **Claude Sonnet frontend/review slice** - after the backend contract is stable,
   Claude may review the API shape and implement the corresponding frontend view
   using `frontend-design` and `finance-dashboard-ux-review`.
4. **Codex integration/security review** - verify no secrets, provider ids, raw
   payloads, misleading market-price labels, trade execution affordances, or
   data-freshness collapses were introduced.

Frontend work should not invent fields before the backend contract exists.
Backend work should not run multiple phases ahead without a minimal UI/review
surface for the completed capability. Every frontend slice must stay read-only,
show loading/empty/error/stale states, and distinguish broker freshness from
market quote freshness.

## Phase 11 - Frontend Dashboard Shell A

Status: P11-T1 through P11-T7 `done` and verified (history in `docs/completed_phases_log.md`).
P11-T8 (pre-push security hardening) `done`.

Scope delivered: React/Vite shell, user/account selector, portfolio summary,
cash/stock/option positions views, broker freshness bar and warnings panel,
report history placeholder, broker connection UI at `/broker` (P11-T7, read-only SnapTrade flow).

Out of scope (deferred): market quote UI, option screener, TradingAgents UI, trade execution UI.

### P11-T8 - Pre-Push SnapTrade Local Security Hardening

- Task id: `P11-T8`
- Title: Pre-Push SnapTrade Local Security Hardening
- Status: `done`
- Objective: Make the local read-only SnapTrade/Fidelity integration safe to commit and push:
  no unauthenticated real-data exposure, no provider identifiers/payloads/secrets reaching the
  frontend or logs, no destructive tooling in the runtime image, standards-based secret encryption.
- Dependencies: P11-T7 (done). No new SnapTrade calls to implement or test.
- Migration impact: Slice E (AEAD secret envelope) changes stored-secret format and requires
  migration `0016_expand_encrypted_secret_ref` because the Fernet envelope exceeds the old
  `String(255)` column. Existing local secret becomes undecryptable → one-time local
  re-register via the normal flow. No production data exists.
- Files expected to change: `docker-compose.yml`; new `.dockerignore` ×3; `frontend/.gitignore`;
  `backend/scripts/manual/delete_snaptrade_user.py`; `backend/app/api/routes/*.py` + new
  `backend/app/core/access_guard.py`; `backend/app/services/broker_import/secrets.py`;
  `backend/app/services/broker_import/providers/snaptrade_sdk_client.py`;
  `backend/app/services/broker_import/snaptrade_connection.py`;
  `backend/alembic/versions/0016_expand_encrypted_secret_ref.py`;
  `backend/app/schemas/broker_sync_api.py`; `backend/app/schemas/broker_account.py`;
  `frontend/src/components/broker/*`; `frontend/src/types/api.ts`; `frontend/src/api/brokerSync.ts`;
  `docs/implementation_plan.md`; `frontend/README.md`; new synthetic tests.
- Implementation steps (ordered slices, lowest blast radius first):
  - Slice A: loopback Docker ports; `.dockerignore` ×3; `frontend/.gitignore`; sanitize + isolate manual script.
  - Slice B: strip `snaptrade_user_id` / `provider_account_id` / raw payloads from public schemas + FE types.
  - Slice C: sanitize SnapTrade SDK exceptions; UI message allowlist.
  - Slice D: local-dev access guard on all real-data routes.
  - Slice E: replace custom crypto with vetted AEAD; versioned envelope.
  - Slice F: decouple app-UUID from SnapTrade userId; read-only portal test; FE terminal-status fix.
- Acceptance criteria: published ports bound to 127.0.0.1; real-data routes require local token;
  no API response carries provider identifiers/payloads; SDK errors yield generic messages
  (no `str(exc)`); secret encryption uses a vetted library; app-user UUID ≠ SnapTrade userId;
  portal always `connection_type="read"` (tested); FE treats `succeeded`/`partially_succeeded`/
  `failed`/`cancelled` as terminal and stops polling; manual script prints no provider IDs/raw exc
  and is excluded from the backend image; no real brokerage values anywhere in repo.
- Tests to run: `cd backend && pytest` (synthetic/mocked only); `cd frontend && npm run typecheck
  && npm run lint && npm run build`; `docker compose config`.
- Rollback notes: all changes are local source/config; revert via git. Slice E: if a stored secret
  cannot decrypt, re-run the normal register flow locally (no prod data; no data loss). No Alembic
  rollback unless the envelope exceeds 255 chars (then revert that migration too).
- Deferrals: UI error allowlist polish (M3), freshness vocabulary cosmetics (L1),
  compose `--reload` review (L2), real multi-user authn/z (out of scope — this is
  a local-dev gate only).
- Verification notes (2026-05-16):
  - Implemented Slice B: public broker schemas and frontend types no longer expose
    `snaptrade_user_id`, `provider_account_id`, `provider_request_id`, raw payloads, or raw metadata.
  - Implemented Slice C: SnapTrade SDK exception wrappers return generic provider-operation
    messages and do not echo raw upstream exception text.
  - Implemented Slice D: all application API routers except `/health`/OpenAPI require
    `X-Local-Access-Token`; Vite proxy injects the header server-side from
    `LOCAL_DEV_ACCESS_TOKEN`.
  - Implemented Slice E: `encrypted_secret_ref` now stores a versioned `Fernet` envelope
    using `cryptography`; no plaintext fallback key remains.
  - Implemented Slice F: registration uses an opaque `poa_*` SnapTrade user ref instead of the
    local app user UUID; SnapTrade user id + user secret are stored inside the encrypted envelope;
    connection portal requests remain `connection_type="read"` with test coverage; frontend sync
    polling treats `succeeded`, `partially_succeeded`, `failed`, and `cancelled` as terminal.
  - Additional safety fix: SnapTrade SDK account mapping no longer falls back to provider account
    number for `display_name`.
  - Added migration `0016_expand_encrypted_secret_ref` so Fernet envelopes fit in
    `provider_credentials_metadata.encrypted_secret_ref`.
  - Fixed broker freshness latest-run ordering to use `coalesce(completed_at, created_at)`.
  - Backend tests ran against an isolated synthetic database `portfolio_options_agent_test`
    using synthetic credentials, not the real local app database:
    `233 passed, 1 deselected in 5.26s`.
  - Frontend verification: `npm run typecheck`, `npm run lint`, and `npm run build` all passed.
  - Alembic verification on the isolated synthetic database:
    `alembic upgrade head` passed and `alembic current` returned
    `0016_expand_encrypted_secret_ref (head)`.
  - `git diff --check` passed.
  - Docker Compose verification note: `docker compose config` was intentionally not printed
    because it can expand environment values. Runtime checks used `docker compose ps`, loopback
    port bindings in `docker-compose.yml`, and isolated synthetic DB verification instead.

## Phase 12 - Market Data Contracts, Snapshots, and Manual Provider

Phase goal: define generic market data contracts for stock and option quotes, option-chain snapshots, provider capabilities, quote freshness, and actionability. This phase must remain strategy-agnostic: it supports future CSP, covered-call, hedge, collar, spread, and long-option workflows, but it must not hardcode wheel strategy assumptions. It includes a narrow frontend companion slice after backend contracts are stable; it does not add real provider integrations or option-chain browsing.

### P12-T1 - Market Data Domain Models

- Task id: `P12-T1`
- Title: Market Data Domain Models
- Objective: Define strategy-agnostic market data domain models for stock quotes, option contract identity, option quote snapshots, option chain snapshots, provider capabilities, quote request context, data mode, freshness, and actionability.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/models.py`
  - `backend/tests/services/market_data/test_domain_models.py`
  - `docs/architecture.md`
  - `docs/current_roadmap.md`
  - `docs/implementation_plan.md`
- Dependencies: `P11-T8`
- Implementation steps:
  1. Add top-of-module documentation explaining broker-vs-quote freshness separation.
  2. Define `DataMode`, `FreshnessStatus`, `ActionabilityStatus`, and `ContractSupportStatus` values.
  3. Define immutable dataclasses for `StockQuoteSnapshot`, `UnderlyingQuoteSnapshot`, `OptionContractIdentity`, `OptionQuoteSnapshot`, `OptionChainSnapshot`, `ProviderCapabilities`, and `QuoteRequestContext`.
  4. Make option identity explicit: OCC symbol when available, normalized identity of underlying + expiration + strike + call/put + multiplier, and provider symbol/contract id as provider-specific metadata.
  5. Include support flags for adjusted contracts, mini options, index options, weeklies, and unsupported/manual-review contracts.
  6. Do not add provider adapters, database tables, formulas, strategy evaluators, or frontend code.
- Acceptance criteria:
  - Market data models are separate from broker sync models and import no broker sync modules.
  - Option quote and chain snapshots are immutable domain objects suitable for later report reproducibility.
  - Market data models contain no CSP, covered-call, wheel, or personal-threshold assumptions.
  - No real provider calls, API keys, migrations, or external services are introduced.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_domain_models.py`
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove market data domain models and tests.
- Verification notes:
  - Refined the roadmap so Phase 12 is strategy-agnostic market data contracts, Phase 13 is generic options/risk services, and wheel-specific CSP/covered-call evaluators move to the new Phase 14 strategy evaluator framework.
  - Added `backend/app/services/market_data/models.py` with immutable domain models for stock quotes, underlying quotes, option contract identity, option quote snapshots, option chain snapshots, provider capabilities, and quote request context.
  - Added `backend/app/services/market_data/__init__.py` exports and top-level documentation for broker-vs-market freshness separation.
  - Added `backend/tests/services/market_data/test_domain_models.py` covering vocabulary, option identity, manual-review flags, quote freshness scope, chain validation, provider capabilities, request context normalization, and invalid-value rejection.
  - Verified no `broker_import`, CSP, covered-call, wheel, personal threshold, SnapTrade, or Fidelity coupling exists in `backend/app/services/market_data` or its tests.
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_domain_models.py` -> `8 passed in 0.03s`.
  - `cd backend && ./.venv/bin/python -m pytest` -> `166 passed, 92 skipped, 1 deselected in 0.45s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - `git diff --check` passed.
  - No migrations, real provider calls, API keys, external services, frontend code, or TradingAgents changes were introduced.
- Status: `done`

### P12-T2 - Provider Interfaces

- Task id: `P12-T2`
- Title: Provider Interfaces
- Objective: Define provider-agnostic `MarketDataProvider`, `OptionDataProvider`, and `GreeksProvider` protocols with capability discovery and no provider-specific assumptions.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/interfaces.py`
  - `backend/tests/services/market_data/test_interfaces.py`
  - `backend/tests/unit/test_module_boundaries.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T1`
- Implementation steps:
  1. Define stock quote and intraday bar methods on `MarketDataProvider`.
  2. Define expiration, option chain, and option snapshot methods on `OptionDataProvider`.
  3. Define optional IV/Greeks calculation method on `GreeksProvider`.
  4. Add provider capability discovery using `ProviderCapabilities`.
  5. Add an import-boundary test: `app.services.market_data.*` must not import from `app.services.broker_import.*`.
- Acceptance criteria:
  - Interfaces are separate from broker sync.
  - No real provider calls by default.
  - No option screener or strategy behavior is implemented.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove market data interface files/tests.
- Verification notes:
  - Added `backend/app/services/market_data/interfaces.py` with provider-agnostic `MarketDataProvider`, `OptionDataProvider`, and `GreeksProvider` protocols.
  - Exported the interfaces from `backend/app/services/market_data/__init__.py`.
  - Added `backend/tests/services/market_data/test_interfaces.py` with fake providers covering capability discovery, stock quotes, underlying quotes, intraday quote/bar-like snapshots, option expirations, option quote snapshots, option chain snapshots, and optional Greeks enrichment.
  - Added `backend/tests/unit/test_module_boundaries.py` to assert `app.services.market_data.*` does not import broker sync modules.
  - Verified no market-data service imports broker sync modules and no market-data interface exposes trade/order or strategy-screening methods; matching strings appear only in negative/boundary tests.
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_interfaces.py tests/unit/test_module_boundaries.py` -> `5 passed in 0.05s`.
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_domain_models.py` -> `8 passed in 0.03s`.
  - `cd backend && ./.venv/bin/python -m pytest` -> `171 passed, 92 skipped, 1 deselected in 0.41s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - `git diff --check` passed.
  - No provider implementations, real provider calls, API keys, migrations, external services, frontend code, option screener behavior, or strategy evaluators were introduced.
- Status: `done`

### P12-T3 - Quote Freshness and Actionability Policy

- Task id: `P12-T3`
- Title: Quote Freshness and Actionability Policy
- Objective: Centralize quote freshness and actionability classification while keeping broker sync freshness separate.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/freshness.py`
  - `backend/tests/services/market_data/test_freshness.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T2`
- Implementation steps:
  1. Implement timestamp/provider-mode based quote freshness classification.
  2. Use `freshness_scope="market_quote"` for market freshness responses.
  3. Classify actionability as `actionable_snapshot`, `analysis_only`, `manual_review_required`, `blocked_stale_quote`, `blocked_unknown_quote`, or `blocked_provider_error`.
  4. Ensure stale, unknown, manual, or EOD-only data cannot be labeled immediately actionable.
- Acceptance criteria:
  - Broker freshness and quote freshness are not collapsed into one timestamp.
  - Stale quote data is never labeled immediately actionable.
  - Actionability policy is strategy-agnostic.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove quote freshness/actionability module/tests.
- Verification notes:
  - Added `backend/app/services/market_data/freshness.py` with `QuoteFreshnessDecision`, quote age calculation, timestamp/data-mode freshness classification, and conservative actionability classification.
  - Exported freshness helpers from `backend/app/services/market_data/__init__.py`.
  - Added `backend/tests/services/market_data/test_freshness.py` for fresh live quotes, delayed/manual/EOD analysis-only quotes, stale/unknown blockers, provider-error blockers, manual-review overrides, and invalid vocabulary rejection.
  - Policy is intentionally conservative: only fresh live market quote snapshots can be `actionable_snapshot`; delayed, manual, EOD-only, stale, unknown, and provider-error data cannot be labeled immediately actionable.
  - Focused market-data test run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data` -> `27 passed in 0.06s`.
  - Full backend test run after P12-T7: `192 passed, 92 skipped, 1 deselected in 0.52s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - No broker freshness fields were reused or collapsed into market quote freshness.
- Status: `done`

### P12-T4 - API-Facing Market Data Schemas

- Task id: `P12-T4`
- Title: API-Facing Market Data Schemas
- Objective: Add API-facing schemas for stock quotes, underlying quotes, option quotes, option chains, provider status, freshness, and actionability.
- Files expected to change:
  - `backend/app/schemas/market_data.py`
  - `backend/tests/unit/test_market_data_schemas.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T3`
- Implementation steps:
  1. Define stock quote, underlying quote, option quote, option chain, and provider status response schemas.
  2. Include provider, timestamp, data mode, freshness status, actionability status, and freshness scope.
  3. Add exact-set schema tests for market quote freshness schemas. OpenAPI route tests are deferred until a public market-data route exists.
  4. Keep broker holdings/cash fields out of market quote schemas.
- Acceptance criteria:
  - Market schemas distinguish quote freshness from broker freshness.
  - No broker holdings, broker account ids, cash balances, or private account fields appear in market quote schemas.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Revert market data schemas and tests.
- Verification notes:
  - Added `backend/app/schemas/market_data.py` with Pydantic schemas for quote freshness, provider capabilities, provider status, option contract identity, stock quotes, underlying quotes, option quotes, and option chains.
  - Added `backend/tests/unit/test_market_data_schemas.py` with exact field-set assertions and forbidden broker/cash/private-field assertions.
  - Verified schemas preserve `freshness_scope="market_quote"` and validate from immutable domain objects.
  - No public market-data router was introduced in this task; OpenAPI route-level tests remain deferred until a market-data API route is intentionally added.
  - Focused schema/freshness run: `cd backend && ./.venv/bin/python -m pytest tests/unit/test_market_data_schemas.py tests/services/market_data/test_freshness.py` -> `11 passed in 0.05s`.
  - Full backend test run after P12-T7: `192 passed, 92 skipped, 1 deselected in 0.52s`.
  - No broker holdings, broker account ids, cash balances, secret fields, raw payloads, or private account fields appear in market quote schemas.
- Status: `done`

### P12-T5 - Manual/Mock Provider

- Task id: `P12-T5`
- Title: Manual/Mock Provider
- Objective: Add a deterministic provider for manually supplied or synthetic quote and option-chain snapshots.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/manual_provider.py`
  - `backend/tests/services/market_data/test_manual_provider.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T4`
- Implementation steps:
  1. Implement provider using explicit synthetic stock quote, underlying quote, option quote, option chain, and Greeks inputs.
  2. Support manual, delayed, stale, EOD-only, and unknown modes without network calls.
  3. Mark freshness and actionability based on supplied quote timestamps and data mode.
  4. Avoid API keys, network access, and provider-specific assumptions.
- Acceptance criteria:
  - Market data tests run without external providers.
  - Manual/mock quotes can feed future deterministic option/risk tests.
  - No real provider integrations are introduced.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove manual provider and tests.
- Verification notes:
  - Added `backend/app/services/market_data/manual_provider.py` with deterministic `ManualMarketDataProvider`, `ManualMarketDataNotFoundError`, `build_manual_stock_quote`, and `build_manual_option_quote`.
  - Exported manual provider helpers from `backend/app/services/market_data/__init__.py`.
  - Added `backend/tests/services/market_data/test_manual_provider.py` covering provider protocol conformance, explicit stock/underlying/option quote retrieval, option chain construction from explicit quotes, delayed/stale/EOD/unknown modes, and safe missing-data errors.
  - Manual/mock provider uses explicit in-memory synthetic inputs only; no network clients, API keys, SDK imports, or provider-specific assumptions were added.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_manual_provider.py tests/unit/test_market_data_schemas.py tests/services/market_data/test_freshness.py` -> `15 passed in 0.06s`.
  - Full backend test run after P12-T7: `192 passed, 92 skipped, 1 deselected in 0.52s`.
- Status: `done`

### P12-T6 - Snapshot and Report Reproducibility Policy

- Task id: `P12-T6`
- Title: Snapshot and Report Reproducibility Policy
- Objective: Define how current quote/chain cache, selected candidate snapshots, and report input snapshots will be handled later without building a full historical options warehouse.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/snapshots.py`
  - `backend/tests/services/market_data/test_snapshots.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T5`
- Implementation steps:
  1. Define policy objects or helpers for current chain cache vs selected candidate snapshot vs report input snapshot.
  2. Define future `quote_snapshot_id` and `chain_snapshot_id` usage for deterministic reports and agent runs.
  3. Add tests proving old report inputs should reference saved snapshots rather than current quotes.
  4. Do not add migrations or full historical options storage yet.
- Acceptance criteria:
  - Reports and strategy evaluations have a clear path to reproducible market inputs.
  - No full historical options warehouse is implemented.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove snapshot policy helpers/tests.
- Verification notes:
  - Added `backend/app/services/market_data/snapshots.py` with lightweight snapshot reference helpers for stock quote snapshots, option quote snapshots, option chain snapshots, and frozen report input snapshots.
  - Exported snapshot policy helpers from `backend/app/services/market_data/__init__.py`.
  - Added `backend/tests/services/market_data/test_snapshots.py` proving stable snapshot metadata, chain stable keys, report inputs using saved snapshot references, rejection of current-cache references for report inputs, and non-empty snapshot ids.
  - No database tables, migrations, historical options warehouse, or current quote lookup behavior were introduced.
  - Focused market-data run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data` -> `27 passed in 0.06s`.
  - Full backend test run after P12-T7: `192 passed, 92 skipped, 1 deselected in 0.52s`.
- Status: `done`

### P12-T7 - Mocked Market Data Tests

- Task id: `P12-T7`
- Title: Mocked Market Data Tests
- Objective: Cover domain models, provider interfaces, contract identity, manual/mock provider behavior, freshness, actionability, and module boundaries.
- Files expected to change:
  - `backend/tests/services/market_data/*`
  - `backend/tests/unit/test_module_boundaries.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T6`
- Implementation steps:
  1. Add provider contract tests.
  2. Add quote freshness and actionability tests.
  3. Add option contract identity tests, including unsupported/adjusted/manual-review cases.
  4. Add manual provider tests.
  5. Confirm no external provider calls run by default.
- Acceptance criteria:
  - Market data layer is safe to use without real credentials.
  - Market data layer remains strategy-agnostic and separate from broker sync.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove market data tests and fixtures.
- Verification notes:
  - Market data tests now cover domain models, provider interfaces, quote freshness/actionability, manual/mock provider behavior, snapshot reference policy, API-facing schemas, and module boundaries.
  - Added a module-boundary guard to ensure `app.services.market_data.*` imports no broker sync modules, network clients, or real provider SDKs such as `requests`, `httpx`, `yfinance`, `tradier`, `alpaca`, `polygon`, or `snaptrade`.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data tests/unit/test_market_data_schemas.py tests/unit/test_module_boundaries.py` -> `34 passed in 0.06s`.
  - Full backend run: `cd backend && ./.venv/bin/python -m pytest` -> `192 passed, 92 skipped, 1 deselected in 0.52s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - `git diff --check` passed.
  - No external provider calls, real credentials, broker data, frontend code, option-chain browser, option screener, trading UI, or strategy evaluators were introduced.
- Status: `done`

### P12-T8 - Claude review of market data contracts

- Task id: `P12-T8`
- Title: Claude review of market data contracts
- Objective: Ask Claude Sonnet to review the completed Phase 12 backend contract for frontend usability, data freshness clarity, accessibility implications, and finance-safety copy before UI work starts.
- Files expected to change:
  - `backend/app/services/market_data/freshness.py`
  - `backend/app/services/market_data/manual_provider.py`
  - `backend/app/services/market_data/snapshots.py`
  - `backend/tests/services/market_data/test_freshness.py`
  - `backend/tests/services/market_data/test_manual_provider.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T7`
- Implementation steps:
  1. Generate a focused Claude handoff prompt with files limited to market data schemas, provider models, freshness logic, tests, and the relevant plan section.
  2. Require Claude to use `frontend-design` and `finance-dashboard-ux-review`.
  3. Codex adjudicates findings before any frontend implementation.
- Acceptance criteria:
  - Frontend implications are reviewed before adding market data UI.
  - Any accepted backend contract fixes land before P12-T9.
- Tests to run:
  - Documentation/review task only; no tests unless contract fixes are accepted.
- Rollback notes:
  - Remove review notes from the plan if superseded.
- Verification notes:
  - Claude review verdict: PASS, no blockers. Codex adjudicated three findings before frontend P12-T9.
  - I1 decision: accept. Manual/mock providers must not mint `actionable_snapshot`; `build_manual_stock_quote` and `build_manual_option_quote` now reject data modes outside `ManualMarketDataProvider` capabilities, including `live`.
  - I1 evidence: `backend/tests/services/market_data/test_manual_provider.py` now asserts manual builder outputs never have `actionability_status == "actionable_snapshot"` and that `data_mode="live"` raises a safe `ValueError`.
  - I2 decision: partial accept. No new freshness enum was added; `freshness_status` remains quote-recency-oriented while `data_mode` carries cached/indicative semantics. Added a contract docstring in `backend/app/services/market_data/freshness.py` requiring UIs and downstream services to render freshness together with `data_mode` and `actionability_status`.
  - I2 evidence: `backend/tests/services/market_data/test_freshness.py` now asserts recent `cached` and `indicative` quotes are `analysis_only` even when their recency freshness is `fresh`.
  - I3 decision: accept as contract-clarity/documentation. `backend/app/services/market_data/snapshots.py` now states snapshot references store metadata only and each `snapshot_id` must resolve to an immutable stored quote/chain payload for true report reproducibility.
  - I3 Phase 13 prerequisite: before deterministic risk reports rely on market quote snapshots, Phase 13 or a prerequisite hardening task must add immutable stored quote/chain payload storage or explicitly store complete market input snapshots in the report input snapshot.
  - Focused run: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data/test_manual_provider.py tests/services/market_data/test_freshness.py tests/services/market_data/test_snapshots.py` -> `18 passed in 0.05s`.
  - Full backend run after fixes: `cd backend && ./.venv/bin/python -m pytest` -> `195 passed, 92 skipped, 1 deselected in 0.59s`; DB-backed tests skipped because the sandbox cannot reach the configured local PostgreSQL test database.
  - No real provider calls, network calls, migrations, frontend code, option screeners, trading UI, or wheel assumptions were introduced.
- Status: `done`

### P12-T9 - Frontend market data status slice

- Task id: `P12-T9`
- Title: Frontend market data status slice
- Objective: Add a thin read-only frontend surface for market data availability and quote freshness using only the Phase 12 manual/mock contract.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/README.md`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T8`
- Implementation steps:
  1. Add a small market data status panel or placeholder view that makes quote data availability explicit.
  2. Show `freshness_scope="market_quote"` separately from broker portfolio freshness.
  3. Use only manual/mock provider responses; no real provider API calls.
  4. Keep option screener, option-chain browsing, TradingAgents UI, and trade execution UI out of scope.
  5. Ask Claude Sonnet to implement or design this slice, then have Codex review security and API-contract alignment.
- Acceptance criteria:
  - UI distinguishes market quote freshness from broker sync freshness.
  - UI does not imply live/intraday quotes unless the backend says so.
  - No API keys, broker credentials, provider secrets, or account data are stored in browser storage.
  - Frontend typecheck, lint, and build pass.
- Tests to run:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Revert the frontend market status slice and related docs.
- Status: `done`
- Verification notes (2026-05-17):
  - Added `frontend/src/types/marketData.ts` mirroring `market_data.py`
    (`DataMode`, `FreshnessStatus`, `ActionabilityStatus`,
    `ProviderCapabilitiesRead`, `MarketDataProviderStatusRead`).
  - Added `MarketDataStatusPanel` + `MarketDataPage` at route `/market-data`,
    plus a sidebar nav item (collapsed-aware).
  - Static, contract-faithful manual/mock sample only — no fetch, no real
    provider call, no browser storage. Sample uses `data_mode="manual"`,
    `freshness_status="manual"`, `actionability_status="analysis_only"`
    (manual provider cannot mint `actionable_snapshot`, per Codex adjudication).
  - `freshness_status` is never rendered alone — always clustered with
    `data_mode` and `actionability_status`.
  - `freshness_scope="market_quote"` labelled and explicitly separated from
    broker portfolio sync freshness (separation notice on the page).
  - Conservative copy only: "provider not connected yet", "manual/mock inputs
    only", "do not treat as live market pricing", "broker holdings/cash from
    broker sync; market quotes separate". No live/intraday/guaranteed/trade copy.
  - `npm run typecheck`, `npm run lint` (--max-warnings 0), `npm run build` all
    passed. localStorage remains limited to `poa-appearance` /
    `poa-sidebar-collapsed` (no new storage added).

### P12-T10 - Codex integration review for Phase 12 vertical slice

- Task id: `P12-T10`
- Title: Codex integration review for Phase 12 vertical slice
- Objective: Review backend + frontend together after P12-T9 to verify the market data contract, UI copy, and freshness boundary are safe before Phase 13 starts.
- Files expected to change:
  - `docs/implementation_plan.md`
  - `frontend/src/components/marketdata/MarketDataStatusPanel.tsx` (only if review finds a small contract-copy/sample mismatch)
- Dependencies: `P12-T9`
- Implementation steps:
  1. Run backend and frontend tests.
  2. Inspect OpenAPI/frontend types for market quote fields and freshness scope.
  3. Confirm broker freshness and market quote freshness are not collapsed.
  4. Update verification notes.
- Acceptance criteria:
  - Phase 12 ships as a small vertical slice, not a backend-only foundation.
  - Phase 13 can consume manual/mock market inputs safely.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Revert integration notes or reopen P12-T9 if issues are found.
- Status: `done`

Verification notes:

- Codex integration review verdict: PASS. P12-T9 remains a thin frontend market-data status slice and does not start option-chain browsing, screening, trading UI, real providers, or live quote claims.
- Files changed during P12-T10:
  - `frontend/src/components/marketdata/MarketDataStatusPanel.tsx`
  - `docs/implementation_plan.md`
- Review finding and fix:
  - Found one small contract-polish mismatch: the static `MarketDataProviderStatusRead.checked_at` sample was a prose string even though the backend schema exposes `checked_at: datetime`.
  - Fixed `SAMPLE_STATUS.checked_at` to an ISO timestamp string (`2026-05-18T15:00:00Z`) while keeping the panel static and mock/manual-only.
- Backend/frontend contract review:
  - `frontend/src/types/marketData.ts` mirrors the backend market-data status vocabulary and keeps `freshness_scope: "market_quote"`.
  - `frontend/src/components/marketdata/MarketDataStatusPanel.tsx` renders `data_mode`, `freshness_status`, and `actionability_status` together and never renders freshness status alone.
  - `frontend/src/pages/MarketDataPage.tsx` explicitly states that broker holdings/cash come from broker sync and market quotes are a separate, not-yet-connected source.
  - The frontend market-data slice performs no network calls, adds no browser storage, and uses only static manual/mock sample data.
- Safety boundary review:
  - Broker portfolio freshness and market quote freshness remain separate (`broker_portfolio` vs. `market_quote`).
  - No real SnapTrade, market data provider, LLM, or TradingAgents calls were made.
  - No `.env` or secret files were read.
  - No trade/order/cancel/disconnect UI, option screener, guaranteed-return wording, or live-market-price implication was introduced.
- Tests run:
  - `cd backend && ./.venv/bin/python -m pytest`
    - Result: `195 passed, 92 skipped, 1 deselected in 0.53s`
    - Skips are the expected guarded database tests because the configured database is unavailable or not marked safe for destructive tests in this environment.
  - `cd frontend && npm run typecheck`
    - Result: passed (`tsc --noEmit`)
  - `cd frontend && npm run lint`
    - Result: passed (`eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0`)
  - `cd frontend && npm run build`
    - Result: passed (`77 modules transformed`, built in `469ms`)
- Acceptance criteria evidence:
  - Small vertical slice: backend market-data contracts/manual provider plus a static frontend market-data status page are complete; no speculative provider or screener surface was added.
  - Phase 13 can consume manual/mock market inputs safely: backend market-data tests cover domain models, provider interfaces, freshness/actionability, snapshots, schemas, module boundaries, and manual provider behavior; frontend copy preserves the manual/mock analysis-only boundary.
- Residual risk:
  - Phase 13 deterministic risk reports must still freeze market input payloads or add stored immutable quote/chain payloads before reports depend on market data.
  - Real market data provider integration remains deferred; Phase 12 intentionally makes zero real provider calls.

## Phase 13 - Generic Options Metrics and Portfolio Risk Engine

Phase goal: implement reusable deterministic option metrics and portfolio risk services before strategy evaluators or custom agents explain them. This phase is not a wheel-strategy phase. Python calculates all metrics; LLMs may explain structured results later but must not invent metrics. Strategy-specific CSP, covered-call, collar, spread, hedge, or wheel lifecycle logic belongs in the strategy evaluator layer after these generic services are stable.

Phase 13 prerequisite: deterministic risk reports that rely on market data must consume immutable market input snapshots. Before report outputs depend on quote/chain data, add stored quote/chain payload support or embed complete frozen quote/chain payloads in the report input snapshot; metadata-only `snapshot_id` references are not sufficient by themselves for reproducibility.

### P13-T1 - option formulas

- Task id: `P13-T1`
- Title: option formulas
- Objective: Implement deterministic formulas for premium yield, annualized ROI, breakeven, downside buffer, bid-ask spread percentage, and premium capture.
- Files expected to change:
  - `backend/app/services/options/formulas.py`
  - `backend/tests/services/options/test_formulas.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T10`
- Implementation steps:
  1. Add pure-Python Decimal-based formulas.
  2. Document inputs and units.
  3. Add edge-case tests for zero/invalid inputs.
- Acceptance criteria:
  - Formula outputs are deterministic and covered by unit tests.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove formulas and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/options/formulas.py` as a pure-Python,
  Decimal-only formula module. No database, API route, market data provider,
  broker sync service, LLM, TradingAgents, or frontend code was touched.
- Formulas implemented:
  - `premium_yield(premium, capital_at_risk)`
  - `annualized_roi(return_amount, capital_at_risk, days_held)`
  - `breakeven_after_credit(reference_price, credit)`
  - `downside_buffer(reference_price, breakeven_price)`
  - `bid_ask_spread_percentage(bid, ask)`
  - `premium_capture(initial_credit, current_debit_to_close)`
- Units are documented in function docstrings. Returned percentages are raw
  Decimal ratios; presentation layers decide rounding and percent formatting.
- Added `backend/tests/services/options/test_formulas.py` with deterministic
  unit coverage for normal cases and invalid zero/negative edge cases.
- Tests run:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/options/test_formulas.py`
    - Result: `19 passed in 0.02s`
  - `cd backend && ./.venv/bin/python -m pytest`
    - Result: `214 passed, 92 skipped, 1 deselected in 0.49s`
    - Skips are the expected guarded database tests because the configured
      database is unavailable or not marked safe for destructive tests in this
      environment.
- Claude handoff:
  - No frontend/UI work is needed for P13-T1 alone. The next Claude-owned work
    should wait until a reviewable risk output surface exists later in Phase 13
    (for example after collateral, assignment/allocation, and risk-rule outputs
    are stable enough for a thin risk-review UI slice).

### P13-T2 - collateral and free cash

- Task id: `P13-T2`
- Title: collateral and free cash
- Objective: Calculate generic option collateral usage, free cash, and cash reserve impact for account-level risk review.
- Files expected to change:
  - `backend/app/services/risk/collateral.py`
  - `backend/tests/services/risk/test_collateral.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T1`
- Implementation steps:
  1. Calculate collateral usage from account positions and strategy-neutral collateral inputs.
  2. Distinguish total cash, reserved collateral, and free cash.
  3. Keep account values synthetic in tests.
- Acceptance criteria:
  - Cash/collateral outputs are deterministic and account scoped.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove collateral service and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/collateral.py` as a deterministic,
  strategy-neutral collateral module.
- Added `CollateralRequirement`, `CollateralSummary`, and
  `calculate_collateral_summary(...)`.
- The service distinguishes `total_cash`, `existing_reserved_cash`,
  `option_collateral_required`, `total_reserved_cash`, `free_cash`, and
  `collateral_utilization`.
- Negative `free_cash` is allowed as a deterministic risk signal instead of
  being clamped.
- Added `backend/tests/services/risk/test_collateral.py` with synthetic unit
  coverage for normal calculations and invalid inputs.
- Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk/test_collateral.py` -> `8 passed in 0.02s`.

### P13-T3 - assignment and exercise scenario

- Task id: `P13-T3`
- Title: assignment and exercise scenario
- Objective: Project cash, holdings, concentration, and allocation after selected option assignment or exercise scenarios.
- Files expected to change:
  - `backend/app/services/risk/assignment.py`
  - `backend/tests/services/risk/test_assignment.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T2`
- Implementation steps:
  1. Project assigned/exercised shares and cash impact from structured scenario inputs.
  2. Calculate projected allocation and concentration.
  3. Emit structured scenario outputs.
- Acceptance criteria:
  - Assignment projections do not depend on LLMs.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove assignment service and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/assignment.py` as a deterministic
  assignment/exercise scenario projection module.
- Added support for `short_put_assignment`, `short_call_assignment`,
  `long_call_exercise`, and `long_put_exercise`.
- The projection emits share delta, cash delta, projected cash, projected total
  value, projected holdings, and largest-position concentration.
- The service rejects scenarios that would create negative projected long-share
  quantities.
- Added `backend/tests/services/risk/test_assignment.py` with synthetic unit
  coverage for short put assignment, short call assignment, long option
  exercise actions, and invalid inputs.
- Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk/test_assignment.py tests/services/risk/test_collateral.py` -> `19 passed in 0.03s`.

### P13-T4 - allocation impact service

- Task id: `P13-T4`
- Title: allocation impact service
- Objective: Calculate projected allocation drift, concentration, and exposure impact from generic portfolio or option scenarios.
- Files expected to change:
  - `backend/app/services/risk/allocation.py`
  - `backend/tests/services/risk/test_allocation.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T3`
- Implementation steps:
  1. Calculate target allocation drift and concentration.
  2. Support projected post-scenario allocation inputs.
  3. Keep account allocation rules synthetic/config-driven in tests.
- Acceptance criteria:
  - Allocation impact outputs are deterministic and strategy-agnostic.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove allocation impact service and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/allocation.py` as a deterministic,
  strategy-agnostic allocation and concentration module.
- Added `AllocationPosition`, `AllocationTarget`, `AllocationImpactItem`,
  `AllocationImpact`, and `calculate_allocation_impact(...)`.
- The service calculates total value, actual weights, optional target drift,
  absolute drift, and largest-position concentration.
- Added `backend/tests/services/risk/test_allocation.py` with synthetic unit
  coverage for target drift, missing targets, empty/zero-value portfolios, and
  invalid inputs.
- Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk/test_allocation.py tests/services/risk/test_assignment.py tests/services/risk/test_collateral.py` -> `27 passed in 0.05s`.

### P13-T5 - risk rule engine

- Task id: `P13-T5`
- Title: risk rule engine
- Objective: Evaluate deterministic risk rule violations from option metrics, collateral, assignment/exercise scenarios, allocation impact, quote freshness, and broker freshness.
- Files expected to change:
  - `backend/app/services/risk/violations.py`
  - `backend/tests/services/risk/test_violations.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T4`
- Implementation steps:
  1. Emit `risk_rule_violations` as deterministic structured outputs.
  2. Use severity values `info`, `warning`, `violation`, and `blocker`.
  3. Keep strategy thresholds configurable or synthetic; do not hardcode private thresholds.
- Acceptance criteria:
  - Risk-rule violations are structured, deterministic, and severity tagged.
  - LLMs are not used to create or modify violations.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove risk rule engine and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/violations.py` as a deterministic
  risk-rule violation engine.
- Added `RiskRuleViolation`, `RiskThresholdRule`,
  `evaluate_threshold_rules(...)`, `evaluate_market_actionability(...)`, and
  `evaluate_broker_freshness(...)`.
- Severity vocabulary is structured as `info`, `warning`, `violation`, and
  `blocker`.
- Missing required metrics emit blocker violations instead of silently passing.
- Broker freshness and market quote actionability remain distinct input sources.
- Added `backend/tests/services/risk/test_violations.py` with synthetic unit
  coverage for threshold rules, missing metrics, market actionability, broker
  freshness, and invalid inputs.
- Focused test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk/test_violations.py tests/services/risk/test_allocation.py tests/services/risk/test_assignment.py tests/services/risk/test_collateral.py` -> `48 passed in 0.05s`.

### P13-T6 - deterministic risk report

- Task id: `P13-T6`
- Title: deterministic risk report
- Objective: Combine portfolio summary, market inputs, option formulas, collateral, assignment/exercise scenarios, allocation impact, and violations into a deterministic risk report.
- Files expected to change:
  - `backend/app/services/risk/report.py`
  - `backend/tests/services/risk/test_report.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T5`
- Implementation steps:
  1. Compose deterministic report sections from structured service outputs.
  2. Persist or hand off to Phase 10 report history where appropriate.
  3. Keep narrative explanation template-based for now.
- Acceptance criteria:
  - A deterministic risk report can be generated with synthetic inputs.
  - Report identifies risk-rule violations without LLM invention.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove deterministic risk report service and tests.
- Status: `done`

Verification notes:

- Implemented `backend/app/services/risk/report.py` as a template-based
  deterministic risk report composer.
- Added `RiskReportSection`, `DeterministicRiskReport`,
  `build_deterministic_risk_report(...)`, and
  `render_risk_report_markdown(...)`.
- The report combines option metrics, collateral summary, assignment/exercise
  scenario projections, allocation impact, risk-rule violations, calculation
  version, generated timestamp, and an input snapshot reference.
- Markdown output is conservative and explicitly says it comes from
  deterministic Python services only; no LLM narrative is generated.
- Persistence to Phase 10 report history is not wired yet; the service returns
  structured output and markdown for later API/UI integration.
- Added `backend/tests/services/risk/test_report.py` with synthetic unit
  coverage for composed sections, markdown output, violation display, no-
  violation state, and required-field validation.
- Focused risk-service test result: `cd backend && ./.venv/bin/python -m pytest tests/services/risk` -> `52 passed in 0.05s`.
- Full backend test result after P13-T2 through P13-T6:
  `cd backend && ./.venv/bin/python -m pytest` -> `266 passed, 92 skipped, 1 deselected in 0.53s`.
  Skips are the expected guarded database tests because the configured database
  is unavailable or not marked safe for destructive tests in this environment.
- Claude handoff:
  - Backend deterministic risk contracts are now ready for P13-T7 review before
    any P13-T8 frontend risk-review slice begins.

### P13-T7 - Claude review of generic risk contracts

- Task id: `P13-T7`
- Title: Claude review of generic risk contracts
- Objective: Ask Claude Sonnet or Opus, depending on risk level, to review generic deterministic risk output schemas and frontend implications before building the risk UI slice.
- Files expected to change:
  - `docs/implementation_plan.md`
  - Accepted-fix files from Claude review, if any, before P13-T8:
    - `backend/app/schemas/risk.py`
    - `backend/app/services/options/formulas.py`
    - `backend/app/services/risk/allocation.py`
    - `backend/app/services/risk/assignment.py`
    - `backend/app/services/risk/collateral.py`
    - `backend/app/services/risk/report.py`
    - `backend/app/services/risk/violations.py`
    - `backend/tests/services/options/test_formulas.py`
    - `backend/tests/services/risk/test_allocation.py`
    - `backend/tests/services/risk/test_assignment.py`
    - `backend/tests/services/risk/test_collateral.py`
    - `backend/tests/services/risk/test_report.py`
    - `backend/tests/unit/test_risk_schemas.py`
- Dependencies: `P13-T6`
- Implementation steps:
  1. Generate a focused Claude handoff prompt limited to deterministic option/risk services, schemas, tests, and this plan section.
  2. Use Opus only if the review concerns financial calculation semantics, collateral, assignment exposure, or long/short liability handling.
  3. Require review output to separate blockers, important issues, deferrals, and suggested changes for Codex.
  4. Codex adjudicates findings before UI work starts.
- Acceptance criteria:
  - Deterministic outputs are reviewed before UI presentation.
  - Any accepted backend correctness fixes land before P13-T8.
- Tests to run:
  - Documentation/review task only; no tests unless fixes are accepted.
- Rollback notes:
  - Remove review notes if superseded.
- Status: `done`

Verification notes (2026-05-17):

- Opus review raised two blockers (B1: unbounded report contract / no
  broker-secret guard; B2: no deterministic aggregate severity) and seven
  important finance-semantics issues. Codex accepted and fixed all of them.
- B1 resolved: added `backend/app/schemas/risk.py` read schemas with a
  broker/cash/secret/raw-payload forbidden-key guard at both the domain
  (`RiskReportSection`) and schema layers; `input_snapshot` is now typed
  `ReportMarketDataSnapshot | None` instead of `Mapping[str, object]`;
  rendered markdown and the public Read schema no longer expose `account_id`.
- B2 resolved: deterministic `highest_severity` / `has_blocker` added and
  tested using the `info<warning<violation<blocker` ordering.
- Important issues resolved: split downside vs upside breakeven helpers;
  documented annualized ROI as simple/non-compounded/not a forecast;
  documented zero-cash collateral semantics and surfaced free cash;
  documented naked short-call assignment as an MVP scope boundary;
  relabeled assignment vs allocation weight denominators; added
  missing-target allocation drift rows; documented the broker-vs-market
  severity asymmetry.
- Tests: focused `84 passed`; full `279 passed, 92 skipped, 1 deselected`;
  `git diff --check` passed.
- Opus re-review verdict: PASS — contract is safe for a read-only frontend.
  P13-T8 may proceed.
- Deferred (track, not P13-T8 blockers): consolidate the duplicated
  forbidden-key constant (currently in `schemas/risk.py`, `risk/report.py`,
  and `tests/unit/test_risk_schemas.py`) into one shared source before a
  real risk API route is added; the report-fact guard is key-name based,
  so the future route assembling `option_metrics` must be audited so
  broker-sourced values cannot be injected under benign metric keys.

Verification notes:

- Claude P13-T7 review verdict: BLOCKED at the P13-T7 -> P13-T8 gate. Backend
  commit/correctness was acceptable, but the risk report contract was not yet
  safe to expose to frontend.
- Codex adjudication and decisions:
  - B1 accepted. Risk report output needed a constrained read contract and a
    broker/private-data guard. Added `backend/app/schemas/risk.py` with explicit
    read schemas for risk reports, sections, violations, and typed market-data
    snapshot references. Changed deterministic reports to use
    `ReportMarketDataSnapshot | None` instead of unbounded
    `Mapping[str, object]`. Added report fact-key guards against broker,
    cash, secret, and raw-provider fields.
  - B2 accepted. The frontend should not derive severity precedence. Added
    deterministic `highest_severity` and `has_blocker` to
    `DeterministicRiskReport`, populated them in report building, rendered them
    in markdown, and covered blocker precedence in tests.
  - Annualized ROI finding accepted. Documented it as simple, non-compounded
    linear extrapolation and not a forecast. Added negative-return coverage.
  - Breakeven direction finding accepted. Constrained
    `breakeven_after_credit` to downside/credit-reduces-cost use and added
    `upside_breakeven_after_credit` for upper-boundary use. Added a
    counterexample test showing the two directions differ.
  - Zero-cash collateral utilization finding partially accepted. Kept
    `collateral_utilization == 0` when `total_cash == 0` because the percentage
    denominator is undefined, but documented and tested that `free_cash < 0`
    plus `total_reserved_cash` are the authoritative over-commitment signals.
  - Naked short-call assignment finding accepted as a scope boundary. The MVP
    assignment engine models long-share holdings only; a short-call assignment
    that would create short stock raises instead of modeling margin/short-stock
    behavior. Added explicit docs and test coverage.
  - Valuation/weight semantics finding accepted. Documented that assignment
    projections reprice only the scenario underlying while other holdings keep
    supplied values; assignment concentration weights include projected cash,
    while allocation impact weights exclude cash unless cash is supplied as a
    position. Report fact labels now distinguish these denominators.
  - Missing-target allocation finding accepted. Allocation impact now emits
    zero-position drift items for targets that have no matching position, so
    under-allocation is visible.
  - Broker-vs-market severity asymmetry finding accepted. Added a module
    docstring explaining why market quote stale/unknown/provider-error states
    block actionable risk analysis while stale/cached broker data is warning
    unless the broker state is error/reauth-required.
  - Deferred: the engine does not yet self-emit informational findings, and
    markdown still renders Decimals with default string formatting. These are
    presentation/report-polish concerns and do not block the schema/safety gate.
- Code/tests changed for accepted items:
  - `backend/app/schemas/risk.py`
  - `backend/app/services/options/formulas.py`
  - `backend/app/services/risk/allocation.py`
  - `backend/app/services/risk/assignment.py`
  - `backend/app/services/risk/collateral.py`
  - `backend/app/services/risk/report.py`
  - `backend/app/services/risk/violations.py`
  - `backend/tests/services/options/test_formulas.py`
  - `backend/tests/services/risk/test_allocation.py`
  - `backend/tests/services/risk/test_assignment.py`
  - `backend/tests/services/risk/test_collateral.py`
  - `backend/tests/services/risk/test_report.py`
  - `backend/tests/unit/test_risk_schemas.py`
- Tests run:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/options/test_formulas.py tests/services/risk tests/unit/test_risk_schemas.py`
    - Result: `84 passed in 0.14s`
  - `cd backend && ./.venv/bin/python -m pytest`
    - Result: `279 passed, 92 skipped, 1 deselected in 0.65s`
    - Skips are the expected guarded database tests because the configured
      database is unavailable or not marked safe for destructive tests in this
      environment.
- Gate status:
  - RESOLVED. The Opus re-review (see "Opus re-review verdict: PASS" above)
    confirmed the deterministic risk report contract is safe for a read-only
    frontend. The earlier BLOCKED gate is cleared; P13-T8 proceeded.

### P13-T8 - Frontend generic risk review slice

- Task id: `P13-T8`
- Title: Frontend generic risk review slice
- Objective: Add a read-only frontend view for deterministic option metrics, collateral, assignment/exercise scenarios, allocation impact, and risk-rule violations.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/README.md`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T7`
- Implementation steps:
  1. Ask Claude Sonnet to design and implement the risk review slice using `frontend-design` and `finance-dashboard-ux-review`.
  2. Display deterministic outputs as calculated facts, not LLM advice.
  3. Show `risk_rule_violations` by severity: `info`, `warning`, `violation`, `blocker`.
  4. Include loading, empty, missing-market-data, stale-quote, and broker-stale states.
  5. Do not add buy/sell/order/execute controls or guaranteed-return language.
- Acceptance criteria:
  - Users can inspect generic deterministic risk outputs without agent, TradingAgents, or strategy evaluator integration.
  - UI distinguishes deterministic calculations from future LLM-generated explanation.
  - No trade execution UI or broker action UI is introduced.
  - Frontend typecheck, lint, and build pass.
- Tests to run:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Revert the frontend risk review slice and related docs.
- Status: `done`
- Verification notes (2026-05-18):
  - Frontend-only, stubbed slice. There is NO backend risk HTTP route; the UI
    is built against the typed contract using a synthetic in-memory stub
    (`frontend/src/api/riskReview.ts`). No real SnapTrade/Fidelity/market-data/
    LLM/TradingAgents APIs are called; no browser storage; no `.env`/DB access.
  - Files changed:
    - `frontend/src/types/api.ts` — exact mirror of `backend/app/schemas/risk.py`
      (Decimal→string; omits `account_id`/forbidden broker-private keys).
    - `frontend/src/api/riskReview.ts` (new, synthetic stub).
    - `frontend/src/hooks/useRiskReview.ts` (new).
    - `frontend/src/components/risk/RiskReviewPanel.tsx` (new).
    - `frontend/src/pages/RiskReviewPage.tsx` (new).
    - `frontend/src/App.tsx`, `frontend/src/components/layout/Sidebar.tsx`
      (route `/risk` + nav).
  - Codex BLOCKED fixes applied: (B1) generic stub now uses
    `collateral_method: "short_option_cash_reserve"` — no CSP/wheel/covered-call
    strategy wording or UI; (B2) option-chain snapshot `stable_key` now uses
    underlying:expiration semantics (`XYZ:2026-06-19`), distinct from the
    per-contract quote key.
  - Severity is driven solely by backend `has_blocker`/`highest_severity`
    (never recomputed); violations grouped by severity with icon+text;
    deterministic facts rendered verbatim; `annualized_roi` carries the
    "simple annualized — not a forecast, not guaranteed" caveat; market-quote
    provenance shown distinctly from broker freshness; states covered
    (loading/empty/error/missing-market/stale-quote/broker-stale).
  - Build/tests:
    - `cd frontend && npm run typecheck` — passed (0 errors).
    - `cd frontend && npm run lint` — passed (0 warnings, --max-warnings 0).
    - `cd frontend && npm run build` — passed (`index-BxKXnQ5M.js`).
    - `cd backend && ./.venv/bin/python -m pytest` — `279 passed, 92 skipped,
      1 deselected` (unchanged; no backend edits in this task).
  - No interactive browser click-through was performed by Claude (no dev
    server/display in that environment); state coverage was verified via the
    scenario switcher code paths and build, not a visual session.
  - Codex P13-T9 re-review passed on 2026-05-18. Browser click-through was
    intentionally not performed during re-review to avoid opening pages that may
    render real brokerage data; source review plus typecheck/lint/build/backend
    tests passed.

### P13-T9 - Codex integration review for Phase 13 vertical slice

- Task id: `P13-T9`
- Title: Codex integration review for Phase 13 vertical slice
- Objective: Verify backend deterministic risk outputs and the frontend risk review slice align before strategy evaluators are added.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P13-T8`
- Implementation steps:
  1. Run backend and frontend tests.
  2. Confirm frontend fields map directly to deterministic backend outputs.
  3. Confirm no LLM text, strategy recommendation, TradingAgents output, or trade execution affordance is mixed into deterministic risk UI.
  4. Update verification notes.
- Acceptance criteria:
  - Phase 13 ships as a small vertical generic risk-review slice.
  - Strategy evaluators can consume reviewed deterministic outputs in Phase 14.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Reopen P13-T8 if integration issues are found.
- Status: `done`

Verification notes (2026-05-18):

- Codex integration review verdict: PASS.
- Contract fidelity:
  - `frontend/src/types/api.ts` risk types map to
    `backend/app/schemas/risk.py` read schemas:
    `DeterministicRiskReportRead`, `RiskReportSectionRead`,
    `RiskRuleViolationRead`, and `MarketDataSnapshotReferenceRead`.
  - Decimal values are represented as JSON strings in frontend types, and
    section facts allow `string | number | null` for the backend
    `Decimal | str | int | None` shape.
  - Risk-specific client types do not reintroduce `account_id` or other
    broker/private keys that the backend risk schema intentionally omits.
- Frontend safety and deterministic framing:
  - Overall severity is driven by backend `has_blocker` and
    `highest_severity`; the frontend does not re-rank or recompute aggregate
    severity.
  - Risk-rule violations are grouped by literal severity with icon and text,
    not color alone.
  - Deterministic facts are labelled as Python calculation output, separated
    from any future LLM text, and annualized ROI includes the explicit
    "simple annualized — not a forecast, not guaranteed" caveat.
  - Market quote provenance is shown with `freshness_scope="market_quote"` and
    remains separate from broker portfolio freshness.
  - No buy/sell/order/execute/disconnect controls, strategy recommendations,
    TradingAgents output, or real API calls were introduced.
- P13-T8 blocker fixes confirmed:
  - `frontend/src/api/riskReview.ts` uses generic
    `collateral_method: "short_option_cash_reserve"` instead of CSP/wheel
    strategy wording.
  - Option-chain snapshot references use underlying:expiration semantics
    (`XYZ:2026-06-19`) rather than the per-contract quote key.
- Tests run:
  - `cd frontend && npm run typecheck` — passed (0 errors).
  - `cd frontend && npm run lint` — passed (0 warnings, `--max-warnings 0`).
  - `cd frontend && npm run build` — passed (`81 modules transformed`, built in
    `365ms`, output bundle `index-BxKXnQ5M.js`).
  - `cd backend && ./.venv/bin/python -m pytest` — `279 passed, 92 skipped,
    1 deselected in 0.51s`.
  - Skips are the expected guarded database tests because the configured
    database is unavailable or not marked safe for destructive tests in this
    environment.
- Browser click-through was intentionally not performed in this review pass to
  avoid opening pages that may render real brokerage data. A future visual QA
  pass can use synthetic/local-safe state only.
- Deferred:
  - Consolidate the duplicated forbidden-key constant before a real risk API
    route is added.
  - Audit the future route that assembles risk report facts so broker-sourced
    values cannot be injected under benign metric keys.

## Phase 14 - Trade Intent Review Foundation

Phase goal: introduce `TradeIntent` as the core abstraction for proposed manual stock, ETF, and options trades. This phase should broaden the product from options-income review to a portfolio-aware trade review pipeline. It must not add order execution, broker order routes, strategy recommendations, or real provider calls.

### P14-T1 - TradeIntent domain models

- Task id: `P14-T1`
- Title: TradeIntent domain models
- Objective: Define strategy-neutral intent models for proposed stock, ETF, and options trades.
- Files expected to change:
  - `backend/app/services/trade_review/models.py`
  - `backend/tests/services/trade_review/test_models.py`
  - `docs/architecture.md`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T9`
- Implementation steps:
  1. Define `TradeIntent` with shared id, user/account references, asset class, intent type, assumptions, notes, calculation version, and data freshness snapshot.
  2. Define `StockTradeIntent`, `ETFTradeIntent`, `OptionStrategyIntent`, and `OptionLeg`.
  3. Support stock buy, stock sell/trim, ETF review, long call, long put, CSP, and covered-call intents without making any one strategy the schema foundation.
  4. Keep models deterministic and serializable for reports/journals.
- Acceptance criteria:
  - One intent foundation can represent stocks, ETFs, and options.
  - No `covered_call_candidates`, `csp_candidates`, `wheel_positions`, or `premium_income_strategy` core tables/models are introduced.
  - No broker execution/order behavior.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove trade-review model files/tests and plan notes.
- Status: `not_started`

### P14-T2 - PortfolioContextBuilder and MarketSnapshotResolver

- Task id: `P14-T2`
- Title: Portfolio context and market snapshot resolution
- Objective: Resolve the portfolio and market inputs needed to review a trade intent without sending sensitive brokerage data to LLMs.
- Files expected to change:
  - `backend/app/services/trade_review/context.py`
  - `backend/app/services/trade_review/snapshots.py`
  - `backend/tests/services/trade_review/test_context.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T1`
- Implementation steps:
  1. Define `PortfolioContextBuilder` inputs/outputs using existing portfolio summaries and positions.
  2. Define `MarketSnapshotResolver` inputs/outputs using Phase 12 market-data snapshots.
  3. Preserve broker freshness and market quote freshness separately.
  4. Return structured context for deterministic services only; do not create LLM prompts in this phase.
- Acceptance criteria:
  - Context and market snapshot outputs are explicit, typed, and freshness-aware.
  - Sensitive provider identifiers, account numbers, raw payloads, and secrets are not included.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove context/snapshot resolver files/tests.
- Status: `not_started`

### P14-T3 - TradeIntentValidator

- Task id: `P14-T3`
- Title: TradeIntentValidator
- Objective: Validate trade intents before deterministic review.
- Files expected to change:
  - `backend/app/services/trade_review/validation.py`
  - `backend/tests/services/trade_review/test_validation.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T2`
- Implementation steps:
  1. Validate supported asset class, action, quantity, option leg shape, expiration, strike, multiplier, and price assumptions.
  2. Emit structured validation warnings/blockers instead of prose-only failures.
  3. Keep unsupported contracts and ambiguous intents as manual-review-required states.
- Acceptance criteria:
  - Invalid or ambiguous intents do not reach the deterministic review engine as actionable.
  - Validation output uses structured severity and codes.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove validator files/tests.
- Status: `not_started`

### P14-T4 - Journal and report-history links

- Task id: `P14-T4`
- Title: Trade review journal links
- Objective: Link trade intents to report history and future journal entries without adding full journal UI yet.
- Files expected to change:
  - `backend/app/services/trade_review/journal.py`
  - `backend/tests/services/trade_review/test_journal_links.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T3`
- Implementation steps:
  1. Define how reviewed trade intents reference report threads/messages.
  2. Define a future `JournalService` boundary for user notes and post-review tracking.
  3. Do not add broker activity sync, order tracking, or realized P&L history.
- Acceptance criteria:
  - A deterministic review can be traced to the intent and report history.
  - Journal linkage is read-only/audit-oriented, not execution-oriented.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove journal link files/tests.
- Status: `not_started`

### P14-T5 - Claude review of TradeIntent contracts

- Task id: `P14-T5`
- Title: Claude review of TradeIntent contracts
- Objective: Review frontend implications, finance-safety language, and product scope before building the deterministic trade review engine.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P14-T4`
- Implementation steps:
  1. Generate a focused Claude handoff prompt limited to TradeIntent models, context/snapshot contracts, validator outputs, and this plan section.
  2. Use Sonnet for UX/copy review; use Opus only for high-risk financial semantics disputes.
  3. Codex adjudicates findings before Phase 15 starts.
- Acceptance criteria:
  - TradeIntent contracts support stock, ETF, and options review without wheel/CSP/covered-call overfitting.
  - Any accepted fixes land before Phase 15.
- Tests to run:
  - Documentation/review task only; no tests unless fixes are accepted.
- Rollback notes:
  - Remove review notes if superseded.
- Status: `not_started`

### P14-T6 - Codex integration review for Phase 14

- Task id: `P14-T6`
- Title: Codex integration review for Phase 14
- Objective: Verify TradeIntent foundation contracts before deterministic trade review services are added.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P14-T5`
- Implementation steps:
  1. Run backend tests.
  2. Confirm TradeIntent, context, snapshot, validation, and journal-link contracts are strategy-neutral.
  3. Confirm no order execution, broker action, or advice wording was introduced.
- Acceptance criteria:
  - Phase 14 can support stock, ETF, and options trade review in Phase 15.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Reopen P14-T5 if integration issues are found.
- Status: `not_started`

## Phase 15 - Deterministic Trade Review Engine MVP

Phase goal: run one deterministic review pipeline for proposed stock, ETF, and options trades. Covered calls and cash-secured puts are early high-value workflows, but not the product identity. Long calls and long puts are included early because many retail options users are buyers, not only premium sellers.

### P15-T1 - PayoffScenarioEngine

- Task id: `P15-T1`
- Title: PayoffScenarioEngine
- Objective: Compute generic payoff/scenario outputs for stock, ETF, and option-leg intents.
- Files expected to change:
  - `backend/app/services/trade_review/payoff.py`
  - `backend/tests/services/trade_review/test_payoff.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T6`
- Implementation steps:
  1. Support stock/ETF price-change scenarios.
  2. Support long call, long put, short put, and short call single-leg scenarios using generic option-leg math.
  3. Keep multi-leg support extensible without building a full optimizer.
- Acceptance criteria:
  - Payoff outputs are deterministic and strategy-neutral.
  - No "best trade" or recommendation logic.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove payoff engine files/tests.
- Status: `not_started`

### P15-T2 - PortfolioImpactEngine

- Task id: `P15-T2`
- Title: PortfolioImpactEngine
- Objective: Calculate cash impact, collateral impact, assignment/exercise exposure, and allocation/concentration impact for a reviewed trade intent.
- Files expected to change:
  - `backend/app/services/trade_review/portfolio_impact.py`
  - `backend/tests/services/trade_review/test_portfolio_impact.py`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T1`
- Implementation steps:
  1. Consume portfolio context, market snapshots, and payoff outputs.
  2. Compute cash, reserved collateral, projected exposure, and concentration deltas.
  3. Preserve broker freshness and market quote freshness separately.
- Acceptance criteria:
  - Impact outputs are structured and report-ready.
  - Cash/collateral effects are explicit for both option sellers and option buyers.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove portfolio impact engine files/tests.
- Status: `not_started`

### P15-T3 - RiskRuleEngine integration for trade review

- Task id: `P15-T3`
- Title: RiskRuleEngine integration for trade review
- Objective: Apply deterministic risk rules to trade-review outputs.
- Files expected to change:
  - `backend/app/services/trade_review/risk.py`
  - `backend/tests/services/trade_review/test_risk.py`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T2`
- Implementation steps:
  1. Convert validation, payoff, portfolio impact, broker freshness, and market freshness results into `risk_rule_violations`.
  2. Support severity: `info`, `warning`, `violation`, `blocker`.
  3. Treat stale/unknown market quote inputs conservatively.
- Acceptance criteria:
  - Risk output is deterministic and frontend-ready.
  - No LLM-generated risk metrics.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove trade-review risk files/tests.
- Status: `not_started`

### P15-T4 - StrategyEvaluator wrappers

- Task id: `P15-T4`
- Title: StrategyEvaluator wrappers
- Objective: Add thin wrappers around the generic trade-review pipeline for early workflows.
- Files expected to change:
  - `backend/app/services/strategies/interfaces.py`
  - `backend/app/services/strategies/stock_review.py`
  - `backend/app/services/strategies/etf_review.py`
  - `backend/app/services/strategies/options_single_leg.py`
  - `backend/tests/services/strategies/test_trade_review_wrappers.py`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T3`
- Implementation steps:
  1. Define `StrategyEvaluator.evaluate(intent, portfolio_context, market_snapshot) -> StrategyReview`.
  2. Add `StockBuyReviewEvaluator`, `StockSellTrimReviewEvaluator`, `ETFReviewEvaluator`, `LongCallReviewEvaluator`, `LongPutReviewEvaluator`, `CashSecuredPutEvaluator`, and `CoveredCallEvaluator`.
  3. Keep CSP and covered call as wrappers, not core schema foundations.
- Acceptance criteria:
  - Early evaluators share the same `TradeIntent` pipeline.
  - Wheel lifecycle is not implemented here.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove strategy wrapper files/tests.
- Status: `not_started`

### P15-T5 - deterministic trade review report

- Task id: `P15-T5`
- Title: deterministic trade review report
- Objective: Generate a versioned deterministic report from trade intent, context, market snapshot, payoff, portfolio impact, and risk-rule outputs.
- Files expected to change:
  - `backend/app/services/trade_review/report.py`
  - `backend/tests/services/trade_review/test_report.py`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T4`
- Implementation steps:
  1. Include calculation versioning and data freshness snapshot.
  2. Persist or link report output through existing report history contracts.
  3. Use review/scenario wording, not advice or recommendation wording.
- Acceptance criteria:
  - Deterministic report is reproducible from structured inputs.
  - No "you should buy/sell", guaranteed-return, or execution language.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove trade review report files/tests.
- Status: `not_started`

### P15-T6 - Claude review of deterministic trade review contracts

- Task id: `P15-T6`
- Title: Claude review of deterministic trade review contracts
- Objective: Review trade-review outputs and frontend implications before a UI slice.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P15-T5`
- Implementation steps:
  1. Generate a focused Claude handoff prompt limited to trade review outputs, report shape, tests, and this plan section.
  2. Use `finance-dashboard-ux-review` and `implementation-plan-review`.
  3. Codex adjudicates findings before frontend work.
- Acceptance criteria:
  - Trade-review contracts are safe to expose in a read-only frontend.
- Tests to run:
  - Documentation/review task only; no tests unless fixes are accepted.
- Rollback notes:
  - Remove review notes if superseded.
- Status: `not_started`

### P15-T7 - Codex integration review for Phase 15

- Task id: `P15-T7`
- Title: Codex integration review for Phase 15
- Objective: Verify deterministic trade-review outputs before custom agents and frontend workspace work.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P15-T6`
- Implementation steps:
  1. Run backend tests.
  2. Confirm outputs cover stock, ETF, long call, long put, CSP, and covered-call intents.
  3. Confirm no wheel-only, options-income-only, or execution semantics were introduced.
- Acceptance criteria:
  - Phase 15 ships a generic deterministic trade-review engine.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Reopen P15-T6 if integration issues are found.
- Status: `not_started`

## Phase 16 - Custom Portfolio-Aware Agent Orchestrator

Phase goal: build workflow-first, deterministic-first agents that consume structured trade-review outputs and optionally ask an LLM to explain, summarize, or debate already-computed facts. Agents must not compute financial metrics from scratch and must not receive raw brokerage data by default.

### P16-T1 - Portfolio Context Agent

- Task id: `P16-T1`
- Title: Portfolio Context Agent
- Objective: Load approved user/account context, holdings summaries, freshness metadata, and report history references.
- Files expected to change:
  - `backend/app/services/agents/portfolio_context.py`
  - `backend/tests/services/agents/test_portfolio_context.py`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T7`
- Implementation steps:
  1. Build structured context from existing backend services.
  2. Include freshness and snapshot metadata.
  3. Exclude secrets, provider ids, account numbers, raw payloads, and unnecessary brokerage details from any LLM-bound payload.
- Acceptance criteria:
  - Agent output is structured and deterministic.
  - No private brokerage data is sent to LLMs by default.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove agent and tests.
- Status: `not_started`

### P16-T2 - Trade Review Agent

- Task id: `P16-T2`
- Title: Trade Review Agent
- Objective: Explain deterministic trade-review outputs without inventing metrics or making buy/sell recommendations.
- Files expected to change:
  - `backend/app/services/agents/trade_review.py`
  - `backend/tests/services/agents/test_trade_review.py`
  - `docs/implementation_plan.md`
- Dependencies: `P16-T1`
- Implementation steps:
  1. Consume deterministic trade-review report outputs.
  2. Explain scenario tradeoffs, blockers, and open questions.
  3. Mock LLM explanation boundary by default.
- Acceptance criteria:
  - Agent never computes financial metrics from scratch.
  - Agent avoids "you should buy/sell" wording.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove agent and tests.
- Status: `not_started`

### P16-T3 - Freshness/Guardrail Agent

- Task id: `P16-T3`
- Title: Freshness/Guardrail Agent
- Objective: Prevent stale broker or market inputs from being presented as immediately actionable.
- Files expected to change:
  - `backend/app/services/agents/freshness_guardrail.py`
  - `backend/tests/services/agents/test_freshness_guardrail.py`
  - `docs/implementation_plan.md`
- Dependencies: `P16-T2`
- Implementation steps:
  1. Review broker freshness and market quote freshness separately.
  2. Emit guardrail decisions for stale/unknown/error data.
  3. Persist guardrail outputs to agent steps.
- Acceptance criteria:
  - Stale data cannot be labeled immediately actionable.
  - Broker freshness and quote freshness remain distinct.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove agent and tests.
- Status: `not_started`

### P16-T4 - Report Composer Agent

- Task id: `P16-T4`
- Title: Report Composer Agent
- Objective: Compose deterministic trade-review outputs and approved agent explanations into a durable markdown report.
- Files expected to change:
  - `backend/app/services/agents/report_composer.py`
  - `backend/tests/services/agents/test_report_composer.py`
  - `docs/implementation_plan.md`
- Dependencies: `P16-T3`
- Implementation steps:
  1. Combine structured outputs from prior agents.
  2. Mark deterministic calculations separately from LLM-generated text.
  3. Persist the final markdown report to report history.
- Acceptance criteria:
  - Report is traceable to agent steps and deterministic inputs.
  - LLM boundary remains mocked by default.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove agent and tests.
- Status: `not_started`

### P16-T5 - Claude review of custom agent outputs

- Task id: `P16-T5`
- Title: Claude review of custom agent outputs
- Objective: Review custom-agent output contracts, report messages, and frontend implications before building the first trade-review workspace UI.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P16-T4`
- Implementation steps:
  1. Generate a focused Claude handoff prompt limited to custom agent outputs, report/agent history schemas, tests, and this plan section.
  2. Use Sonnet for UX/copy review; use Opus only for high-risk agent safety or financial reasoning disputes.
  3. Confirm deterministic calculations are visually and semantically separated from LLM-generated text.
- Acceptance criteria:
  - Agent/report output is reviewable before adding UI.
- Tests to run:
  - Documentation/review task only; no tests unless fixes are accepted.
- Rollback notes:
  - Remove review notes if superseded.
- Status: `not_started`

### P16-T6 - Codex integration review for Phase 16

- Task id: `P16-T6`
- Title: Codex integration review for Phase 16
- Objective: Verify custom-agent backend outputs before frontend workspace and TradingAgents evidence work.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P16-T5`
- Implementation steps:
  1. Run backend tests.
  2. Confirm agents consume persisted deterministic outputs rather than recomputing or inventing metrics.
  3. Confirm TradingAgents remains absent from the fast path.
- Acceptance criteria:
  - Phase 16 ships as a deterministic-first custom-agent foundation.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Reopen P16-T5 if integration issues are found.
- Status: `not_started`

## Phase 17 - TradingAgents Adapter as Async Research Evidence

Phase goal: integrate TradingAgents only as optional asynchronous stock/company research evidence. TradingAgents must stay out of the fast trade-review path and must not receive user brokerage holdings, account values, cash, broker account ids, trade journal entries, or account-specific risk thresholds by default.

### P17-T1 - optional dependency detection

- Task id: `P17-T1`
- Title: optional dependency detection
- Objective: Detect whether TradingAgents is installed without requiring it for deterministic app features.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/dependency.py`
  - `backend/tests/services/test_tradingagents_dependency.py`
  - `docs/implementation_plan.md`
- Dependencies: `P16-T6`
- Implementation steps:
  1. Add lazy import detection.
  2. Return actionable install instructions when missing.
  3. Avoid global FastAPI startup imports.
- Acceptance criteria:
  - App works without TradingAgents installed.
  - Missing dependency errors are clear and safe.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove dependency detection files/tests.
- Status: `not_started`

### P17-T2 - async research evidence interface

- Task id: `P17-T2`
- Title: async research evidence interface
- Objective: Define clean methods for ticker/company research that can run asynchronously and attach evidence to reports later.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/interfaces.py`
  - `backend/tests/services/test_tradingagents_interface.py`
  - `docs/implementation_plan.md`
- Dependencies: `P17-T1`
- Implementation steps:
  1. Add methods such as `request_stock_research`, `get_research_status`, `parse_agent_outputs`, and `map_to_report_thread`.
  2. Keep account-level portfolio/risk decisions outside TradingAgents.
  3. Send only ticker/public company research context where possible.
- Acceptance criteria:
  - Interface is stock/company research evidence only.
  - No TradingAgents source code is copied.
  - Research is optional and asynchronous.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove interface and tests.
- Status: `not_started`

### P17-T3 - research cache and budget policy

- Task id: `P17-T3`
- Title: research cache and budget policy
- Objective: Define caching and cost-control rules for light and deep ticker research.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/cache_policy.py`
  - `backend/tests/services/test_tradingagents_cache_policy.py`
  - `docs/implementation_plan.md`
- Dependencies: `P17-T2`
- Implementation steps:
  1. Cache research by ticker, research type, source set, model version, prompt version, and as-of date.
  2. Distinguish light research from deep research.
  3. Require explicit budget/latency acknowledgement for deep research before real providers are added.
- Acceptance criteria:
  - Deep research is not accidentally triggered in the fast path.
  - Cache keys do not include private brokerage data.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove cache policy files/tests.
- Status: `not_started`

### P17-T4 - mocked TradingAgents parser and report mapping

- Task id: `P17-T4`
- Title: mocked TradingAgents parser and report mapping
- Objective: Parse mocked TradingAgents research output into this project's report/agent history format.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/parser.py`
  - `backend/app/services/tradingagents_adapter/report_mapping.py`
  - `backend/tests/services/test_tradingagents_parser.py`
  - `backend/tests/services/test_tradingagents_report_mapping.py`
  - `docs/implementation_plan.md`
- Dependencies: `P17-T3`
- Implementation steps:
  1. Define a safe mocked output shape.
  2. Parse research sections, debate outputs, and final proposal text.
  3. Sanitize and tag output as stock/company research evidence.
  4. Keep final portfolio-aware conclusion owned by custom agents and deterministic services.
- Acceptance criteria:
  - Parser works with mocked outputs only.
  - Output is stored as evidence, not final portfolio-aware advice.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove parser/mapping service and tests.
- Status: `not_started`

### P17-T5 - Claude review of TradingAgents evidence boundary

- Task id: `P17-T5`
- Title: Claude review of TradingAgents evidence boundary
- Objective: Review the TradingAgents adapter outputs and UI implications before exposing stock/company research evidence in the frontend.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P17-T4`
- Implementation steps:
  1. Generate a focused Claude handoff prompt limited to TradingAgents adapter outputs, report mappings, tests, and this plan section.
  2. Confirm TradingAgents is labeled as stock/company research evidence only.
  3. Confirm account-level portfolio, collateral, option-risk, and final conclusions remain owned by custom agents and deterministic services.
- Acceptance criteria:
  - TradingAgents output cannot be mistaken for final portfolio-aware advice.
- Tests to run:
  - Documentation/review task only; no tests unless fixes are accepted.
- Rollback notes:
  - Remove review notes if superseded.
- Status: `not_started`

### P17-T6 - Codex integration review for Phase 17

- Task id: `P17-T6`
- Title: Codex integration review for Phase 17
- Objective: Verify TradingAgents adapter outputs preserve the async evidence boundary before frontend exposure.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P17-T5`
- Implementation steps:
  1. Run backend tests.
  2. Confirm TradingAgents adapter remains optional, async, and stock/company research only.
  3. Confirm no private brokerage context enters mocked prompts or cache keys.
- Acceptance criteria:
  - TradingAgents integration is optional evidence, not the center of the product.
  - Deterministic trade review works without TradingAgents installed.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Reopen P17-T5 if integration issues are found.
- Status: `not_started`

## Phase 18 - Frontend Trade Review Workspace

Phase goal: add the first user-facing trade review workspace for proposed stock, ETF, and options trades after the backend trade-review and custom-agent contracts are stable.

### P18-T1 - New Trade Review workspace shell

- Task id: `P18-T1`
- Title: New Trade Review workspace shell
- Objective: Add a read-only frontend route for creating and reviewing hypothetical trade intents.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/README.md`
  - `docs/implementation_plan.md`
- Dependencies: `P17-T6`
- Implementation steps:
  1. Ask Claude Sonnet to design and implement a New Trade Review workspace using `frontend-design` and `finance-dashboard-ux-review`.
  2. Support stock, ETF, and option intent entry using synthetic/local-safe states.
  3. Clearly label review/scenario analysis and avoid order-ticket UX.
- Acceptance criteria:
  - UI supports trade review without broker order execution.
  - No "you should buy/sell", guaranteed-return, or automated-management language.
- Tests to run:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Revert trade review workspace files and docs.
- Status: `not_started`

### P18-T2 - deterministic trade review report UI

- Task id: `P18-T2`
- Title: deterministic trade review report UI
- Objective: Render deterministic trade-review report sections, portfolio impact, cash/collateral impact, risk-rule violations, data freshness warnings, and journal/report links.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/README.md`
  - `docs/implementation_plan.md`
- Dependencies: `P18-T1`
- Implementation steps:
  1. Display deterministic calculations separately from AI explanation.
  2. Show broker freshness and market quote freshness separately.
  3. Show risk-rule violations by severity with text and icon, not color alone.
- Acceptance criteria:
  - UI distinguishes deterministic facts, optional AI explanation, and optional research evidence.
  - No trade execution UI.
- Tests to run:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Revert report UI files and docs.
- Status: `not_started`

### P18-T3 - optional research evidence display

- Task id: `P18-T3`
- Title: optional research evidence display
- Objective: Display cached or async TradingAgents stock/company research as evidence when available.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/README.md`
  - `docs/implementation_plan.md`
- Dependencies: `P18-T2`
- Implementation steps:
  1. Render research evidence as optional and subordinate to deterministic review.
  2. Show pending, unavailable, stale, and budget-required states.
  3. Do not present research output as final portfolio-aware advice.
- Acceptance criteria:
  - TradingAgents evidence is visually separate from deterministic trade-review conclusions.
  - Missing TradingAgents dependency is a graceful UI state.
- Tests to run:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Revert evidence UI files and docs.
- Status: `not_started`

### P18-T4 - Codex integration review for Phase 18

- Task id: `P18-T4`
- Title: Codex integration review for Phase 18
- Objective: Verify the frontend trade-review workspace preserves read-only, deterministic-first, portfolio-aware boundaries.
- Files expected to change:
  - `docs/implementation_plan.md`
- Dependencies: `P18-T3`
- Implementation steps:
  1. Run backend and frontend tests.
  2. Confirm no order tickets, broker actions, or execution affordances were added.
  3. Confirm UI remains broader than options income, CSP, covered call, or wheel strategy.
- Acceptance criteria:
  - Phase 18 ships a safe portfolio-aware trade review workspace.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
- Rollback notes:
  - Reopen P18-T3 if integration issues are found.
- Status: `not_started`

## Future Layer - Broker Activities, Transactions, and Strategy Memory

This future layer is intentionally deferred until current-position sync, the thin dashboard,
market data contracts, the deterministic risk engine, and trade-intent review foundations are
stable. It should not block Phase 14 or Phase 15.

Purpose:

- Current broker position/balance sync answers "what does the account currently hold?"
- Broker activities/transactions answer "what happened historically in the account?"
- Historical activity is needed for realized premium tracking, option assignment/exercise/
  expiration detection, dividend/interest/fee review, tax-lot-style review, and lifecycle
  reconstruction.

Design decisions:

- Keep current position/balance sync as the source of current account state.
- Add activities as a separate read-only sync layer, not as a replacement for position sync.
- Store sanitized raw provider activities separately first; normalize selected events into
  app-level activity records, trade journal entries, premium income records, and later
  lifecycle records.
- Activities may be cached, delayed, partial, or daily. Do not treat them as intraday
  real-time trade/execution data.
- Keep orders separate from activities. Orders are read-only intent/status data; activities
  are historical account events.
- Do not add automatic trading, order placement, cancellation, disconnect, or destructive
  broker actions.

Candidate future tables/models:

- `broker_activities`: sanitized provider activity records with provider activity id,
  broker account id, type/subtype, symbol/option symbol, quantity, price, amount,
  trade date, settlement date, source/freshness metadata, and sanitized raw payload.
- `broker_activity_sync_runs`: activity-history sync attempts, date ranges, status,
  counts, warnings, sanitized error summaries, and freshness timestamps.
- `broker_orders`: optional later read-only order status/history, kept separate from
  activities and never used for order management.
- `trade_journal_entries`: manual/system notes, reviewed trade intents, and user-reviewed
  annotations.
- `premium_income_records`: normalized option premium credits/debits and realized
  premium capture after reconciliation.
- `wheel_cycles` and `wheel_cycle_events`: later deterministic lifecycle reconstruction
  from trade intents, activities, assignment, stock ownership, and covered-call reviews.

Candidate future tasks:

- `BA-T1` - BrokerActivityProvider interface and mocked SnapTrade activities contract.
- `BA-T2` - `broker_activities` and `broker_activity_sync_runs` schema/migration.
- `BA-T3` - SnapTrade activities sync, mock-first, sanitized payload persistence only.
- `BA-T4` - activity freshness model and dashboard activity sync status.
- `BA-T5` - transaction normalization candidates for trade journal and premium records.
- `BA-T6` - assignment/exercise/expiration detection with deterministic regression tests.
- `BA-T7` - lifecycle reconstruction as user-reviewable candidates, not automatic conclusions.

MVP boundary:

- MVP can store and display sanitized activity history plus freshness.
- MVP should not infer final wheel-cycle conclusions without an audit trail.
- MVP should not use activities for automatic trading or real-time execution confirmation.

## Future Documentation Cleanup

### DOC-T1 - README roadmap realignment

- Task id: `DOC-T1`
- Title: README roadmap realignment
- Objective: Update public README language after the architecture and implementation roadmap realignment.
- Files expected to change:
  - `README.md`
  - `docs/implementation_plan.md`
- Dependencies: Phase 10 roadmap approval.
- Implementation steps:
  1. Update README current status to reflect completed backend progress.
  2. Update README product direction to emphasize the portfolio-aware trade review and risk copilot.
  3. Update quickstart and roadmap language without adding code.
- Acceptance criteria:
  - README accurately describes current backend status and revised agentic product direction.
  - No code changes.
- Tests to run:
  - `git diff --check`
- Rollback notes:
  - Revert README and plan notes.
- Status: `not_started`
