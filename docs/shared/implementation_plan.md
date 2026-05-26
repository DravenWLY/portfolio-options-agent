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

Ordered near-term work after P20B-T4:

1. Add a safe Dashboard account-summary backend contract (`P20B-T7`) so the Modern Desk can bring back current account information without frontend-invented portfolio values.
2. Wire Dashboard cards to completed P20B contracts (`P20C-T1`): readiness, risk alerts, recent reviews, portfolio context, and the future account summary. Keep demo labels visible for synthetic data.
3. Keep the drafted Agent Console realtime architecture (`Phase 21A`) paused as a design reference while the founder evaluates agentic AI patterns. The prototype layout is approved as direction, but realtime transcript, direct-to-agent, broadcast, and quick questions are not authorized for implementation.
4. Redesign Settings as a sectioned page (`P20C-T3`) after settings contracts are approved; do not add broker destructive actions or provider credential controls.
5. Refine Trade Review and Reports after their backend contracts are stable.

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
- Status: `done`
- Verification notes:
  - 2026-05-24 Codex C added standalone portfolio-context read schemas: `PortfolioContextListRead`, `PortfolioContextDetailRead`, `PortfolioContextRead`, freshness/actionability preview shapes, and opaque context-reference validation reuse.
  - Added protected `GET /users/{uid}/portfolio-contexts`, `GET /users/{uid}/portfolio-context/latest`, and `GET /users/{uid}/portfolio-context/{ctx_ref}`. Current source is explicitly demo-only with `data_mode="synthetic_demo"` and `demo_notice="demo · not yet connected"`.
  - Response fields are sanitized display contracts only: opaque context references, source kind, portfolio-shape counts, cash-state labels, separate broker snapshot and market quote freshness, actionability preview, available flows, and caveat codes. No raw holdings, positions, quantities, cash balances, buying power, account values, account/provider ids, raw payloads, thresholds, prompts, LLM responses, or provider traces are exposed.
  - Added synthetic list/latest/detail/unknown-reference/unavailable-context tests, opaque-reference rejection tests, source-labeling checks, forbidden-field/wording sweep, and broker-vs-market freshness separation checks.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q` -> `64 passed in 0.21s`.
  - 2026-05-24 Claude A consumed P20B-T4 in the Portfolio Context page. Files changed: `frontend/src/types/portfolioContext.ts` (new TS types mirroring backend schemas), `frontend/src/api/portfolioContext.ts` (new API client for the three approved endpoints), `frontend/src/pages/PortfolioContextPage.tsx` (rewired from static demo data to backend-backed list+detail with loading/error/empty/success states). Demo labeling preserved via `DemoChip` whenever `data_mode === "synthetic_demo"`. Broker snapshot freshness and market quote freshness rendered as separate panels. Market-data-unavailable state shows a distinct blocked indicator. No forbidden phrases, no localStorage/sessionStorage writes, no unapproved endpoints. typecheck: pass. lint --max-warnings 0: pass. build: pass. No horizontal overflow at 1024/1280/1440. Old `DEMO_PORTFOLIO_SOURCES` and `DEMO_CONTEXT_REFS_TABLE` static constants are no longer imported by the page.

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

### P20B-T7 - dashboard account summary contract

- Task id: `P20B-T7`
- Title: dashboard account summary contract
- Objective: Add a sanitized, display-ready account/portfolio summary contract for the Modern Desk dashboard so the UI can show current account information without inventing frontend values.
- Proposed endpoint: `GET /users/{uid}/dashboard-account-summary`
- Frontend consumers:
  - Dashboard account summary / hero strip.
  - Possible TopBar account/status summary later if PM approves.
- Expected safe response fields:
  - `data_mode`: `synthetic_demo` or `persisted`
  - `demo_notice` while synthetic
  - `generated_at`
  - `summary_reference` opaque id
  - `source_label`
  - `broker_snapshot_freshness` with `freshness_scope="broker_snapshot"`
  - `market_quote_freshness` or `market_data_unavailable`
  - `portfolio_shape` counts only
  - optional display-safe account summary labels such as `total_value_label`, `cash_label`, `stock_exposure_label`, `option_exposure_label`, only if backend owns and redacts/formats them
  - `cash_state`
  - `caveat_codes`
  - `display_sections` or similar backend-owned grouping labels for the dashboard
- Explicitly forbidden:
  - account ids, broker ids, provider ids, provider account ids
  - raw holdings, raw positions, lots, tax lots, or quantities
  - raw cash balances, buying power, account values, or exact allocation vectors unless intentionally transformed into display-safe labels by this contract
  - raw provider payloads or raw CSV rows
  - account-specific thresholds
  - prompts, LLM responses, provider traces
  - execution/advice wording
- Backend notes:
  - This contract may expose user-visible account summary labels because the dashboard is a private user surface, but those labels must not become agent prompt inputs by default.
  - Keep raw private data out of the frontend response. Prefer backend-owned display labels over raw numeric fields unless PM/Codex B explicitly approves a value field.
  - Preserve broker snapshot freshness and market quote freshness as separate concepts.
  - Current implementation may be synthetic-demo first, but must carry list/detail-level `data_mode` and `demo_notice`.
- Tests required:
  - forbidden-field sweep
  - demo metadata
  - broker freshness vs market quote freshness separation
  - empty/unavailable state
  - no advice/execution/guarantee wording
  - local access guard
- Status: `done`
- Verification notes:
  - 2026-05-24 Codex C added `DashboardAccountSummaryRead` plus display-section schema for the Modern Desk dashboard account-summary cards.
  - Added protected `GET /users/{uid}/dashboard-account-summary`, currently synthetic/demo-only with `data_mode="synthetic_demo"` and `demo_notice="demo · not yet connected"`.
  - Response keeps broker snapshot freshness and market quote freshness separate. It exposes only opaque `summary_reference`, source/display labels, portfolio-shape counts, cash-state enum/label, backend-owned display labels, caveat codes, and dashboard grouping sections.
  - Privacy boundaries: no raw holdings, raw positions, lots/tax lots, quantities, raw cash balances, buying power, account values, account/provider ids, raw CSV/provider payloads, thresholds, prompts, LLM responses, provider traces, advice/execution wording, or guaranteed-return wording.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q` -> `69 passed in 0.29s`.
  - Codex B review (2026-05-24): **PASS**. Claude A may consume this contract for Modern Portfolio Desk Dashboard account-summary cards with visible demo/not-connected labeling while `data_mode="synthetic_demo"`.

## Phase 20C - Modern Portfolio Desk frontend wiring and refinements

Phase goal: wire completed Phase 20B contracts into the Modern Portfolio Desk UI and refine page-level information architecture without changing backend contracts or inventing fields.

Shared Phase 20C rules:

- Claude A may consume only Codex B-reviewed backend contracts.
- Keep `demo · not yet connected` labels visible whenever backend `data_mode` is `synthetic_demo`.
- Do not compute account values, cash, allocation, collateral, risk counts, or readiness in the frontend.
- Do not add execution controls, broker destructive actions, provider credential controls, or live LLM/provider controls.
- Preserve separate broker snapshot freshness, market quote freshness, and agent/provider readiness.

### P20C-T1 - dashboard backend wiring

- Task id: `P20C-T1`
- Title: dashboard backend wiring
- Objective: Replace Dashboard static demo cards with reviewed P20B backend contracts while preserving Modern Desk visual fidelity.
- Dependencies:
  - `P20B-T1A`
  - `P20B-T2`
  - `P20B-T3`
  - `P20B-T4`
  - `P20B-T7` for account summary cards; until then, account summary remains visibly demo/not connected.
- Expected frontend behavior:
  - consume recent reviews, risk alerts, readiness, portfolio context, and account summary only from reviewed API clients;
  - show loading, empty, error, and success states;
  - keep demo labels visible for synthetic-demo responses;
  - render account/portfolio summary labels only if backend provides them.
- Status: `done`
- Verification notes (2026-05-24):
  - Files changed: `frontend/src/types/dashboard.ts` (new TS types for TradeReviewListRead, RiskAlertListRead, ReviewReadinessRead, DashboardAccountSummaryRead and all sub-shapes), `frontend/src/api/dashboard.ts` (new API client for four approved endpoints), `frontend/src/pages/DashboardPage.tsx` (rewired from static demo constants to backend-driven with loading/error/empty/success states per panel), `docs/shared/implementation_plan.md`.
  - Endpoints consumed: `GET /users/{uid}/trade-reviews`, `GET /users/{uid}/risk-alerts`, `GET /users/{uid}/readiness`, `GET /users/{uid}/dashboard-account-summary`, `GET /users/{uid}/portfolio-contexts` (via existing portfolioContext API client).
  - Demo labeling: `DemoChip` shown on every panel header and readiness tile when `data_mode === "synthetic_demo"`. No demo labels shown when data_mode is persisted.
  - Freshness separation: readiness strip renders broker snapshot freshness, market quote freshness, and agent provider readiness as three visually separate tiles. Account summary is a fourth tile. What's Running panel also renders broker/market/agent as separate rows.
  - No forbidden phrases, no localStorage/sessionStorage writes, no unapproved endpoint paths.
  - typecheck: pass. lint --max-warnings 0: pass. build: pass (511ms).
  - No horizontal overflow at 1024 / 1280 / 1440.
  - Trade Review, Agent Console, Portfolio Context pages unaffected (screenshot verified).
  - Readiness grid uses fixed `repeat(4, 1fr)` columns matching prototype direction. Body uses fixed `1fr 1fr` grid.
  - Now-unused demo constants: DEMO_READINESS_TILES, DEMO_RECENT_REVIEWS, DEMO_RISK_ALERTS, DEMO_WHATS_RUNNING, DEMO_DISPLAY_NAME. DEMO_QUICK_REVIEWS still used for static quick-review navigation buttons.
  - Account summary tile fix (2026-05-24): ReadinessTile rows now render `total_value_label`, `cash_label`, `stock_exposure_label`, `option_exposure_label` from `DashboardAccountSummaryRead` verbatim. Null values display "—". `cash_label` falls back to `cash_state_label` when null. Stock and option position counts still shown. Codex B blocker resolved.
  - Deferred: full end-to-end browser smoke with running backend (requires LOCAL_DEV_ACCESS_TOKEN). Light/dark theme visual check deferred to stakeholder review.
  - Visual-fidelity fix-up (2026-05-24): readiness strip reduced from 4 equal tiles to 3 tiles with `1.4fr 1fr 1fr` proportions (broker snapshot wider, account summary moved to body). Account summary relocated to body right column as a standalone `AccountSummaryPanel` with KV rows (source, total value, cash, stock/option exposure, stock/option positions), loading/error/success states, DemoChip when synthetic, and market-data-unavailable note. Body grid changed from `1fr 1fr` to `1.6fr 1fr`. All emoji icons removed from sidebar navigation — replaced with typed monochrome SVG `MpIcon` system. Sidebar taxonomy corrected: Product (Landing, Pricing, Sign in), Workspace (Overview, Trade Review, Agent Console, Reports, Portfolio Context, Settings), Data Sources (secondary: Broker, Market Data, Risk Review). typecheck: pass. lint: pass. build: pass. No console errors.

### P20C-T2 - Agent Console prototype-aligned static layout

- Task id: `P20C-T2`
- Title: Agent Console prototype-aligned static layout
- Objective: Move the existing Agent Console response into the approved prototype information architecture without adding realtime or chat behavior before backend support exists.
- Dependencies:
  - existing Phase 19A/19B/19C Agent Console endpoint
  - Codex B architecture note for the prototype layout
- Expected layout:
  - top trade/run summary
  - left agent status rail
  - middle transcript-like role output stream
  - right deterministic evidence rail
  - bottom follow-up composer shown as disabled/not yet active unless Phase 21A backend is complete
- Status: `done`
- Verification notes (2026-05-24):
  - Files changed: `frontend/src/pages/AgentTeamAnalysisPage.tsx` (rewritten — prototype 5-zone layout shell), `frontend/src/components/agent-team/AgentTeamRunSummary.tsx` (new — top run summary band), `frontend/src/components/agent-team/AgentTeamTranscript.tsx` (new — middle transcript column with role cards, final synthesis, provider warnings, safety flags), `frontend/src/components/agent-team/AgentTeamEvidenceRail.tsx` (new — right deterministic evidence rail with actionability, broker freshness, market freshness, evidence summary, stages), `frontend/src/components/agent-team/AgentTeamComposerPlaceholder.tsx` (new — disabled follow-up composer with text input, agent selector, broadcast option, quick question chips, send button), `docs/shared/implementation_plan.md`.
  - Endpoint consumed: `POST /agent-team/trade-review-analysis/preview` (unchanged, via existing `agentTeamApi`).
  - Layout: pre-run shows `[form 320px | status 1fr]`; success shows 5-zone prototype: top run summary band, three-column body `[rail 260px | transcript 1fr | evidence 300px]`, bottom disabled composer placeholder.
  - Structural separation: deterministic evidence (freshness, evidence summary, actionability, stages) in right rail; agent commentary (role outputs, final synthesis) in middle transcript; run metadata in top band. Broker snapshot freshness and market quote freshness remain separate panels.
  - Composer placeholder: visibly disabled (opacity 0.55, pointer-events none, dashed border), includes text input, direct-to-agent selector, broadcast-to-team, quick question chips, send button. All controls disabled with Phase 21A attribution. Makes no API calls, no network requests, no storage writes.
  - Mock/synthetic/provider-unavailable labels: mock provider badges on run summary and per-role cards, provider status pills on each role, analysis-only badges throughout, unavailable reasons rendered verbatim.
  - No forbidden phrases, no localStorage/sessionStorage writes, no new endpoint paths.
  - typecheck: pass. lint --max-warnings 0: pass. build: pass (534ms, 102 modules).
  - Cleanup (2026-05-24): deleted orphaned `AgentTeamAnalysisConsole.tsx` — no imports remain; typecheck/lint/build all pass after removal.
  - Deferred: full end-to-end browser smoke with running backend (requires LOCAL_DEV_ACCESS_TOKEN). Light/dark theme visual check deferred to stakeholder review. Realtime transcript, follow-up submission, direct-to-agent routing, broadcast-to-team, quick question execution all deferred to Phase 21A.
  - PM pause clarification (2026-05-25): Phase 21A is paused; the composer must remain disabled and must not imply near-term activation. Any future copy adjustment removing phase-specific promise language is frontend polish only and does not authorize interaction.

### P20C-T3 - sectioned Settings page layout

- Task id: `P20C-T3`
- Title: sectioned Settings page layout
- Objective: Rework Settings to match the prototype pattern: left settings navigation, right detail panel, safe placeholder states for unavailable sections.
- Dependencies:
  - PM/Codex B approval for each settings section
  - `P20B-T6` if profile/private-alpha display is used
- Explicitly out of scope:
  - broker disconnect/delete
  - credential storage
  - provider API key editing
  - frontend LLM/provider selection
  - destructive account actions
- Status: `done`
- Verification notes (2026-05-24):
  - Files changed: `frontend/src/pages/SettingsPage.tsx` (rewritten — prototype-aligned sectioned layout), `frontend/src/components/layout/Sidebar.tsx` (icons updated to emoji), `docs/shared/implementation_plan.md`.
  - Layout: left settings nav (220px, matching prototype) with 6 section buttons using emoji icons; right detail panel renders the active section only. One section active at a time with accent-border active state.
  - Sections implemented (prototype-aligned): Account (👤 — account status + appearance + 2 future rows), Broker connection (🔗 — scope read-only boundary + 1 future row), Data freshness (🕐 — broker snapshot + market quote freshness panels + 3 future rows), Agents/LLM (🤖 — provider info + 3 future rows), Private alpha status (🛡 — plan/users/state), Analysis disclaimers (ℹ — 6 disclaimers + surface map + browser storage).
  - Future disabled rows: embedded inside relevant sections as `<button disabled>` elements with `cursor: not-allowed`, `opacity: 0.55`, dashed borders, "NOT YET ACTIVE" badge. Not isolated in a separate unreachable section.
  - Sidebar icons: updated from abstract Unicode glyphs to emoji for collapsed-mode distinguishability (📊 📋 🤖 📄 💼 ⚙️ 🔗 📈 ⚠️ 🏠 💲 🔑).
  - Prototype files read for alignment: `design/prototype/.../screens/settings.tsx`, `design/prototype/.../app.tsx`.
  - Safety boundaries: no forbidden trading/advice wording, no localStorage/sessionStorage writes beyond approved keys, no API calls or endpoint paths, no credential/provider/broker destructive controls, no execution controls.
  - typecheck: pass. lint --max-warnings 0: pass. build: pass (577ms).
  - Browser smoke: verified Account, Broker connection, Analysis disclaimers (light 1280px), Account (dark 1280px), all sections (light 1024px), collapsed sidebar emoji icons (light 1024px). Section switching works, disabled future rows are inert, no horizontal overflow at 1024/1280, no console errors.
  - Fix-up pass (Codex B blockers): (1) future settings no longer in separate unreachable section — embedded in parent sections, (2) future rows are `<button disabled>` not `<li>`, (3) sections realigned to prototype's 6 sections, (4) sidebar icons changed to emoji for collapsed-mode clarity, (5) settings nav icons changed to emoji matching section meaning.
  - Deferred: backend-backed settings (freshness thresholds, notification preferences, report defaults, broker account management, provider configuration) require reviewed backend contracts and remain as disabled future rows. P20B-T6 profile/private-alpha display integration deferred.
  - Visual-fidelity fix-up (2026-05-24): all emoji icons removed from Settings nav and section headers — replaced with typed monochrome SVG `MpIcon` system (lock, broker, clock, agent, shield, info). Settings grid changed from `220px 1fr` to `220px minmax(0, 1fr)` with `overflow: hidden` on detail panel to prevent content escape. ScopeRow checkmarks replaced from ✓/✕ characters to `<MpIcon name="check" />` / `<MpIcon name="x" />`. FutureRow circles replaced from `○` to `<MpIcon name="circle" />`. AlphaSection: added `DemoChip` to Panel header, removed unsupported "Connected users: 1/1" field. Surface row grid changed to `minmax(100px, 140px) 1fr` for responsive behavior. Added `overflowWrap: "anywhere"` to surface and future description text. Sidebar emoji icons also replaced with MpIcon across all nav groups. typecheck: pass. lint: pass. build: pass. Browser verified: section switching, no clipping at 1024/1280/1440, dark theme icon adaptation, collapsed sidebar icon distinguishability. No console errors.
  - Codex B re-review blocker (2026-05-24): AccountSection presented unsupported account-shaped placeholder values ("Operator mode: Local trader", "Account scope: Single-operator, single-portfolio") without demo labeling. No reviewed settings/profile backend contract (P20B-T6) exists. Fix: added `DemoChip` to Account panel header (consistent with Broker connection, Agents/LLM, and Private alpha panels), removed the two unsupported account-state rows, replaced with generic informational copy stating account profile details require P20B-T6. Status and Appearance rows retained (product status badge and local UI preference respectively). P20C-T3 remains `in_progress` pending Codex B follow-up re-review.
  - Codex B follow-up re-review (2026-05-24): **PASS**. `AccountSection` now carries visible demo labeling, no longer exposes unbacked operator/account-scope placeholders, and defers real profile/account data to `P20B-T6`. Existing Appearance handling remains local UI preference only. Static checks found no emoji navigation glyphs, new API/storage paths, or prohibited trading/advice wording. Verification rerun: `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, and `git diff --check` all passed.

### P20C-T4 - Trade Review clutter reduction

- Task id: `P20C-T4`
- Title: Trade Review clutter reduction
- Objective: Reduce visible deterministic overload by prioritizing summary, actionability, freshness, and caveats, while moving detailed deterministic sections into expanders. Align layout density with the Modern Portfolio Desk prototype direction.
- Dependencies:
  - no backend changes unless Codex B opens a contract revision
  - existing Trade Review endpoints unchanged: POST /trade-reviews/preview, POST /trade-reviews/portfolio-preview
- Expected files:
  - `frontend/src/pages/TradeReviewPage.tsx` — responsive form/results grid so disclosure cards remain readable in narrow app-browser layouts
  - `frontend/src/components/trade-review/TradeReviewResults.tsx` — reorganize sections into tiered disclosure layout, replace Unicode glyph icons with MpIcon
  - `frontend/src/styles/globals.css` — disclosure chevron rotation and marker suppression CSS
  - `docs/shared/implementation_plan.md`
- Implementation steps:
  1. Replace Unicode severity/status glyphs (ⓘ, △, ✕, ■, ●, ○) with typed monochrome MpIcon SVGs throughout TradeReviewResults
  2. Add disclosure CSS to globals.css for native `<details>` chevron rotation and marker suppression
  3. Create local `DisclosureSection` component wrapping `<details>/<summary>` with existing card styling and MpIcon chevron
  4. Reorganize TradeReviewResults into tiers:
     - Tier 1 (always visible scan path): actionability banner, deterministic reference, trade intent summary, freshness panel, workspace caveats
     - Tier 2 (collapsible disclosure, default closed): portfolio context, portfolio impact, cash/collateral, concentration/allocation, options exposure, scenario payoff, risk-rule violations, missing data warnings
     - Options exposure defaults open when covered-call or CSP safety caveats are present
     - Risk-rule violations and missing data warnings show item count in disclosure summary
  5. Preserve all existing section rendering logic within each disclosure — no data changes, no field changes, no financial computation
- Acceptance criteria:
  - All existing backend fields rendered verbatim; no financial computation
  - First viewport shows actionability, trade intent, freshness, and caveats only
  - Detail sections are expandable via native `<details>` disclosure
  - Covered-call and CSP safety caveats remain visible without user action (caveats block always visible; options exposure defaults open when relevant)
  - No emoji or ambiguous Unicode glyph icons — all status indicators use MpIcon
  - Broker snapshot freshness and market quote freshness remain visually and structurally separate
  - No new API calls, storage keys, or backend changes
  - No execution controls, advice wording, or guaranteed-return language
  - typecheck, lint --max-warnings 0, build pass
  - No horizontal overflow at 1024/1280/1440
- Tests:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint -- --max-warnings 0`
  - `cd frontend && npm run build`
  - Browser smoke: idle, loading, success, error states; light + dark themes; 1024/1280/1440 widths
- Rollback notes: revert TradeReviewResults.tsx and globals.css disclosure CSS changes; restore flat card layout and Unicode glyph icons
- Status: `done`
- Verification notes (2026-05-26, Claude A):
  - `npm run typecheck` — pass
  - `npm run lint -- --max-warnings 0` — pass
  - `npm run build` — pass, dist bundle 393.67 kB gzip 103.74 kB
  - Browser smoke (mock data injected via fetch intercept, backend not running):
    - Dark theme: 1024px, 1280px, 1440px — no horizontal overflow, two-column grid fits at all widths
    - Light theme: 1280px — proper MP light token rendering, card/surface contrast correct
    - Tier 1 scan path (actionability banner, deterministic reference, trade intent, freshness, caveats) all render in first viewport at 1280/1440
    - Tier 2 disclosures (portfolio context, portfolio impact, cash/collateral, concentration/allocation, options exposure, scenario payoff, risk-rule violations, missing data warnings) all render collapsed by default with chevron, count badges, and tag labels
    - Risk-rule violations disclosure: opens correctly showing severity grouping, warning badge, code, message, source, metric, actual, policy rendered verbatim
    - Idle state: placeholder with "No analysis generated yet" renders cleanly
    - Safety strip at page bottom visible
  - No emoji or Unicode glyph icons in TradeReviewResults.tsx — all use MpIcon
  - No localStorage/sessionStorage access in the component
  - No fetch/API calls in the results component (rendering only)
  - Broker snapshot and market quote freshness remain separate columns in Freshness panel
  - Added defensive fallback (`?? CAVEAT_META.info`) in WarningsContent and CaveatsBlock for runtime robustness against unexpected backend payloads
  - Not verified (backend not running): loading state skeleton, API error state, stale broker snapshot scenario, covered-call/CSP caveat defaultOpen with real backend data — these require running backend or a more complete mock harness; deferred to Codex B re-review
  - Pending: Codex B re-review for final `done` status
  - Codex B completion review (2026-05-26): **PASS**. Tier 1 keeps actionability, deterministic reference, intent, two-scope freshness, and caveats visible; Tier 2 uses native disclosure sections for portfolio context and deterministic detail panels. Existing Trade Review endpoints and response field ownership remain unchanged.
  - Codex B narrow fixes: added defensive display handling so an unexpected actionability status is labelled instead of rendering blank, and unexpected risk severities are retained in an explicit fallback group instead of silently omitted. A live narrow-width smoke exposed a collapsed result column in the parent page; `TradeReviewPage.tsx` and `globals.css` now stack the form/results grid below 1120px while preserving the desktop split, and long backend labels wrap without overflow.
  - Verification rerun: `cd frontend && npm run typecheck` passed; `npm run lint -- --max-warnings 0` passed; `npm run build` passed (`395.00 kB`, `103.70 kB` gzip); `git diff --check` passed. Static checks found only the existing approved API client paths and a no-storage doc comment.
  - Browser smoke against the running synthetic preview path: generated analysis displayed the Tier 1 scan path and collapsed Tier 2 disclosures; expanding Portfolio impact displayed deterministic content; main content reported no horizontal overflow at 1024, 1280, and 1440 widths. The grid intentionally stacks at 1024 and retains the two-column layout at 1280/1440.
  - Deferred polish: the pre-results shared empty-state glyph lives outside `TradeReviewResults` and may be migrated to `MpIcon` with the broader shared-state polish pass; it does not block the generated-results disclosure slice.

### P20C-T5 - Agent Console visual-fidelity refinement and obsolete-component cleanup

- Task id: `P20C-T5`
- Title: Agent Console visual-fidelity refinement and obsolete-component cleanup
- Owner: Claude A
- Objective: Bring the already approved five-zone Agent Console closer to the Modern Portfolio Desk prototype in spacing, hierarchy, typography, rail proportions, and responsive behavior. In particular, the middle pane must read visually as one chat-like transcript surface with agent turns and an attached disabled composer, rather than a loose stack of output cards. Preserve the existing stateless analysis-preview contract and keep all follow-up controls inert.
- Dependencies:
  - completed `P20C-T2` prototype-aligned static Agent Console layout
  - existing Phase 19A/19B/19C reviewed Agent Console response contract
  - Phase 21A remains paused; this task does not activate follow-up or realtime functionality
- Design reference:
  - `design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/agent-console.tsx` as visual reference only
  - Translate design intent into existing React/TypeScript components; do not paste prototype behavior or invent data.
- Expected files:
  - `frontend/src/pages/AgentTeamAnalysisPage.tsx`
  - `frontend/src/components/agent-team/AgentTeamPipelineRail.tsx`
  - `frontend/src/components/agent-team/AgentTeamRunSummary.tsx`
  - `frontend/src/components/agent-team/AgentTeamTranscript.tsx`
  - `frontend/src/components/agent-team/AgentTeamEvidenceRail.tsx`
  - `frontend/src/components/agent-team/AgentTeamComposerPlaceholder.tsx`
  - `frontend/src/components/agent-team/AgentTeamAnalysisConsole.tsx` only if verified orphaned and removed
  - `frontend/src/styles/globals.css` only for scoped Agent Console responsive or disclosure styling
  - `docs/shared/implementation_plan.md`
- Implementation steps:
  1. Compare the current success state to the prototype's five-zone structure: top run summary, left pipeline/evidence-input rail, middle transcript, right synthesis/deterministic-evidence rail, and bottom composer placeholder.
  2. Refine layout proportions, spacing, card hierarchy, typography, and responsive stacking so the page reads as an analysis workspace rather than a loose collection of panels.
  3. Rework the middle pane into one bounded transcript/chat surface: a transcript header, a scrollable/readable role-turn stream, visually coherent message-turn treatment, a clearly separated final-synthesis turn, and the disabled composer attached to the bottom of that same middle pane. Do not implement chat behavior.
  4. Render only real existing contract outputs as turns. Do not fabricate a user-message history, typing state, role debate, timestamps, streaming state, or evidence attachment content not present in the existing response.
  5. Preserve structural separation between deterministic evidence and agent commentary. Do not relocate generated commentary into deterministic summary cards.
  6. Replace remaining status/alert/empty-state Unicode glyphs in the Agent Console slice with typed `MpIcon` SVGs; use icon plus text for state meaning.
  7. Keep `AgentTeamComposerPlaceholder` fully disabled: no editable prompt state, no submission, no direct-to-role/broadcast behavior, no quick-question action, and no network/storage write. Use clear `not yet active` wording without promising a delivery phase.
  8. Preserve the only approved network path: `POST /agent-team/trade-review-analysis/preview`.
  9. Check whether `frontend/src/components/agent-team/AgentTeamAnalysisConsole.tsx` has no remaining importer; remove it only if it is demonstrably orphaned and the build passes after deletion.
  10. Verify narrow and desktop layouts with synthetic/mock output and update task notes before review.
- Acceptance criteria:
  - Five-zone success layout visibly aligns with the prototype's information architecture and remains usable at 1024, 1280, and 1440 widths without horizontal overflow.
  - The middle pane presents a unified transcript/chat-like reading experience, not a stack of independent report cards; role outputs appear as turns and final synthesis is a distinct final narrative turn.
  - The disabled composer is visually attached to the bottom of the middle transcript pane, as in the prototype, but remains entirely non-interactive.
  - Existing `AgentTeamAnalysisConsoleRead` fields are rendered only where backed by the current contract; no invented transcript, timer, evidence, or portfolio fields are added.
  - Deterministic evidence remains visually separate from agent role output and final narrative synthesis.
  - Broker snapshot freshness and market quote freshness remain separate scopes.
  - Composer remains visibly disabled and inert; Phase 21A remains paused.
  - No new endpoint, no backend/type-contract change, no localStorage/sessionStorage write, and no frontend financial calculation.
  - No execution controls, advice wording, guaranteed-return wording, or live-provider claims.
  - No emoji or ambiguous Unicode status glyphs remain in the Agent Console slice; state indicators use `MpIcon` plus text.
  - If the obsolete monolithic component is deleted, repository search confirms it is unreferenced before deletion.
  - `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, and browser visual smoke pass.
- Tests:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint -- --max-warnings 0`
  - `cd frontend && npm run build`
  - Static grep: only `POST /agent-team/trade-review-analysis/preview`; no new storage calls or prohibited trading/advice phrases.
  - Browser smoke using synthetic/mock analysis: idle, loading, success, and partial-success where available; light/dark; 1024/1280/1440; disabled composer interaction confirms no request/storage mutation.
- Rollback notes: revert only the P20C-T5 Agent Console presentation changes and restore the pre-refinement components; do not alter the existing Agent Console endpoint or unpause Phase 21A.
- Status: `done`
- Verification notes (2026-05-26):
  - `npm run typecheck` — clean (0 errors after removing unused `KV` import from AgentTeamRunSummary)
  - `npm run lint -- --max-warnings 0` — clean
  - `npm run build` — clean (103 modules, 1.19s)
  - `git diff --check` — no whitespace issues
  - Prohibited pattern grep — only safe JSDoc comments mentioning storage to say it is *not* used
  - Browser smoke (mock fetch, no backend):
    - Idle state: MpIcon circle renders correctly after fixing EmptyState to accept ReactNode icon prop
    - Success state at 1440 light: five-zone layout renders, chat-like transcript with role avatars + accent borders, synthesis turn, composer inside transcript panel, safety strip
    - Success state at 1280 light: balanced columns, no overflow
    - Success state at 1024 light: tight but functional, no horizontal overflow
    - Dark mode at 1440/1280/1024: good contrast, no invisible text, badges readable
    - Composer inertness confirmed: all 7 controls disabled, tabIndex -1, pointer-events none, aria-disabled true, opacity 0.55
    - Zero localStorage/sessionStorage keys after mock submission
    - Only POST /agent-team/trade-review-analysis/preview intercepted (mock); no other network calls
  - Additional fix during verification: updated `StateViews.tsx` EmptyState `icon` prop from `string` to `React.ReactNode`, replaced ErrorState `⚠` Unicode with `MpIcon name="alert"`, and updated AgentTeamAnalysisPage to pass `<MpIcon name="circle" size={28} />` — these changes also pass typecheck/lint/build
  - AgentTeamAnalysisConsole.tsx confirmed already deleted in prior session — no cleanup needed
  - Ready for Codex B review
- Fix-up verification notes (2026-05-26, Codex B blocker fixes):
  - Blocker 1 — responsive layout at 1024px:
    - Moved success-body grid from inline styles to scoped CSS classes in globals.css (`.mp-agent-console-body`, `.mp-ac-rail`, `.mp-ac-transcript`, `.mp-ac-evidence`)
    - Wide desktop (>1120px): three-column grid `240px minmax(0, 1fr) 280px` with sticky rails
    - Narrow desktop (≤1120px): single-column layout — transcript full-width (order 1), pipeline rail below (order 2), evidence rail below (order 3); rails un-stick and scroll naturally
    - Breakpoint matches existing Trade Review responsive threshold (1120px)
    - Files changed: `frontend/src/pages/AgentTeamAnalysisPage.tsx` (removed 4 inline style objects, added CSS class names), `frontend/src/styles/globals.css` (added responsive rules)
  - Blocker 2 — Phase 21A reference removal:
    - Replaced "Realtime transcript, direct-to-agent, broadcast, and follow-up controls belong to Phase 21A (currently paused)." with neutral wording: "Follow-up controls are disabled placeholders and are not active in this build."
    - `rg -i "phase 21"` on agent-team source files returns zero matches
    - File changed: `frontend/src/pages/AgentTeamAnalysisPage.tsx` (JSDoc comment only)
  - Static checks:
    - `npm run typecheck` — clean
    - `npm run lint -- --max-warnings 0` — clean
    - `npm run build` — clean (103 modules, 960ms)
    - No Phase 21A references in frontend agent-team source
    - No prohibited Unicode glyphs (●△✕○⚠⊞)
    - No prohibited wording or storage calls
  - Browser smoke (mock fetch, no backend):
    - 1440 light: three-column layout preserved, transcript readable
    - 1280 light: three-column layout preserved, balanced columns
    - 1024 light expanded sidebar: responsive single-column, transcript full-width and readable, composer attached, rails flow below
    - 1024 light collapsed sidebar: even more room, no overlap or horizontal overflow
    - 1024 dark expanded sidebar: responsive layout working, good contrast
    - 1440 dark: three-column preserved, good contrast
    - Broker snapshot and market quote freshness remain separately visible at all breakpoints
    - Only pre-existing `poa-sidebar-collapsed` localStorage key present; zero sessionStorage
  - Ready for Codex B re-review
  - Codex B re-review PASS (2026-05-26):
    - Responsive blocker resolved: scoped `.mp-agent-console-body` rules preserve the three-column desktop workspace and prioritize the full-width transcript at `max-width: 1120px`, with unstuck rails flowing below.
    - Phase-specific frontend attribution blocker resolved: Agent Console source uses neutral disabled-placeholder wording; no `Phase 21` reference remains in the reviewed frontend slice.
    - Contract and safety seam intact: only the existing analysis-preview API path remains, contract types are unchanged, deterministic evidence remains separate from commentary, broker and market freshness stay separate, and the composer remains inert.
    - Independent checks passed: `npm run typecheck`; `npm run lint -- --max-warnings 0`; `npm run build` (`103` modules, `399.52 kB` JS / `104.59 kB` gzipped); prohibited wording/glyph/storage-write grep; `git diff --check`.

### P20C-T6 - Shared Modern Desk state and icon cleanup

- Task id: `P20C-T6`
- Title: Shared Modern Desk state and icon cleanup
- Owner: Claude A
- Objective: Clean up residual shared loading/empty/error-state and status-icon inconsistencies visible on already approved Modern Portfolio Desk surfaces after page-specific refinements are complete.
- Dependencies:
  - completed and reviewed `P20C-T5`
- Expected files:
  - `frontend/src/components/shared/StateViews.tsx`
  - existing Modern Portfolio Desk page consumers only where required to adopt the shared typed icon/state API
  - `frontend/src/components/shared/mp/MpIcon.tsx` only if an additional generic state icon is genuinely required
  - `docs/shared/implementation_plan.md`
- Implementation steps:
  1. Inventory residual Unicode/emoji status and empty-state glyphs on Phase 20 Modern Portfolio Desk routes only.
  2. Replace shared state indicators with typed `MpIcon` usage while keeping loading, empty, and error copy and data behavior stable.
  3. Keep changes presentation-only; do not open new data contracts or rewrite legacy pages outside visible Phase 20 surface consistency needs.
  4. Verify each touched route in light/dark appearance and responsive widths.
- Acceptance criteria:
  - Shared Phase 20 empty/error/loading states use consistent Modern Portfolio Desk styling and icon-plus-text semantics.
  - No frontend financial computation, endpoint changes, contract changes, storage additions, or safety-copy regression.
  - No activation of the Agent Console composer or Phase 21A behavior.
  - `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, and scoped browser smoke pass.
- Tests:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint -- --max-warnings 0`
  - `cd frontend && npm run build`
  - Browser smoke across only touched Phase 20 routes and states.
- Rollback notes: revert shared-state presentation updates and consumer prop changes; retain all completed page layouts and backend wiring.
- Status: `done`
- Verification notes (2026-05-26):
  - **Files changed (7):**
    - `frontend/src/components/shared/StateViews.tsx` — EmptyState default icon changed from `"○"` string to `<MpIcon name="circle" size={28} />` ReactNode.
    - `frontend/src/components/shared/mp/DemoChip.tsx` — Added MpIcon import; replaced `○` text glyph with `<MpIcon name="circle" size={10} />`.
    - `frontend/src/pages/DashboardPage.tsx` — Removed 3 redundant `icon="○"` EmptyState props (default now handles it).
    - `frontend/src/pages/TradeReviewPage.tsx` — Removed 2 redundant `icon="○"` EmptyState props.
    - `frontend/src/pages/PortfolioContextPage.tsx` — Removed 2 redundant `icon="○"` EmptyState props; replaced `■` unavailable-market glyph with `<MpIcon name="alert" size={16} />`; removed unused `unavailableIcon` style; added MpIcon import.
    - `frontend/src/pages/LandingPage.tsx` — Replaced 8 FEATURES Unicode decorative icons (`⊛ ◇ ◷ △ ◫ ◰ ⊙ ✦`) with semantically matched MpIcon SVGs (lock, spark, clock, alert, agent, shield, portfolio, reports); replaced safety-section `● Is` / `✕ Is not` glyphs with `<MpIcon name="check" />` / `<MpIcon name="x" />`; changed FEATURES type from `Array<{ icon: string }>` to `Array<{ icon: React.ReactNode }>`; added MpIcon import.
    - `docs/shared/implementation_plan.md` — P20C-T6 status and verification notes.
  - **Checks run:** `npm run typecheck` PASS, `npm run lint -- --max-warnings 0` PASS, `npm run build` PASS (103 modules, 1.03s).
  - **Scoped static checks:** prohibited execution/advice wording (all hits are safety disclaimers — correct), localStorage/sessionStorage writes (none), fetch/axios/api additions (none), remaining ambiguous Unicode glyphs in changed files (zero).
  - **Browser smoke:** Dashboard (light+dark), Trade Review (light), Portfolio Context (light), Landing (light+dark) — all empty states render SVG circle icon, DemoChip renders SVG circle, Landing feature icons render as typed SVGs, safety indicators render check/x SVGs. All icon+text semantics preserved.
  - **Deferred legacy glyph occurrences (out of scope):** position components, broker legacy pages, market data legacy pages, risk review legacy pages — not swept per task scope constraints. These surfaces were not modified and contain glyphs that belong to future cleanup tasks outside Phase 20C.
  - **No regressions:** Agent Console composer remains disabled. Phase 21A remains paused. No storage, network, computation, or safety-language changes.
  - **Codex B review (2026-05-26): PASS.** Verified the scoped `MpIcon` replacements, shared `React.ReactNode` icon boundary, absence of remaining ambiguous glyphs/storage writes/new request paths in the touched files, and unchanged Agent Console/Phase 21A boundary. Independent `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build` (`103` modules), and `git diff --check` passed. Phase 20C is accepted as the current Modern Desk frontend integration checkpoint.

## Phase 21A - Realtime Agent Console backend contract

Phase goal, if reactivated later: define and implement the backend foundation required for the prototype Agent Console's persisted transcript, ordered progress stream, follow-up input, direct-to-agent routing, broadcast-to-team routing, and quick-question suggestions.

PM pause decision (2026-05-25): Phase 21A is paused before backend implementation while the founder studies agentic AI patterns and evaluates which workflow, routing, memory, critique, evaluation, and human-in-the-loop concepts belong in Portfolio Copilot. The architecture draft is retained for future discussion only. Codex C must not begin Phase 21A implementation unless Codex A later explicitly reactivates a scoped task. The Agent Console follow-up composer must remain disabled.

### P21A-T0 - Realtime Agent Console architecture contract

- Task id: `P21A-T0`
- Title: Realtime Agent Console architecture contract
- Objective: Define the safe run/thread, event, transcript, deterministic evidence rail, follow-up routing, persistence, and transport boundaries before backend implementation.
- Dependencies:
  - completed Phase 19A/19B/19C agent-team boundaries
  - completed `P20C-T2` prototype-aligned console layout
- Files expected to change:
  - `docs/codex-b-architecture/PHASE_21A_REALTIME_AGENT_CONSOLE_CONTRACT.md`
  - `docs/codex-b-architecture/adr/0007-agent-console-http-commands-sse-streaming.md`
  - `docs/shared/implementation_plan.md`
  - `docs/shared/current_roadmap.md`
  - `docs/shared/TASKS.md`
  - `docs/codex-b-architecture/ARCHITECTURE_HANDOFF.md`
- Architecture decision draft:
  - Keep existing stateless `POST /agent-team/trade-review-analysis/preview` unchanged.
  - Use backend-owned HTTP commands for new initial analysis and follow-up requests.
  - Use Server-Sent Events for ordered validated status/transcript progress with reconnect/replay support.
  - Defer native WebSocket and Socket.IO until a separately reviewed bidirectional-control need exists.
  - Stream completed validated message/status events only; do not stream raw LLM tokens, prompts, payloads, traces, or exception bodies.
  - Reuse app-owned run/step/thread/message persistence where semantics fit; any new persistence requires a reviewed mapping decision first.
- Acceptance criteria:
  - conceptual request/read/event schemas and role-specific prompt boundaries are documented;
  - deterministic evidence and agent commentary remain separate;
  - failure/rate-limit and replay semantics are documented;
  - frontend enablement remains blocked until backend and safety review pass.
- Status: `paused` (draft retained as a design reference; no implementation authorized pending future PM reactivation).
- Verification notes (2026-05-24, Codex B architecture draft):
  - Created `docs/codex-b-architecture/PHASE_21A_REALTIME_AGENT_CONSOLE_CONTRACT.md`.
  - Created proposed ADR `docs/codex-b-architecture/adr/0007-agent-console-http-commands-sse-streaming.md`.
  - Recommended HTTP command endpoints plus SSE event delivery, consistent with the existing architecture preference for SSE agent progress.
  - Kept Phase 19B live-provider gate unchanged: mock remains default and real LLM calls are not part of Phase 21A acceptance.
  - PM direction update (2026-05-25): paused further agentic/realtime design expansion before Codex C implementation while the founder studies agentic AI. Draft contract and ADR remain reference material only; disabled composer stays disabled.

### P21A-T1 - Safe run, transcript, event, and persistence mapping contracts

- Task id: `P21A-T1`
- Title: Safe run, transcript, event, and persistence mapping contracts
- Owner: Codex C
- Objective: Define typed backend-only read/write/event schemas and explicitly map Phase 21A semantics onto existing app-owned persistence primitives before adding a realtime route.
- Dependencies:
  - explicit future PM reactivation of Phase 21A
  - refreshed approval of `P21A-T0`
- Implementation steps:
  - Add safe typed schemas for accepted run, run snapshot, transcript message, SSE event, and follow-up request/acceptance.
  - Assess `agent_runs`, `agent_steps`, `report_threads`, and `report_messages` for console thread/message compatibility.
  - If existing persistence is not semantically correct, stop with a minimal persistence proposal rather than silently adding or overloading tables.
  - Add recursive forbidden-field and prohibited-language tests for all new safe shapes.
- Acceptance criteria:
  - frontend receives opaque references only;
  - no provider/model/prompt/freshness/actionability override fields exist in request contracts;
  - no raw provider tokens/traces, private values, or internal IDs exist in read/event contracts;
  - persistence decision is written in verification notes before route work begins.
- Status: `not_started` (`paused`; do not begin pending explicit future PM reactivation).

### P21A-T2 - Mock-first persisted initial analysis command and reads

- Task id: `P21A-T2`
- Title: Mock-first persisted initial analysis command and reads
- Owner: Codex C
- Objective: Add a persisted mock-first analysis-run creation path and reloadable safe run/transcript reads without altering the existing stateless preview route.
- Dependencies:
  - `P21A-T1`
- Proposed endpoints:
  - `POST /agent-team/analysis-runs`
  - `GET /agent-team/analysis-runs/{run_reference}`
  - `GET /agent-team/analysis-threads/{thread_reference}/messages`
- Acceptance criteria:
  - request reuses the safe portfolio-backed trade-review boundary;
  - mock provider remains default;
  - separate broker snapshot freshness and market quote freshness persist in safe reads;
  - deterministic evidence survives role/provider failures;
  - no frontend work, live external call, or TradingAgents execution is introduced.
- Status: `not_started` (`paused`; do not begin pending explicit future PM reactivation).

### P21A-T3 - SSE safe event stream and replay

- Task id: `P21A-T3`
- Title: SSE safe event stream and replay
- Owner: Codex C
- Objective: Expose ordered, reconnectable, frontend-safe progress events for a persisted analysis run.
- Dependencies:
  - `P21A-T2`
- Proposed endpoint:
  - `GET /agent-team/analysis-runs/{run_reference}/events`
- Implementation steps:
  - Emit validated lifecycle/message events only after safety validation.
  - Add monotonically ordered event IDs and `Last-Event-ID` replay semantics.
  - Add content-free heartbeat behavior and graceful terminal close behavior.
  - Cover partial completion for mock rate-limit/quota/provider failure scenarios.
- Acceptance criteria:
  - no token-by-token content, raw prompt, raw provider output, stack trace, or exception body is emitted;
  - replay returns only missing safe events;
  - event/status vocabulary is stable for eventual Claude A consumption.
- Status: `not_started` (`paused`; do not begin pending explicit future PM reactivation).

### P21A-T4 - Follow-up command and role-routing boundary

- Task id: `P21A-T4`
- Title: Follow-up command and role-routing boundary
- Owner: Codex C
- Objective: Support sanitized console follow-up questions targeted to an approved role or broadcast through the approved sequence.
- Dependencies:
  - `P21A-T3`
- Proposed endpoint:
  - `POST /agent-team/analysis-runs/{run_reference}/follow-ups`
- Implementation steps:
  - Validate question length, references, routing mode, and private-looking content.
  - Route direct questions to approved roles only.
  - Treat broadcast as role-specific prompt construction, never one shared prompt carrying portfolio evidence to public analysts.
  - Preserve risk/portfolio-only access to agent-safe deterministic evidence.
- Acceptance criteria:
  - public analysts receive public/synthetic evidence only;
  - risk and portfolio manager receive only approved agent-safe deterministic evidence;
  - unsafe questions are rejected before prompt construction or storage;
  - provider failures degrade to safe partial transcript results.
- Status: `not_started` (`paused`; do not begin pending explicit future PM reactivation).

### P21A-T5 - Safety, privacy, and reliability review

- Task id: `P21A-T5`
- Title: Safety, privacy, and reliability review
- Owner: Claude B
- Objective: Review the Phase 21A backend contract implementation for prompt privacy, safe transcript/events, partial-run clarity, and no execution/advice leakage.
- Dependencies:
  - `P21A-T1` through `P21A-T4`
- Status: `not_started` (`paused`; no review needed unless Phase 21A is reactivated and implemented).

### P21A-T6 - Architecture integration signoff and frontend handoff

- Task id: `P21A-T6`
- Title: Architecture integration signoff and frontend handoff
- Owner: Codex B
- Objective: Verify persistence coherence, HTTP/SSE boundaries, existing preview-route stability, and readiness for a later Claude A composer/SSE integration slice.
- Dependencies:
  - `P21A-T5`
- Acceptance criteria:
  - existing stateless Agent Console preview behavior remains compatible;
  - mock-first persisted run/follow-up/event behavior is contract-safe;
  - deterministic evidence and commentary remain structurally separate;
  - Claude A receives an explicit reviewed frontend contract before activating interactive console controls.
- Status: `not_started` (`paused`; no frontend handoff unless Phase 21A is reactivated and reviewed).

## Phase 22A - Provider-Neutral Market Data Evaluation Foundation

Phase goal: create the backend-only, offline, synthetic/replay-first foundation
needed to evaluate stock/ETF and listed-options market-data semantics without
selecting or calling a real provider.

PM decision (2026-05-25): **APPROVE WITH REVISIONS**. Tradier is no longer the
assumed scalable production provider; it may remain a prototyping or reference
candidate only. Production provider selection is reopened for later written
RFI/licensing review. Phase 21A remains paused and the disabled Agent Console
composer remains disabled.

Founder sequencing clarification (2026-05-25): maintain two market-data
tracks. The immediate track is free or low-friction early evaluation with
honest delayed/indicative/limited-source labels. Commercial vendor RFI
outreach is retained for later scale planning and is not required before an
approved local/internal evaluation adapter.

Architecture reference:

- `docs/codex-b-architecture/PHASE_22A_MARKET_DATA_EVALUATION_CONTRACT.md`
- `docs/codex-b-architecture/adr/0003-market-data-timing-tradier-rest-snapshots.md`
- `docs/codex-b-architecture/MARKET_DATA_PROVIDER_RFI.md`

Shared Phase 22A rules:

- The initial implementation is synthetic/replay-only and must make no
  external provider calls.
- Preserve provider-neutral REST/snapshot semantics; streaming remains
  separately deferred.
- Preserve broker portfolio snapshot freshness separately from underlying
  equity quote freshness and option quote/chain freshness.
- Represent IV and Greeks provenance or unavailable state explicitly.
- `live` may be reserved/test vocabulary only; it must not become a public
  provider/current-quote claim without later provider and licensing approval.
- Do not expose raw provider payloads, entitlements, credentials,
  vendor-private identifiers, or unsupported live claims.
- Do not add frontend surfaces, LLM/agent market-data ingestion, Phase 21A
  work, TradingAgents work, or broker execution behavior.

### P22A-T1 - Provider-Neutral Market-Data Snapshot Contracts And Synthetic/Replay Scenario Tests

- Task id: `P22A-T1`
- Title: Provider-Neutral Market-Data Snapshot Contracts And Synthetic/Replay Scenario Tests
- Owner: Codex C
- Objective: Review and narrowly refine the existing provider-neutral
  stock/ETF quote, option quote/chain, freshness, and IV/Greeks provenance
  contracts so Phase 22A market-data behavior is represented and tested through
  offline synthetic/replay scenarios only.
- Dependencies:
  - Codex A Phase 22A approval dated 2026-05-25.
  - Codex B Phase 22A architecture contract and amended ADR 0003.
  - Existing Phase 12 provider-neutral market-data domain models, interfaces,
    manual provider, snapshots, and tests.
- Expected bounded modules to inspect or change:
  - `backend/app/services/market_data/models.py`
  - `backend/app/services/market_data/interfaces.py`
  - `backend/app/services/market_data/freshness.py`
  - `backend/app/services/market_data/snapshots.py`
  - `backend/app/services/market_data/manual_provider.py`, only if compatibility
    changes are necessary
  - a small synthetic/replay-only provider or fixture module under
    `backend/app/services/market_data/`, only if the existing manual provider
    cannot cleanly express replay scenarios
  - `backend/app/schemas/market_data.py`, only if domain contract refinements
    require schema alignment
  - `backend/tests/services/market_data/`
  - `backend/tests/unit/test_market_data_schemas.py`, only if schema vocabulary
    is changed
  - `docs/shared/implementation_plan.md`, verification notes only
- Existing contract gap to assess explicitly:
  - current `DataMode` supports `live`, `delayed`, `indicative`, `cached`,
    `eod`, `manual`, and `unknown`, while Phase 22A requires explicit product
    concepts for `synthetic` and `unavailable`;
  - current market freshness is generally scoped as `market_quote`; determine
    the smallest backwards-conscious way to preserve separate underlying quote
    and option quote/chain provenance/freshness without collapsing either into
    broker snapshot freshness;
  - document the resolution in verification notes rather than silently
    changing vocabulary.
- Implementation steps:
  1. Read the Phase 22A contract, amended ADR 0003, existing market-data
     models/interfaces/freshness/snapshot helpers, and their tests.
  2. Identify the minimal domain/schema refinements required to represent
     synthetic/replay, indicative or limited-source, delayed, live-reserved,
     unavailable, stale, and provider-failure scenarios.
  3. Keep contracts provider-neutral and snapshot-oriented; do not add a
     vendor adapter or vendor-specific configuration.
  4. Add synthetic/replay fixture behavior sufficient to exercise stock/ETF
     underlying quote, selected option quote or chain, and IV/Greeks
     provenance/unavailability cases.
  5. Add deterministic tests for the approved scenarios and prove market
     quote scopes remain distinct from broker snapshot freshness wherever the
     integration seam is exercised.
  6. Record any remaining contract gap or compatibility decision in this task's
     verification notes.
- Acceptance criteria:
  - Stock/ETF quote and listed-option quote/chain evaluation remains
    provider-neutral and REST/snapshot-oriented.
  - Tests cover an available underlying stock/ETF quote and an available
    selected option quote/chain snapshot.
  - Tests cover missing/unavailable data, stale data, delayed data,
    indicative/limited-source data, and provider failure.
  - Tests cover IV and Greeks available, unavailable, and provenance/source
    states.
  - Tests demonstrate underlying quote and option quote/chain freshness or
    provenance are not silently collapsed, and remain separate from broker
    portfolio snapshot freshness at any actionability seam under test.
  - Synthetic/replay and unavailable concepts are represented or an explicit
    bounded contract-gap recommendation is returned for Codex B review.
  - `live` remains reserved/test vocabulary only; no code or docs claim an
    approved live external provider.
  - No provider SDK, account setup, credentials, `.env` changes, external
    calls, frontend changes, LLM/agent market-data path, Phase 21A work,
    TradingAgents work, route expansion, migration, streaming, or raw-provider
    payload exposure is introduced.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data tests/unit/test_market_data_schemas.py -q`
  - If shared actionability integration changes: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review/test_actionability.py tests/services/agents/ -q`
  - `git diff --check`
- Rollback notes:
  - Revert only the Phase 22A synthetic/replay contract refinements and focused
    tests, restoring the existing Phase 12 manual/provider-neutral behavior.
  - Do not revert unrelated Phase 20B/P20C, Phase 19, or paused Phase 21A
    changes.
- Status: `done`.
- Verification notes:
  - 2026-05-25 Codex C refined the existing Phase 12 provider-neutral domain contracts only: `DataMode` now retains all existing modes and adds `synthetic` plus `unavailable`; `FreshnessStatus` adds `unavailable`, which maps conservatively to `blocked_unknown_quote`.
  - Compatibility decision: replay is represented through fixed synthetic fixture snapshots and `replay` IV/Greeks provenance rather than a distinct quote-truth `data_mode`. A recent synthetic snapshot can be temporally `fresh` while remaining `analysis_only`; `live` stays reserved/test vocabulary and is still rejected by the manual/synthetic provider builders.
  - Added distinct quote-record scopes for `underlying_quote`, `option_quote`, and `option_chain`; snapshot references retain legacy aggregate `freshness_scope="market_quote"` for report-schema compatibility and add `input_freshness_scope` for granular provenance. Broker `broker_snapshot` scope remains separate at the actionability seam.
  - Added explicit implied-volatility provenance alongside expanded IV/Greeks provenance values (`provider`, `calculated`, `manual`, `synthetic`, `replay`, `unavailable`, `missing`). The existing manual provider now supports offline synthetic/replay, delayed, indicative, stale/cached, EOD, unavailable, and unknown fixture scenarios without network calls.
  - Added deterministic synthetic/replay tests covering available underlying and option/chain snapshots, delayed/indicative/stale/unavailable inputs, sanitized provider-error status, IV/Greeks provenance and unavailability, distinct quote scopes, and broker-vs-market actionability separation.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data tests/unit/test_market_data_schemas.py -q` -> `45 passed in 0.10s`; expanded compatibility run `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review/test_actionability.py tests/services/agents/ tests/services/trade_review/test_trade_review_snapshots.py tests/services/risk tests/unit/test_risk_schemas.py -q` -> `142 passed in 0.21s`; `git diff --check` -> clean.
  - Codex B blocker fix (2026-05-25): `MarketDataSnapshotReferenceRead` now preserves `input_freshness_scope` through deterministic risk-report read serialization while retaining aggregate `freshness_scope="market_quote"` for compatibility. Risk-schema regression coverage now asserts both option-quote and option-chain granular input provenance survive serialization. Files changed: `backend/app/schemas/risk.py`, `backend/tests/unit/test_risk_schemas.py`, and this verification note. Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data tests/unit/test_market_data_schemas.py tests/unit/test_risk_schemas.py -q` -> `49 passed in 0.46s`; `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review/test_actionability.py tests/services/agents/ tests/services/trade_review/test_trade_review_snapshots.py tests/services/risk tests/unit/test_risk_schemas.py -q` -> `142 passed in 2.16s`; `git diff --check` -> clean. Status remains `in_progress` pending Codex B re-review.
  - Codex B re-review (2026-05-25): **PASS**. The prior serialization blocker is resolved: deterministic risk-report reads preserve `input_freshness_scope="option_quote"` and `"option_chain"` while retaining aggregate `freshness_scope="market_quote"`. The correction introduces no provider, route, migration, frontend, agent, execution, or live-data scope expansion. Independent verification: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data tests/unit/test_market_data_schemas.py tests/unit/test_risk_schemas.py -q` -> `49 passed in 0.10s`; `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review/test_actionability.py tests/services/agents/ tests/services/trade_review/test_trade_review_snapshots.py tests/services/risk tests/unit/test_risk_schemas.py -q` -> `142 passed in 0.23s`; `git diff --check` -> clean.

### P22A-T2 - Market-Data Vendor Capability And Licensing Comparison

- Task id: `P22A-T2`
- Title: Market-Data Vendor Capability And Licensing Comparison
- Owner: Codex B
- Objective: Produce an architecture and commercial-rights comparison of
  candidate U.S. equity and listed-options data providers against the
  provider-neutral P22A contract before any provider trial, SDK integration,
  or live-data implementation is authorized.
- Dependencies:
  - completed `P22A-T1`
  - `docs/codex-b-architecture/PHASE_22A_MARKET_DATA_EVALUATION_CONTRACT.md`
  - `docs/codex-b-architecture/MARKET_DATA_PROVIDER_RFI.md`
  - amended ADR 0003
- Candidate providers to compare:
  - Intrinio
  - Databento
  - dxFeed
  - Massive, only if it materially improves the comparison
- Expected documents to inspect or change:
  - `docs/codex-b-architecture/MARKET_DATA_PROVIDER_RFI.md`
  - a new comparison memo under `docs/codex-b-architecture/`, if authorized
  - `docs/shared/implementation_plan.md`, verification notes only
  - ADR 0003 only if a later PM-approved provider decision supersedes its
    current provider-neutral posture
- Analysis questions:
  - What U.S. equity quote coverage is offered: consolidated CTA/UTP, limited
    feeds, delayed, or indicative?
  - What listed-options coverage is offered: OPRA-derived quotes, option
    chains, contracts/expirations, NBBO or bid/ask/last, volume/open interest,
    IV, and Greeks provenance?
  - Which rights cover external paid-user display, deterministic backend
    calculations, storage/replay for reproducible reports, derived summaries,
    and any later separately approved sanitized agent-evidence use?
  - What exchange entitlements, user/device fees, professional-user treatment,
    reporting obligations, minimum commitments, and trial restrictions apply?
  - What REST snapshot, historical/replay, rate-limit, outage/SLA, and possible
    later streaming capabilities exist?
  - Which unanswered commercial or licensing questions require written vendor
    response rather than assumption?
- Implementation steps:
  1. Use the RFI template as the comparison rubric and identify required
     answers for each candidate vendor.
  2. Prepare a source-attributed comparison matrix distinguishing confirmed
     public information from questions requiring written vendor confirmation.
  3. Compare fit for private alpha, paid beta, and later hundreds/thousands of
     end users without selecting a provider prematurely.
  4. Recommend which vendors, if any, should receive the written RFI and what
     decision gate must precede a bounded evaluation trial.
  5. Return the comparison and unresolved questions to Codex A for PM decision.
- Acceptance criteria:
  - The comparison covers equity, listed-options, IV/Greeks provenance,
    licensing/display/retention/derived-use rights, engineering shape, and
    commercial scaling.
  - Claims are source-attributed and distinguish public documentation from
    unverified assumptions or required written vendor answers.
  - No final production provider is selected in this task.
  - No API key, account setup, credential, SDK, provider adapter, provider
    request, paid trial, route, schema, frontend, streaming, LLM/agent
    market-data ingestion, Phase 21A, TradingAgents, or broker action work is
    authorized or introduced.
  - Alpaca Basic limited-source/indicative smoke testing and an Intrinio
    delayed-options trial remain possible future evaluation proposals only,
    requiring separate PM approval and explicit labeling constraints.
- Output:
  - provider capability/licensing comparison memo;
  - recommended written RFI recipient list, if justified;
  - open licensing/commercial questions;
  - recommendation for whether a later provider evaluation task should be
    drafted, with no implementation authorization.
- Verification:
  - Documentation/source review only; do not test provider endpoints or create
    accounts.
  - `git diff --check` for any approved documentation update.
- Rollback notes:
  - Remove only the comparison memo and P22A-T2 verification notes if the
    evaluation direction is replaced.
  - Preserve the completed provider-neutral synthetic/replay contract from
    `P22A-T1`.
- Verification notes (2026-05-25, Codex B):
  - Created
    `docs/codex-b-architecture/PHASE_22A_MARKET_DATA_VENDOR_COMPARISON.md`
    as a source-attributed vendor capability and licensing comparison.
  - Reviewed public official documentation only for Intrinio, Databento,
    dxFeed, and Massive; no provider accounts, credentials, trials, SDKs, or
    provider endpoint calls were used.
  - Included Massive because its published business options packaging,
    calculated-analytics, and no-exchange-approval claims materially improve
    the comparison; raw OPRA quote versus calculated-value scope and commercial
    rights remain questions for a written response.
  - Initially recommended sending the uniform RFI to all four candidates after
    PM approval. Founder sequencing clarification (2026-05-25): retain the RFI
    for later commercial-scale selection, but defer outreach while a separate
    early free/delayed provider assessment proceeds. No provider is selected
    and no external evaluation or integration work is authorized by `P22A-T2`.
  - Identified product-document alignment follow-up: `PRD.md`,
    `MVP_SCOPE.md`, and `FEATURE_PRIORITY.md` retain Tradier-first wording
    that no longer matches amended ADR 0003 and the Phase 22A decision.
  - Verification: documentation-only review; `git diff --check` -> clean.
- Status: `done`.

### P22A-T3 - Free/Delayed Early-Evaluation Provider Assessment

- Task id: `P22A-T3`
- Title: Free/Delayed Early-Evaluation Provider Assessment
- Owner: Codex B
- Objective: Identify the most practical free or low-friction market-data
  source for a later local/internal backend evaluation of stock/ETF and
  listed-options snapshot contracts, while keeping production selection and
  commercial RFI outreach deferred.
- Dependencies:
  - completed `P22A-T1` provider-neutral synthetic/replay contracts
  - completed `P22A-T2` commercial vendor comparison, retained for the later
    scale-selection track
  - `docs/codex-b-architecture/PHASE_22A_MARKET_DATA_EVALUATION_CONTRACT.md`
- Candidate paths assessed:
  - Alpaca Basic
  - Tradier Sandbox/Developer
  - Intrinio delayed-options free trial, only as a conditional path
  - Yahoo Finance, screening/rejection decision only
- Expected documents to inspect or change:
  - `docs/codex-b-architecture/PHASE_22A_EARLY_EVALUATION_PROVIDER_ASSESSMENT.md`
  - `docs/codex-b-architecture/PHASE_22A_MARKET_DATA_EVALUATION_CONTRACT.md`
  - `docs/codex-b-architecture/PHASE_22A_MARKET_DATA_VENDOR_COMPARISON.md`
  - `docs/shared/implementation_plan.md`
  - `docs/shared/current_roadmap.md`, `docs/shared/TASKS.md`, and
    `docs/codex-b-architecture/ARCHITECTURE_HANDOFF.md`, only to keep current
    handoff ordering accurate
- Implementation steps:
  1. Review official public documentation only for free/trial availability,
     stock/ETF and option data scope, chain/snapshot capability, IV/Greeks,
     mode/latency, account requirements, and use restrictions.
  2. Compare each path against provider-neutral `synthetic`, `indicative`,
     `delayed`, and `unavailable` vocabulary and the analysis-only boundary.
  3. Recommend a first local/internal candidate or return a blocker if no
     candidate can safely exercise the required contracts.
  4. Explicitly keep production use, public display, RFI outreach, live
     claims, frontend work, streaming, and agent market-evidence ingestion
     outside the assessment.
- Acceptance criteria:
  - Official sources are cited and confirmed facts are distinguished from
    permissions or trial terms that still require approval.
  - Recommendation identifies the limitation label required for every
    considered early-evaluation path.
  - No provider account, credential, endpoint call, SDK, adapter, external
    smoke test, frontend data display, or agent integration is introduced.
  - The commercial RFI path remains documented but is no longer represented as
    a prerequisite for local/internal early evaluation.
- Verification:
  - Documentation/source review only; no provider endpoint testing or account
    creation.
  - `git diff --check`.
- Rollback notes:
  - Remove only the P22A-T3 assessment memo and sequencing-alignment notes if
    PM replaces the early-evaluation strategy.
  - Preserve `P22A-T1` provider-neutral contracts and the later commercial RFI
    materials.
- Verification notes (2026-05-25, Codex B):
  - Created
    `docs/codex-b-architecture/PHASE_22A_EARLY_EVALUATION_PROVIDER_ASSESSMENT.md`
    using public official documentation only; no accounts, credentials,
    trials, SDKs, or provider endpoints were used.
  - Recommendation for PM decision: Alpaca Basic is the first candidate for a
    later backend-only local/internal evaluation adapter because it documents a
    zero-cost U.S. equity and options path plus option snapshot/chain/Greeks
    shapes. It must be represented as `limited_source`/`indicative`,
    `analysis_only`, and non-redistributable, not as product-current data.
  - Tradier Sandbox is the secondary candidate if actual 15-minute delayed
    stock/options quotes are preferred for local testing; sandbox Greeks are
    unavailable and distribution requires partner treatment.
  - Intrinio delayed options is a conditional higher-fidelity path for delayed
    OPRA plus IV/Greeks only after written free-trial/use terms are reviewed.
  - Yahoo Finance is screened out as an application backend source because
    official material does not support product redistribution/commercial use.
  - RFI outreach to commercial-scale candidates is deferred until later PM
    reactivation; the existing RFI/template and comparison remain retained.
  - Verification: documentation/source review only; `git diff --check` ->
    clean.
- Status: `done`.

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
