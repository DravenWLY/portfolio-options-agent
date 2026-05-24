# Implementation Plan

Active and future implementation tasks only. Completed phase history lives in `docs/shared/completed_phases_log.md`. High-level review context lives in `docs/shared/current_roadmap.md`; role-specific briefs live in the agent folders under `docs/`.

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

## Recently Completed

Phase 18A - Frontend Trade Review Workspace Readiness is complete and archived in `docs/shared/completed_phases_log.md`.
Phase 18B - Frontend Trade Review Workspace Expansion is complete and archived in `docs/shared/completed_phases_log.md`; P18B-T3 remains deferred pending reviewed Phase 17 backend evidence contracts.
Phase 18C - Real Portfolio-Backed Trade Review Workspace is complete and archived in `docs/shared/completed_phases_log.md`.
Phase 17A - Public Research Evidence Agent MVP is complete and archived in `docs/shared/completed_phases_log.md`; deep TradingAgents execution, real LLM/API calls, debate loops, and frontend research-evidence UI remain frozen pending separate PM reactivation.

Phase 19A - Basic Portfolio-Aware LLM Agent Team + Analysis Console is complete and archived in `docs/shared/completed_phases_log.md`; real Google/Gemini provider work remains a separate reviewed gate.
Phase 19B - Real LLM Provider Gate is complete and archived in `docs/shared/completed_phases_log.md`; mock remains default and live provider use remains backend-only explicit opt-in.
Phase 19C - Agent-Team Evidence and Prompt Foundation is complete and archived in `docs/shared/completed_phases_log.md`; live LLM/API smoke testing remains a separate future gate.
Phase 20A - Modern Portfolio Desk Frontend Integration is complete and archived in `docs/shared/completed_phases_log.md`; remaining placeholder cards should be wired through Phase 20B backend contracts before removing demo labels.

## Phase 20B - Modern Portfolio Desk backend contracts (placeholder wire-up)

Phase goal: deliver the missing backend reads so Phase 20A's `demo · not yet connected` placeholder cards can be replaced with real, sanitized data. Each task below is a separate Codex C / Codex B backend slice. None blocks P20A.

Phase 20B is not a frontend redesign phase. It exists to turn the most useful Phase 20A placeholder surfaces into real backend-backed reads after the prototype-fidelity UI stabilizes. Until a specific P20B task is implemented and reviewed, Claude A should keep the corresponding card visibly labeled `demo · not yet connected` and must not invent frontend-only data fields.

Shared Phase 20B contract rules:

- Keep all endpoints read-only.
- Use synthetic tests and fixtures only.
- Preserve existing Trade Review and Agent Console endpoints unchanged.
- Do not expose raw holdings, raw positions, cash balances, buying power, account values, broker/provider ids, provider contract ids, raw payloads, trade-journal entries, account-specific thresholds, secrets, prompts, or provider traces.
- Preserve separate broker snapshot freshness, market quote freshness, and agent/provider availability concepts.
- Return display-ready labels/statuses from backend where possible so frontend does not calculate financial facts.
- Frontend may format dates, labels, and already-safe strings, but must not compute portfolio metrics, risk counts, readiness, cash impact, collateral, or allocation values.
- Add schema/mapper forbidden-field tests for every response shape before Claude A consumes the contract.
- Prefer small endpoints with stable typed response schemas over broad dashboard blobs.

Claude A guidance while Phase 20B is partially implemented:

- Dashboard readiness, risk-alert, and recent-review cards may consume P20B-T1/T1A/T2/T3 only with visible `demo · not yet connected` labels while those endpoints remain synthetic-demo.
- Report and standalone portfolio-context cards remain placeholder/demo cards until P20B-T4/P20B-T5 are implemented and reviewed.
- Placeholder constants must live in one frontend demo-data module and every non-backed card must show `demo · not yet connected`.
- Do not create ad hoc API clients for proposed P20B paths until Codex C implements and Codex B reviews the backend contract.
- Do not hide missing backend work behind realistic account names, realistic dollar precision, or personal policy strings.

### P20B-T1 - persisted trade review list contract

- Task id: `P20B-T1`
- Title: persisted trade review list contract
- Objective: Add a sanitized read contract for recent trade-review runs so Dashboard "Recent trade reviews" and Reports list placeholders can be backed by real app-owned review history.
- Proposed endpoint: `GET /users/{uid}/trade-reviews`
- Frontend consumers:
  - Dashboard recent reviews table.
  - Reports list, if reports are represented as saved/generated review artifacts.
- Expected safe response fields:
  - `review_id` or opaque `review_reference`
  - `created_at`
  - `supported_flow`
  - `review_flow_label`
  - `symbol_or_underlying`
  - `review_actionability_status`
  - `highest_severity`
  - `report_status` such as `preview_only`, `saved`, `generated`, `unavailable`
  - `source_mode` such as `synthetic_preview`, `portfolio_preview`, `saved_review`
  - optional `broker_snapshot_freshness_label`
  - optional `market_quote_freshness_label`
- Explicitly forbidden:
  - raw submitted trade intent payloads
  - raw report body
  - account ids / provider ids
  - holdings / positions / quantities
  - cash, buying power, collateral, account values
  - account-specific thresholds
- Backend notes:
  - Current preview routes are stateless, so Codex B must decide whether this task first persists preview runs or only lists already-persisted report history.
  - Prefer opaque review references over sequential ids in frontend-facing payloads.
  - Do not include full deterministic report details; link to a future detail contract instead.
- Tests required:
  - response-model forbidden-field sweep
  - empty list state
  - mixed actionability statuses
  - mixed source modes
  - local access/auth guard consistent with existing routes
- Status: `done`
- Verification notes:
  - 2026-05-23 Codex C added the initial sanitized read contract for `GET /users/{uid}/trade-reviews`: typed `TradeReviewListRead` / `TradeReviewListItemRead` schemas, a synthetic/demo read service, and a protected user route.
  - The response is list-only and includes opaque `review_reference`, display labels, actionability/severity/report/source statuses, and optional broker/market freshness labels. It intentionally excludes raw submitted intents, report bodies, holdings/positions/quantities, cash/buying power/collateral/account values, broker/provider ids, thresholds, prompts, LLM responses, and provider traces.
  - Current implementation uses deterministic synthetic/demo rows plus an empty-list state because preview runs are still stateless; real persistence source remains a Codex B design decision before Claude A consumes this as production-backed data.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q` -> `41 passed in 0.13s`.
  - Codex B review (2026-05-23): **PASS as a frontend-readiness contract only**. Endpoint placement under `/users/{uid}/trade-reviews` is acceptable, the schema is narrow/list-only, and privacy tests cover the right forbidden fields. Persistence is not required before marking this contract slice done, but frontend must keep the card visibly demo/not connected until a real app-owned persisted review source exists.
  - Follow-up P20B-T1A completed the required list-level synthetic/demo source metadata. Claude A may consume this endpoint only with visible `demo · not yet connected` labeling until a real persisted source exists.

### P20B-T1A - trade review list demo-source labeling

- Task id: `P20B-T1A`
- Title: trade review list demo-source labeling
- Objective: Make the P20B-T1 recent-review list contract explicitly self-describing while it is synthetic/demo-only, so Claude A can wire it without accidentally presenting rows as real persisted history.
- Dependencies: `P20B-T1`.
- Files expected to change:
  - `backend/app/schemas/trade_review_workspace.py`
  - `backend/app/services/trade_review/frontend_read.py`
  - `backend/tests/api/test_trade_review_workspace.py`
  - `backend/tests/services/trade_review/test_frontend_read.py` if useful
  - `docs/shared/implementation_plan.md`
- Required contract addition:
  - Add list-level metadata to `TradeReviewListRead`, for example:
    - `data_mode`: `Literal["synthetic_demo", "persisted"]`
    - `demo_notice`: optional display-safe string such as `demo · not yet connected`
  - Current synthetic service must return `data_mode="synthetic_demo"` and a non-empty `demo_notice`.
  - Future persistence-backed implementation can return `data_mode="persisted"` and omit `demo_notice`.
- Acceptance criteria:
  - Existing list item fields remain unchanged.
  - Response remains list-only and frontend-safe.
  - Empty list response still carries list-level `data_mode`.
  - Forbidden-field validation still runs over the full response.
  - Tests prove the synthetic response is explicitly labelled as demo/not connected.
  - Existing preview routes remain unchanged.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
  - `git diff --check`
- Rollback notes: remove the list-level metadata fields and tests, restoring the P20B-T1 response shape.
- Status: `done`
- Verification notes:
  - 2026-05-23 Codex C added list-level `data_mode` and `demo_notice` metadata to `TradeReviewListRead`.
  - Current synthetic responses now return `data_mode="synthetic_demo"` and `demo_notice="demo · not yet connected"` for both populated and empty list states.
  - Existing list item fields remain unchanged, preview routes remain unchanged, and forbidden-field validation still runs over the full response.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q` -> `46 passed in 0.15s`.
  - Codex B review (2026-05-23): **PASS**. Demo metadata is sufficient to prevent frontend confusion with real persisted review history. Claude A may consume the endpoint only with the visible `demo · not yet connected` label until a persistence-backed source is implemented.

### P20B-T2 - aggregate risk alerts contract

- Task id: `P20B-T2`
- Title: aggregate risk alerts contract
- Objective: Add a sanitized read contract for Dashboard risk-alert cards that summarizes deterministic warnings without exposing account-specific thresholds or private portfolio details.
- Proposed endpoint: `GET /users/{uid}/risk-alerts`
- Frontend consumers:
  - Dashboard risk-alert feed.
  - Possible Settings/notification preference preview later.
- Expected safe response fields:
  - `alert_reference`
  - `generated_at`
  - `severity`
  - `category` such as `concentration`, `cash_collateral`, `stale_broker_snapshot`, `stale_market_quote`, `missing_data`, `agent_provider`
  - `title`
  - `summary`
  - `related_symbol_or_underlying` when safe
  - `related_review_reference` when safe
  - `freshness_scope` when the alert is freshness-related
  - `is_blocking`
- Explicitly forbidden:
  - raw risk rule thresholds
  - raw concentration/allocation percentages unless backend has an explicit safe display label
  - position quantities
  - cash/collateral dollar amounts
  - account values / buying power
  - account ids / provider ids
- Backend notes:
  - Alerts should be derived from deterministic services and existing actionability decisions, not generated by an LLM.
  - Prefer backend-owned `policy_label` / `display_label` over exposing threshold values.
  - Missing-data alerts should remain clearly separate from risk-rule violations.
- Tests required:
  - forbidden-field sweep
  - stale broker vs stale market quote separation
  - no raw threshold exposure
  - empty state
  - deterministic source labeling
- Status: `done`
- Verification notes:
  - 2026-05-23 Codex C added `RiskAlertListRead` / `RiskAlertItemRead` and protected `GET /users/{uid}/risk-alerts`.
  - Current implementation is synthetic/demo-only and includes list-level `data_mode="synthetic_demo"` plus `demo_notice="demo · not yet connected"`.
  - Alert rows expose display-ready references, severity/category/title/summary, safe related symbol/review refs, freshness scope, and `is_blocking`. They intentionally omit raw thresholds, raw concentration/allocation values, position quantities, cash/collateral/account values, provider ids, raw provider payloads, prompts, LLM responses, and provider traces.
  - Synthetic rows preserve stale broker snapshot vs stale market quote separation through distinct `freshness_scope` values.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q` -> `46 passed in 0.15s`.
  - Codex B review (2026-05-23): **PASS**. Endpoint placement under `/users/{uid}/risk-alerts` is acceptable; the schema is narrow, display-ready, demo-labeled, and preserves broker-vs-market freshness scope separation. Claude A may consume this endpoint only with visible demo/not-connected labeling.

### P20B-T3 - readiness aggregate contract

- Task id: `P20B-T3`
- Title: readiness aggregate contract
- Objective: Add a backend-owned readiness summary for the Dashboard hero strip without collapsing broker snapshot freshness, market quote freshness, and agent/provider availability into one ambiguous "ready" value.
- Proposed endpoint: `GET /users/{uid}/readiness`
- Frontend consumers:
  - Dashboard hero/readiness strip.
  - TopBar freshness/status widgets if PM later approves global indicators.
- Expected safe response fields:
  - `generated_at`
  - `overall_review_mode` such as `normal_review`, `analysis_only`, `manual_confirmation_required`, `blocked`
  - `broker_snapshot` summary with `freshness_scope="broker_snapshot"`, `status`, `as_of_label`, `reason_codes`
  - `market_quotes` summary with `freshness_scope="market_quote"`, `status`, `as_of_label`, `reason_codes`
  - `agent_provider` summary with `provider_mode`, `provider_status`, `is_mock_default`, `last_checked_at`
  - `recommended_user_action_label` for data readiness only, not trade advice
- Explicitly forbidden:
  - "ready to trade" / "safe to trade" wording
  - raw holdings, balances, or provider details
  - live provider keys/prompts
  - account-specific thresholds
- Backend notes:
  - This endpoint should summarize actionability/freshness, not recompute trade review.
  - Use "review readiness" or "analysis readiness" language, never execution readiness.
  - Agent provider status must remain separate from broker/market freshness.
- Tests required:
  - all actionability status families
  - broker stale and market stale independently
  - provider unavailable / mock default
  - forbidden wording scan
  - forbidden-field sweep
- Status: `done`
- Verification notes:
  - 2026-05-23 Codex C added `ReviewReadinessRead` plus nested `BrokerSnapshotReadinessRead`, `MarketQuoteReadinessRead`, and `AgentProviderReadinessRead` schemas.
  - Added protected `GET /users/{uid}/readiness`, currently synthetic/demo-only with `data_mode="synthetic_demo"` and `demo_notice="demo · not yet connected"`.
  - Response keeps broker snapshot freshness, market quote freshness, and agent provider status as separate nested objects. It uses `overall_review_mode="analysis_only"` and a data/review-readiness-only `recommended_user_action_label`; no execution readiness or trade advice wording is introduced.
  - Privacy boundaries: the response omits raw holdings, positions, quantities, cash/buying-power/account values, account/provider ids, raw provider payloads, prompts, LLM responses, provider traces, and account-specific thresholds.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q` -> `51 passed in 0.23s`.
  - Codex B review (2026-05-23): **PASS**. Endpoint placement under `/users/{uid}/readiness` is acceptable; broker snapshot readiness, market quote readiness, and agent-provider readiness remain separate; wording stays analysis/review-oriented rather than execution-oriented. Claude A may consume this endpoint only with visible demo/not-connected labeling.

### P20B-T4 - portfolio context enumeration + detail contracts

- Task id: `P20B-T4`
- Title: portfolio context enumeration + detail contracts
- Objective: Add standalone sanitized portfolio-context reads so the Portfolio Context page can display available contexts without relying on Trade Review preview responses.
- Proposed endpoints:
  - `GET /users/{uid}/portfolio-contexts`
  - `GET /users/{uid}/portfolio-context/latest`
  - `GET /users/{uid}/portfolio-context/{ctx_ref}`
- Frontend consumers:
  - Portfolio Context page.
  - Trade Review context selector, if replacing hardcoded `ctx_demo_*` options.
- Expected safe response fields:
  - opaque `context_reference`
  - `context_label`
  - `source_kind` such as `broker_snapshot`, `manual`, `csv`, `synthetic_demo`
  - `portfolio_shape` counts only
  - `cash_state` as an enum/label only, not a balance
  - `broker_snapshot_freshness`
  - `market_quote_freshness` or explicit `market_data_unavailable`
  - `actionability_preview`
  - `available_flows`
  - `caveat_codes`
- Explicitly forbidden:
  - raw holdings / positions / quantities
  - cash balances, buying power, account values
  - account ids, broker ids, provider ids, provider account ids
  - raw CSV rows or provider payloads
  - account-specific rules or thresholds
- Backend notes:
  - Reuse `PortfolioContextSummaryRead` where possible, but avoid leaking fields that were safe only inside a narrower preview response.
  - Context references must be opaque and validated; do not encode broker/account/provider identifiers.
  - This task may also remove duplicated demo context references from frontend dropdowns after review.
- Tests required:
  - opaque reference validation
  - forbidden-field sweep
  - manual/CSV/broker/synthetic-demo source labeling
  - latest unavailable / empty state
  - broker freshness and market quote freshness remain distinct
- Status: `not_started`.

### P20B-T5 - reports list + detail contracts

- Task id: `P20B-T5`
- Title: reports list + detail contracts
- Objective: Add safe Reports page reads for generated/saved review artifacts without exposing raw private report inputs or provider traces.
- Proposed endpoints:
  - `GET /users/{uid}/reports`
  - `GET /reports/{report_ref}`
- Frontend consumers:
  - Reports page list/detail.
  - Dashboard report shortcuts.
- Expected safe list fields:
  - opaque `report_reference`
  - `created_at`
  - `title`
  - `report_type`
  - `source_review_reference`
  - `review_flow_label`
  - `review_actionability_status`
  - `visibility`
  - `summary_status`
- Expected safe detail fields:
  - sanitized report markdown or structured sections already approved for frontend display
  - deterministic section labels
  - agent commentary sections, if already safety-validated
  - data limitations / freshness block
  - reproducibility refs that are opaque
- Explicitly forbidden:
  - raw provider payloads
  - raw prompts / raw LLM responses
  - raw account data / holdings / cash
  - account ids / provider ids
  - private thresholds
  - trade journal entries unless separately reviewed and redacted
- Backend notes:
  - Distinguish `agent_output`, `analysis_console`, and `final_report` message types.
  - Internal-only public research evidence should not automatically appear in user-facing reports.
  - Markdown must already be sanitized; frontend should render conservatively.
- Tests required:
  - list empty state
  - detail not found
  - forbidden-field sweep over list and detail
  - internal messages excluded by default
  - no advice/execution/guarantee wording
- Status: `not_started` (blocked).

### P20B-T6 - current user / profile display contract

- Task id: `P20B-T6`
- Title: current user / profile display contract
- Objective: Add a minimal safe profile read for prototype greeting/avatar surfaces without introducing auth flows, credential handling, or broker identity leakage.
- Proposed endpoint: `GET /me`
- Frontend consumers:
  - TopBar avatar slot.
  - Dashboard greeting.
  - Settings private-alpha/account display.
- Expected safe response fields:
  - `display_name`
  - `avatar_initials`
  - `private_alpha_status`
  - `appearance_preferences` only if already app-owned and non-sensitive
  - optional `feature_flags` for frontend display, not authorization
- Explicitly forbidden:
  - email unless PM/security approves
  - broker account names/ids
  - auth/session tokens
  - API keys or provider credentials
  - legal names pulled from brokerage/provider payloads
- Backend notes:
  - This should not become a full auth/session phase.
  - If real auth is not ready, keep marketing/auth screens static and label sign-in as not active.
  - Display name should be app-owned user metadata or a neutral fallback such as `Trader`.
- Tests required:
  - unauthenticated/local-dev behavior consistent with existing app guard
  - no token/secret/provider fields
  - neutral fallback behavior
- Status: `not_started` (blocked on auth / session design).

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
