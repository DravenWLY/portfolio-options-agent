# Implementation Plan

Active and future implementation tasks only. Completed Phase 1-10 history lives in `docs/completed_phases_log.md`. High-level review context lives in `docs/current_roadmap.md` and `docs/agent_context/`.

Default reading rule: load this file for the current phase and next phase only. Avoid loading `docs/completed_phases_log.md` unless a task explicitly needs historical verification details.

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

## Phase 12 - Market Data Contracts and Manual Provider

Phase goal: define quote and option-chain contracts after report history and the first dashboard shell, while keeping broker freshness separate from market quote freshness.

### P12-T1 - MarketDataProvider interface

- Task id: `P12-T1`
- Title: MarketDataProvider interface
- Objective: Define provider-agnostic stock quote and intraday bar interfaces separate from broker sync.
- Files expected to change:
  - `backend/app/services/market_data/__init__.py`
  - `backend/app/services/market_data/interfaces.py`
  - `backend/app/services/market_data/models.py`
  - `backend/tests/unit/test_module_boundaries.py`
  - `backend/tests/services/market_data/test_interfaces.py`
  - `docs/implementation_plan.md`
- Dependencies: `P11-T6`
- Implementation steps:
  1. Add top-of-module documentation explaining broker-vs-quote freshness separation.
  2. Define market quote provider protocol and response models.
  3. Use `freshness_scope="market_quote"` for market freshness responses.
  4. Add an import-boundary test: `app.services.market_data.*` must not import from `app.services.broker_import.*`.
- Acceptance criteria:
  - Market data interfaces are separate from broker sync.
  - Broker freshness and quote freshness are not collapsed into one timestamp.
  - No real provider calls by default.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove market data interface files/tests.
- Status: `not_started`

### P12-T2 - OptionDataProvider interface

- Task id: `P12-T2`
- Title: OptionDataProvider interface
- Objective: Define option quote, option chain, IV, and Greeks provider interfaces.
- Files expected to change:
  - `backend/app/services/market_data/interfaces.py`
  - `backend/app/services/market_data/models.py`
  - `backend/tests/services/market_data/test_option_interfaces.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T1`
- Implementation steps:
  1. Add option expirations, chain, snapshot, and quote methods.
  2. Include IV and Greeks fields.
  3. Include quote timestamp, provider, and quote freshness.
- Acceptance criteria:
  - Option market data is represented without broker account coupling.
  - No option screener behavior is implemented yet.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Revert option interface additions.
- Status: `not_started`

### P12-T3 - quote freshness model

- Task id: `P12-T3`
- Title: quote freshness model
- Objective: Centralize live/delayed/stale/EOD quote freshness classification.
- Files expected to change:
  - `backend/app/services/market_data/freshness.py`
  - `backend/tests/services/market_data/test_freshness.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T2`
- Implementation steps:
  1. Define quote freshness statuses and data modes.
  2. Implement timestamp and provider-mode based classification.
  3. Keep broker sync freshness separate.
- Acceptance criteria:
  - Stale quote data is never labeled immediately actionable.
  - Market freshness responses use `freshness_scope="market_quote"`.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove quote freshness module/tests.
- Status: `not_started`

### P12-T4 - market quote response models

- Task id: `P12-T4`
- Title: market quote response models
- Objective: Add API-facing schemas for stock quotes, option quotes, option chains, and provider status.
- Files expected to change:
  - `backend/app/schemas/market_data.py`
  - `backend/tests/unit/test_market_data_schemas.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T3`
- Implementation steps:
  1. Define quote and option chain response schemas.
  2. Include provider, timestamp, and freshness fields.
  3. Add exact-set OpenAPI tests for market quote freshness schemas.
- Acceptance criteria:
  - Market schemas distinguish quote freshness from broker freshness.
  - No broker holdings/cash fields appear in market quote schemas.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Revert market data schemas and tests.
- Status: `not_started`

### P12-T5 - manual/mock provider

- Task id: `P12-T5`
- Title: manual/mock provider
- Objective: Add a deterministic market data provider for manually entered or synthetic quote snapshots.
- Files expected to change:
  - `backend/app/services/market_data/manual_provider.py`
  - `backend/tests/services/market_data/test_manual_provider.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T4`
- Implementation steps:
  1. Implement provider using explicit synthetic quote inputs.
  2. Mark freshness based on supplied quote timestamps.
  3. Avoid network and API keys.
- Acceptance criteria:
  - Market data tests run without external providers.
  - Manual/mock quotes can feed future deterministic risk tests.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove manual provider and tests.
- Status: `not_started`

### P12-T6 - mocked market data tests

- Task id: `P12-T6`
- Title: mocked market data tests
- Objective: Cover provider interfaces, manual/mock provider behavior, and quote freshness.
- Files expected to change:
  - `backend/tests/services/market_data/*`
  - `backend/tests/unit/test_module_boundaries.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T5`
- Implementation steps:
  1. Add provider contract tests.
  2. Add quote freshness tests.
  3. Add stale quote warning tests.
  4. Confirm no external provider calls run by default.
- Acceptance criteria:
  - Market data layer is safe to use without real credentials.
  - Market data layer remains separate from broker sync.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove market data tests and fixtures.
- Status: `not_started`

## Phase 13 - Deterministic Options/Risk Engine MVP

Phase goal: implement deterministic calculations before custom agents explain them. Python calculates all metrics; LLMs may explain structured results later but must not invent metrics.

### P13-T1 - option formulas

- Task id: `P13-T1`
- Title: option formulas
- Objective: Implement deterministic formulas for premium yield, annualized ROI, breakeven, downside buffer, bid-ask spread percentage, and premium capture.
- Files expected to change:
  - `backend/app/services/options/formulas.py`
  - `backend/tests/services/options/test_formulas.py`
  - `docs/implementation_plan.md`
- Dependencies: `P12-T6`
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
- Status: `not_started`

### P13-T2 - collateral and free cash

- Task id: `P13-T2`
- Title: collateral and free cash
- Objective: Calculate short-put collateral, option collateral usage, free cash, and cash reserved for DCA/buy-the-dip.
- Files expected to change:
  - `backend/app/services/risk/collateral.py`
  - `backend/tests/services/risk/test_collateral.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T1`
- Implementation steps:
  1. Calculate collateral from short put positions.
  2. Distinguish total cash, reserved collateral, and free cash.
  3. Keep account values synthetic in tests.
- Acceptance criteria:
  - Cash/collateral outputs are deterministic and account scoped.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove collateral service and tests.
- Status: `not_started`

### P13-T3 - assignment scenario

- Task id: `P13-T3`
- Title: assignment scenario
- Objective: Project cash, holdings, concentration, and allocation after all or selected short puts are assigned.
- Files expected to change:
  - `backend/app/services/risk/assignment.py`
  - `backend/tests/services/risk/test_assignment.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T2`
- Implementation steps:
  1. Project assigned shares and cash usage.
  2. Calculate projected allocation and concentration.
  3. Emit structured scenario outputs.
- Acceptance criteria:
  - Assignment projections do not depend on LLMs.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove assignment service and tests.
- Status: `not_started`

### P13-T4 - covered call eligibility

- Task id: `P13-T4`
- Title: covered call eligibility
- Objective: Detect covered call eligibility from stock and option holdings.
- Files expected to change:
  - `backend/app/services/options/covered_calls.py`
  - `backend/tests/services/options/test_covered_calls.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T3`
- Implementation steps:
  1. Detect 100-share lots by account and symbol.
  2. Account for existing short calls.
  3. Return deterministic eligibility and warnings.
- Acceptance criteria:
  - Eligibility results are structured and testable.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove covered call service and tests.
- Status: `not_started`

### P13-T5 - CSP candidate evaluator

- Task id: `P13-T5`
- Title: CSP candidate evaluator
- Objective: Evaluate cash-secured put candidates from deterministic option, account, and risk inputs.
- Files expected to change:
  - `backend/app/services/options/csp.py`
  - `backend/tests/services/options/test_csp.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T4`
- Implementation steps:
  1. Apply deterministic filters for IV, volume/open interest, spread, DTE, collateral, and assignment scenario.
  2. Accept manual/mock market inputs.
  3. Do not hardcode private strategy thresholds.
- Acceptance criteria:
  - CSP results are deterministic and explainable.
  - Strategy thresholds come from config or test fixtures, not personal real values.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove CSP evaluator and tests.
- Status: `not_started`

### P13-T6 - allocation and concentration risk

- Task id: `P13-T6`
- Title: allocation and concentration risk
- Objective: Calculate allocation drift, sector/concentration exposure, and risk-rule violations.
- Files expected to change:
  - `backend/app/services/risk/allocation.py`
  - `backend/app/services/risk/violations.py`
  - `backend/tests/services/risk/test_allocation.py`
  - `backend/tests/services/risk/test_violations.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T5`
- Implementation steps:
  1. Calculate target allocation drift and concentration.
  2. Emit `risk_rule_violations` as deterministic structured outputs.
  3. Use severity values `info`, `warning`, `violation`, and `blocker`.
- Acceptance criteria:
  - Risk-rule violations are structured, deterministic, and severity tagged.
  - LLMs are not used to create or modify violations.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove allocation/risk violation services and tests.
- Status: `not_started`

### P13-T7 - deterministic risk report

- Task id: `P13-T7`
- Title: deterministic risk report
- Objective: Combine portfolio summary, market inputs, option formulas, collateral, assignment, and violations into a deterministic risk report.
- Files expected to change:
  - `backend/app/services/risk/report.py`
  - `backend/tests/services/risk/test_report.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T6`
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
- Status: `not_started`

## Phase 14 - Custom Portfolio-Aware Agent Orchestrator

Phase goal: build workflow-first, deterministic-first agents that consume structured portfolio/risk outputs and optionally ask an LLM to explain, summarize, or debate already-computed facts.

### P14-T1 - Portfolio Context Agent

- Task id: `P14-T1`
- Title: Portfolio Context Agent
- Objective: Load user/account context, holdings, cash, broker freshness, and report history references.
- Files expected to change:
  - `backend/app/services/agents/portfolio_context.py`
  - `backend/tests/services/agents/test_portfolio_context.py`
  - `docs/implementation_plan.md`
- Dependencies: `P13-T7`
- Implementation steps:
  1. Build structured context from existing backend services.
  2. Include freshness and snapshot metadata.
  3. Persist outputs to agent steps.
- Acceptance criteria:
  - Agent output is structured and deterministic.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove agent and tests.
- Status: `not_started`

### P14-T2 - Options Income Agent

- Task id: `P14-T2`
- Title: Options Income Agent
- Objective: Interpret deterministic CSP/covered-call results without inventing metrics.
- Files expected to change:
  - `backend/app/services/agents/options_income.py`
  - `backend/tests/services/agents/test_options_income.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T1`
- Implementation steps:
  1. Consume deterministic option/risk engine outputs.
  2. Classify candidates as do/wait/avoid/conditional based on structured inputs.
  3. Mock LLM explanation boundary by default.
- Acceptance criteria:
  - Agent never computes financial metrics from scratch.
  - Default tests make no LLM calls.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove agent and tests.
- Status: `not_started`

### P14-T3 - Collateral and Assignment Risk Agent

- Task id: `P14-T3`
- Title: Collateral and Assignment Risk Agent
- Objective: Review collateral usage, free cash, and assignment scenarios from deterministic outputs.
- Files expected to change:
  - `backend/app/services/agents/collateral_assignment.py`
  - `backend/tests/services/agents/test_collateral_assignment.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T2`
- Implementation steps:
  1. Consume collateral and assignment services.
  2. Flag blocker/violation conditions from existing `risk_rule_violations`.
  3. Persist the agent decision and evidence.
- Acceptance criteria:
  - Agent reasoning is traceable to deterministic inputs.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove agent and tests.
- Status: `not_started`

### P14-T4 - Allocation Risk Agent

- Task id: `P14-T4`
- Title: Allocation Risk Agent
- Objective: Explain allocation drift and concentration risks from deterministic analysis.
- Files expected to change:
  - `backend/app/services/agents/allocation_risk.py`
  - `backend/tests/services/agents/test_allocation_risk.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T3`
- Implementation steps:
  1. Consume allocation/concentration outputs.
  2. Highlight account-level and user-level exposures.
  3. Persist structured conclusions to report history.
- Acceptance criteria:
  - Agent output references deterministic violations and inputs.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove agent and tests.
- Status: `not_started`

### P14-T5 - Freshness/Guardrail Agent

- Task id: `P14-T5`
- Title: Freshness/Guardrail Agent
- Objective: Prevent stale broker or market inputs from being presented as immediately actionable.
- Files expected to change:
  - `backend/app/services/agents/freshness_guardrail.py`
  - `backend/tests/services/agents/test_freshness_guardrail.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T4`
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

### P14-T6 - Report Composer Agent

- Task id: `P14-T6`
- Title: Report Composer Agent
- Objective: Compose custom-agent outputs into a durable markdown report.
- Files expected to change:
  - `backend/app/services/agents/report_composer.py`
  - `backend/tests/services/agents/test_report_composer.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T5`
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

## Phase 15 - TradingAgents Adapter

Phase goal: integrate TradingAgents only as an optional stock/company research evidence stream after this project already has portfolio context, deterministic risk outputs, and durable report/agent history.

### P15-T1 - optional dependency detection

- Task id: `P15-T1`
- Title: optional dependency detection
- Objective: Detect whether TradingAgents is installed without requiring it for deterministic app features.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/dependency.py`
  - `backend/tests/services/test_tradingagents_dependency.py`
  - `docs/implementation_plan.md`
- Dependencies: `P14-T6`
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

### P15-T2 - adapter interface

- Task id: `P15-T2`
- Title: adapter interface
- Objective: Define clean methods for TradingAgents-backed stock/company research.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/interfaces.py`
  - `backend/tests/services/test_tradingagents_interface.py`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T1`
- Implementation steps:
  1. Add methods such as `run_stock_research`, `run_market_brief`, `run_agent_workflow`, `parse_agent_outputs`, and `map_to_report_thread`.
  2. Keep account-level portfolio/risk decisions outside TradingAgents.
  3. Keep adapter optional.
- Acceptance criteria:
  - Interface is stock/company research only.
  - No TradingAgents source code is copied.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove interface and tests.
- Status: `not_started`

### P15-T3 - missing dependency fallback

- Task id: `P15-T3`
- Title: missing dependency fallback
- Objective: Provide safe API/service behavior when TradingAgents is unavailable.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/errors.py`
  - `backend/tests/services/test_tradingagents_missing.py`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T2`
- Implementation steps:
  1. Add adapter errors for missing dependency and unsupported workflow.
  2. Ensure deterministic portfolio/options/risk features still work.
  3. Add tests without TradingAgents installed.
- Acceptance criteria:
  - Missing TradingAgents disables only TradingAgents-powered stock research.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove fallback errors/tests.
- Status: `not_started`

### P15-T4 - mocked TradingAgents output parser

- Task id: `P15-T4`
- Title: mocked TradingAgents output parser
- Objective: Parse mocked TradingAgents research output into this project's report/agent history format.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/parser.py`
  - `backend/tests/services/test_tradingagents_parser.py`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T3`
- Implementation steps:
  1. Define a safe mocked output shape.
  2. Parse research sections, debate outputs, and final proposal text.
  3. Sanitize and tag output as stock/company research evidence.
- Acceptance criteria:
  - Parser works with mocked outputs only.
  - Output is stored as evidence, not final portfolio-aware advice.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove parser and tests.
- Status: `not_started`

### P15-T5 - map TradingAgents output into report messages and agent steps

- Task id: `P15-T5`
- Title: TradingAgents report mapping
- Objective: Attach TradingAgents stock/company research to report history without letting it own portfolio decisions.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/report_mapping.py`
  - `backend/tests/services/test_tradingagents_report_mapping.py`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T4`
- Implementation steps:
  1. Map parsed TradingAgents sections into report messages and agent steps.
  2. Tag content as `tradingagents_stock_research`.
  3. Keep final portfolio-aware conclusion owned by custom agents and deterministic services.
- Acceptance criteria:
  - TradingAgents output is traceable and optional.
  - No TradingAgents core edits, submodule, or source copy.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove mapping service and tests.
- Status: `not_started`

## Phase 16 - Frontend Agent Workspace B

Phase goal: add the review workspace for reports, agent runs, risk debates, and optional TradingAgents research after the backend has durable report/agent history and custom agent outputs.

### P16-T1 - report detail

- Task id: `P16-T1`
- Title: report detail
- Objective: Show report messages and final markdown report in the frontend.
- Files expected to change:
  - `frontend/*`
  - `docs/implementation_plan.md`
- Dependencies: `P15-T5`
- Implementation steps:
  1. Add report detail route/page.
  2. Render messages, final markdown, and metadata.
  3. Distinguish deterministic content from narrative content.
- Acceptance criteria:
  - Report detail can review prior reports.
  - No trade execution UI.
- Tests to run:
  - Frontend build/typecheck and UI smoke test.
- Rollback notes:
  - Revert report detail UI.
- Status: `not_started`

### P16-T2 - agent run monitor

- Task id: `P16-T2`
- Title: agent run monitor
- Objective: Show run status, step timeline, errors, retry notices, and costs.
- Files expected to change:
  - `frontend/*`
  - `docs/implementation_plan.md`
- Dependencies: `P16-T1`
- Implementation steps:
  1. Render agent run timeline from backend run/step APIs.
  2. Show deterministic inputs/outputs and future LLM usage separately.
  3. Add empty/loading/error states.
- Acceptance criteria:
  - User can inspect run progress and step outputs.
- Tests to run:
  - Frontend build/typecheck and UI smoke test.
- Rollback notes:
  - Revert agent run monitor UI.
- Status: `not_started`

### P16-T3 - risk review workspace

- Task id: `P16-T3`
- Title: risk review workspace
- Objective: Present collateral, assignment, allocation, and risk-rule violations as an operator review surface.
- Files expected to change:
  - `frontend/*`
  - `docs/implementation_plan.md`
- Dependencies: `P16-T2`
- Implementation steps:
  1. Show deterministic risk sections.
  2. Highlight `risk_rule_violations` by severity.
  3. Avoid buy/sell/execute controls.
- Acceptance criteria:
  - Risk workspace distinguishes review from execution.
- Tests to run:
  - Frontend build/typecheck and UI smoke test.
- Rollback notes:
  - Revert risk review UI.
- Status: `not_started`

### P16-T4 - TradingAgents research section

- Task id: `P16-T4`
- Title: TradingAgents research section
- Objective: Display optional TradingAgents stock/company research evidence inside reports.
- Files expected to change:
  - `frontend/*`
  - `docs/implementation_plan.md`
- Dependencies: `P16-T3`
- Implementation steps:
  1. Render TradingAgents output as a labeled research evidence stream.
  2. Keep it visually separate from deterministic portfolio/risk outputs.
  3. Show missing-dependency state if TradingAgents is unavailable.
- Acceptance criteria:
  - UI does not imply TradingAgents owns portfolio-aware conclusions.
- Tests to run:
  - Frontend build/typecheck and UI smoke test.
- Rollback notes:
  - Revert TradingAgents research UI.
- Status: `not_started`

### P16-T5 - agent disagreement and guardrail display

- Task id: `P16-T5`
- Title: agent disagreement and guardrail display
- Objective: Show custom-agent disagreement, freshness blockers, and guardrail outcomes.
- Files expected to change:
  - `frontend/*`
  - `docs/implementation_plan.md`
- Dependencies: `P16-T4`
- Implementation steps:
  1. Render agent disagreement and guardrail summaries.
  2. Show broker freshness and market quote freshness separately.
  3. Make blocker conditions visually clear without suggesting trade execution.
- Acceptance criteria:
  - UI separates deterministic calculations, custom-agent reasoning, and TradingAgents narrative.
  - No automatic trading or order placement UI.
- Tests to run:
  - Frontend build/typecheck and UI smoke test.
- Rollback notes:
  - Revert guardrail display UI.
- Status: `not_started`

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
  2. Update README product direction to emphasize the portfolio-aware options income and risk copilot.
  3. Update quickstart and roadmap language without adding code.
- Acceptance criteria:
  - README accurately describes current backend status and revised agentic product direction.
  - No code changes.
- Tests to run:
  - `git diff --check`
- Rollback notes:
  - Revert README and plan notes.
- Status: `not_started`
