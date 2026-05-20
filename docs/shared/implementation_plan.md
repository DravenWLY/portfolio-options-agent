# Implementation Plan

Active and future implementation tasks only. Completed Phase 1-16 history lives in `docs/shared/completed_phases_log.md`. High-level review context lives in `docs/shared/current_roadmap.md`; role-specific briefs live in the agent folders under `docs/`.

Default reading rule: load this file for the current phase and next phase only. Avoid loading `docs/shared/completed_phases_log.md` unless a task explicitly needs historical verification details.

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

## Phase 17 - TradingAgents/Public Research Evidence Adapter

Phase goal: integrate TradingAgents and/or other public research sources only as optional asynchronous public stock/company research evidence. TradingAgents must stay out of the fast trade-review path, must not become the portfolio-aware decision engine, and must not receive user brokerage holdings, account values, cash, broker account ids, trade journal entries, or account-specific risk thresholds by default.

### P17-T1 - optional dependency detection

- Task id: `P17-T1`
- Title: optional dependency detection
- Objective: Detect whether TradingAgents is installed without requiring it for deterministic app features.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/dependency.py`
  - `backend/tests/services/test_tradingagents_dependency.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P16B-T4`
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
- Objective: Define clean methods for public ticker/company research that can run asynchronously and attach evidence to reports later.
- Files expected to change:
  - `backend/app/services/tradingagents_adapter/interfaces.py`
  - `backend/tests/services/test_tradingagents_interface.py`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P17-T1`
- Implementation steps:
  1. Add methods such as `request_stock_research`, `get_research_status`, `parse_agent_outputs`, and `map_to_report_thread`.
  2. Keep account-level portfolio/risk decisions outside TradingAgents and other public evidence adapters.
  3. Send only ticker/public company research context where possible.
- Acceptance criteria:
  - Interface is public stock/company research evidence only.
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
  - `docs/shared/implementation_plan.md`
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
  - `docs/shared/implementation_plan.md`
- Dependencies: `P17-T3`
- Implementation steps:
  1. Define a safe mocked output shape.
  2. Parse research sections, debate outputs, and final proposal text.
  3. Sanitize and tag output as public stock/company research evidence.
  4. Keep final portfolio-aware conclusion owned by custom agents and deterministic services.
- Acceptance criteria:
  - Parser works with mocked outputs only.
  - Output is stored as evidence, not final portfolio-aware advice.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Remove parser/mapping service and tests.
- Status: `not_started`

### P17-T5 - Claude review of public research evidence boundary

- Task id: `P17-T5`
- Title: Claude review of public research evidence boundary
- Objective: Review the TradingAgents/public evidence adapter outputs and UI implications before exposing stock/company research evidence in the frontend.
- Files expected to change:
  - `docs/shared/implementation_plan.md`
- Dependencies: `P17-T4`
- Implementation steps:
  1. Generate a focused Claude handoff prompt limited to TradingAgents adapter outputs, report mappings, tests, and this plan section.
  2. Confirm TradingAgents is labeled as public stock/company research evidence only.
  3. Confirm account-level portfolio, collateral, option-risk, and final conclusions remain owned by custom agents and deterministic services.
- Acceptance criteria:
  - Public research evidence cannot be mistaken for final portfolio-aware advice.
- Tests to run:
  - Documentation/review task only; no tests unless fixes are accepted.
- Rollback notes:
  - Remove review notes if superseded.
- Status: `not_started`

### P17-T6 - Codex integration review for Phase 17

- Task id: `P17-T6`
- Title: Codex integration review for Phase 17
- Objective: Verify TradingAgents/public evidence adapter outputs preserve the async evidence boundary before frontend exposure.
- Files expected to change:
  - `docs/shared/implementation_plan.md`
- Dependencies: `P17-T5`
- Implementation steps:
  1. Run backend tests.
  2. Confirm TradingAgents/public evidence adapters remain optional, async, and public stock/company research only.
  3. Confirm no private brokerage context enters mocked prompts or cache keys.
- Acceptance criteria:
  - TradingAgents/public research integration is optional evidence, not the center of the product.
  - Deterministic trade review works without TradingAgents installed.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest`
- Rollback notes:
  - Reopen P17-T5 if integration issues are found.
- Status: `not_started`

## Phase 18 - Frontend Trade Review Workspace

Phase goal: add the first user-facing trade review workspace for proposed stock, ETF, and options trades after the backend trade-review, Phase 16A deterministic components, and Phase 16B orchestration contract are stable. Rich research/debate UI waits for Phase 17 contracts.

### P18-T1 - New Trade Review workspace shell

- Task id: `P18-T1`
- Title: New Trade Review workspace shell
- Objective: Add a read-only frontend route for creating and reviewing hypothetical trade intents.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/README.md`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P16A-T6`, `P16B-T1`
- Implementation steps:
  1. Ask Claude Sonnet to design and implement a New Trade Review workspace using `frontend-design` and `finance-dashboard-ux-review`.
  2. Support stock, ETF, and option intent entry using synthetic/local-safe states.
  3. Clearly label review/scenario analysis and avoid order-ticket UX.
- Acceptance criteria:
  - UI supports trade review without broker order execution.
  - No "you should buy/sell", guaranteed-return, or automated-management language.
  - A typed sanitized trade-review read schema and forbidden-field tests exist before frontend consumes backend data.
  - Coverage/collateral netting is either implemented or visibly caveated.
  - Real market data is not required for local MVP demo; if the UI implies quote-current options review for external beta, a real REST snapshot provider is required first.
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
  - `docs/shared/implementation_plan.md`
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
- Objective: Display cached or async public stock/company research as evidence when available.
- Files expected to change:
  - `frontend/src/*`
  - `frontend/README.md`
  - `docs/shared/implementation_plan.md`
- Dependencies: `P18-T2`, `P17-T6`
- Implementation steps:
  1. Render research evidence as optional and subordinate to deterministic review.
  2. Show pending, unavailable, stale, and budget-required states.
  3. Do not present research output as final portfolio-aware advice.
- Acceptance criteria:
  - TradingAgents/public research evidence is visually separate from deterministic trade-review conclusions.
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
  - `docs/shared/implementation_plan.md`
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
stable. It should not block Phase 16 agent work or Phase 18 trade-review workspace work.

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
  - `docs/shared/implementation_plan.md`
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
