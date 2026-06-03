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

## Phase 20D - Dashboard Information Architecture And Contract Readiness

Phase goal: decide the Dashboard's information hierarchy and contract needs
before adding new data surfaces, visual panels, or backend endpoints. This is
product/UX and architecture planning only, not implementation.

Shared Phase 20D rules:

- Preserve the completed Phase 20C Dashboard until a later implementation task
  is separately approved.
- Do not create frontend cards, routes, API clients, or backend endpoints in
  this phase.
- Classify every proposed panel as already contract-backed, blocked on an
  approved future contract, or deferred/out of scope.
- Keep private user-facing portfolio aggregates separate from any future
  agent-safe evidence projection.
- Do not turn the Dashboard into a market terminal, quote watchlist, brokerage
  account mirror, AI recommendation feed, options screener, or execution UI.

### P20D-T0 - Dashboard Content Definition And Contract Gap Map

- Task id: `P20D-T0`
- Title: Dashboard Content Definition And Contract Gap Map
- Owner: Codex A with Codex B architecture support and Claude A UX input when available
- Objective: Define what the Dashboard should tell a manual investor in the
  first viewport, map approved information to existing reviewed contracts, and
  rank missing contract needs before any new implementation task is opened.
- Dependencies:
  - completed and reviewed Phase 20C frontend checkpoint
  - completed P20B demo-labelled Dashboard contracts
  - current Phase 22A market-data evaluation boundary
- Expected documents to create or update:
  - `docs/codex-a-product/DASHBOARD_CONTENT_DECISION.md`
  - `docs/shared/implementation_plan.md`, verification notes only
  - `docs/shared/current_roadmap.md` and `docs/shared/TASKS.md`, only if the
    approved content definition opens a later implementation slice
- Definition questions:
  - What must be understandable within five seconds of opening the Dashboard?
  - Which currently supported items remain in the first viewport: review
    readiness, broker snapshot freshness, market-data availability/data mode,
    safe portfolio/account summary labels, and start-new-review action?
  - Should recent analysis appear only after persistence-backed report/review
    contracts exist?
  - Which proposed market overview, economic-calendar/news, report, identity,
    or account-summary additions require a new reviewed backend contract?
  - Which private aggregates may be user-visible on an authenticated private
    surface but must remain excluded from LLM/agent prompts by default?
- Implementation steps:
  1. Inventory currently rendered Dashboard panels and their existing reviewed
     P20B contracts.
  2. Define first-viewport user goals and rank panel priority for a read-only
     manual-review cockpit.
  3. Prepare a panel/contract gap map with categories: existing contract,
     new contract required, deferred for safety/product reason, and not in
     Dashboard scope.
  4. Separate user-private display candidates from any later agent-safe
     evidence concepts.
  5. Return ranked follow-up contract proposals to Codex A; do not implement
     them in this task.
- Acceptance criteria:
  - The first viewport prioritizes review readiness, broker/portfolio context
    freshness, market-data availability/data mode, and a start-new-review
    action.
  - Recent analysis status is included only where persistence contracts exist
    or is explicitly labelled blocked.
  - No proposed panel implies trade execution, recommendation, current quote
    availability, or provider connection without a reviewed contract.
  - Market/news/account/report additions are each assigned an explicit
    contract-readiness status.
  - No code, schema, route, endpoint, prototype rewrite, API call, or provider
    integration is performed.
- Verification:
  - Documentation-only review against PM direction and existing contracts.
  - `git diff --check` for any subsequent documentation output.
- Rollback notes:
  - Remove only the Dashboard planning memo and its plan verification notes if
    PM replaces the information architecture.
  - Preserve completed Phase 20B/P20C implementation.
- Status: `done` (docs-only planning; no backend or frontend implementation authorized).
- Verification notes (2026-05-26, Codex A):
  - Created `docs/codex-a-product/DASHBOARD_CONTENT_DECISION.md` as the
    first-viewport content decision and contract-gap map.
  - Decision: the Dashboard is a review-readiness cockpit, not a collection
    of synthetic activity panels, brokerage mirrors, quote terminals,
    screeners, or recommendation surfaces.
  - Kept the start-review action and readiness/freshness hierarchy as the
    primary eventual first-viewport content; classified account summary,
    recent reviews, risk alerts, portfolio context, reports, market/news, and
    profile display by current contract readiness and product value.
  - Recorded that P20B display contracts used by Phase 20C remain
    `synthetic_demo`/demo-labelled development surfaces unless and until a
    separately approved real-source/private-display mapping exists.
  - Explicitly excluded P22A-T4 Alpaca evaluation output from Dashboard
    consumption: `indicative`/`limited_source` remains backend evaluation only
    until a separate frontend-display decision.
  - Ranked future contract needs, led by a real-source private Dashboard
    account-summary decision and real-source readiness mapping, followed by
    persisted recent reviews and attributable deterministic risk alerts.
  - No frontend/backend code, endpoint, schema, provider call, or Agent
    Console activation is authorized by this planning memo.

### P20D-T1 - Private Dashboard Account Summary Contract

- Task id: `P20D-T1`
- Title: Private Dashboard Account Summary Contract
- Owner: Codex C implementation, Codex B architecture/privacy review, Claude B safety review if frontend implications broaden
- Objective: Refine the existing Dashboard account-summary backend contract so
  a private authenticated Dashboard can later show account-detail labels
  without exposing raw account values, holdings, positions, identifiers, or
  agent prompt inputs.
- Dependencies:
  - completed `P20D-T0` Dashboard content decision
  - Codex A 2026-05-26 approval-in-principle for private account-detail labels
  - `docs/codex-b-architecture/PHASE_20D_DASHBOARD_ACCOUNT_DETAIL_CONTRACT.md`
  - completed `P20B-T7` synthetic/demo account-summary contract
- Files expected to inspect or change:
  - `backend/app/schemas/trade_review_workspace.py`
  - `backend/app/services/trade_review/frontend_read.py`
  - `backend/app/api/routes/users.py`, only if route/query shape must expose
    privacy display mode
  - `backend/tests/api/test_trade_review_workspace.py`
  - `backend/tests/services/trade_review/test_frontend_read.py`
  - `docs/shared/implementation_plan.md`
- Contract direction:
  - Revise the existing `DashboardAccountSummaryRead` /
    `GET /users/{uid}/dashboard-account-summary` contract rather than adding a
    duplicate endpoint.
  - Add or refine display-only fields for account details, provenance, and
    privacy mode. Candidate fields include `display_scope`,
    `valuation_basis`, `market_data_mode`, `privacy_display_mode`,
    `total_value_label`, `cash_label`, `cash_state_label`,
    `stock_etf_exposure_label`, `options_exposure_label`,
    `collateral_usage_label`, `portfolio_shape_label`,
    `position_count_label`, `broker_snapshot_freshness`,
    `market_quote_freshness`, `source_label`, `summary_reference`, and
    `caveat_codes`.
  - Default real-source scope should be selected context or selected account
    until combined portfolio aggregation is explicitly safe and clearly
    labelled.
  - Keep `combined_portfolio` as an allowed display scope only when the backend
    can prove and label aggregation semantics, source freshness, and caveats.
  - Preserve existing synthetic/demo behavior with visible demo metadata.
  - Use `privacy_display_mode="amounts_hidden"` as the safest default for any
    real-source path until a reviewed frontend toggle exists.
- Implementation steps:
  1. Compare the existing `DashboardAccountSummaryRead` with
     `PHASE_20D_DASHBOARD_ACCOUNT_DETAIL_CONTRACT.md`.
  2. Propose the smallest backward-compatible schema refinement needed for the
     approved private display labels and provenance.
  3. Implement synthetic/read-contract behavior only unless a separately
     approved real-source mapping already exists in safe app-owned services.
  4. Add or update service/API tests for field shape, privacy mode,
     selected-scope default, hidden-amount behavior, synthetic/demo behavior,
     freshness separation, valuation basis, market-data mode, caveats, and
     forbidden-field sweeps.
  5. Add explicit tests proving the response does not include raw holdings,
     raw positions, quantities, raw cash balances, buying power, raw account
     values, account/broker/provider ids, raw provider payloads, raw CSV rows,
     thresholds, prompts, LLM traces, or agent context envelopes.
  6. Document any contract gap that prevents real-source mapping; do not
     improvise raw fields to satisfy Dashboard visuals.
- Acceptance criteria:
  - Backend owns all calculation and formatting; frontend can render labels
    verbatim.
  - No raw numeric account values are returned unless a later task explicitly
    approves a specific sanitized value field.
  - Broker snapshot freshness and market quote freshness remain separate.
  - Valuation basis, market-data mode, display scope, source label, as-of data,
    and caveats are explicit.
  - Privacy display mode is represented and defaults safely.
  - Synthetic/demo values cannot look like real account data in normal product
    mode.
  - Account-detail labels remain private user-facing display fields and are not
    added to LLM/agent prompt inputs.
  - No frontend changes, market-data provider calls, LLM calls, broker calls,
    TradingAgents work, Phase 21A work, execution UI, or order behavior.
- Tests:
  - Focused backend API/service tests for the account-summary contract.
  - Forbidden-field and forbidden-wording sweeps.
  - Existing trade-review/front-end-read regression tests.
  - `git diff --check`.
- Rollback notes:
  - Revert only the schema/service/test refinements for `P20D-T1`.
  - Preserve completed `P20B-T7`, `P20C-T1`, and `P20D-T0` history unless the
    PM explicitly replaces the Dashboard account-detail decision.
- Verification notes:
  - 2026-05-26 Codex C refined the existing `DashboardAccountSummaryRead` /
    `GET /users/{uid}/dashboard-account-summary` contract for private
    dashboard account-detail display labels without adding a duplicate
    endpoint.
  - Added explicit `display_scope`, `valuation_basis`, `market_data_mode`,
    and `privacy_display_mode` fields. Synthetic/demo responses now default to
    `privacy_display_mode="amounts_hidden"` and keep visible
    `data_mode="synthetic_demo"` / `demo_notice="demo · not yet connected"`.
  - Added display-label-only fields for `stock_etf_exposure_label`,
    `options_exposure_label`, `collateral_usage_label`,
    `portfolio_shape_label`, and `position_count_label`; preserved the
    previous `stock_exposure_label` / `option_exposure_label` fields as
    compatibility aliases.
  - Broker snapshot freshness and market quote freshness remain separate;
    synthetic market data is labelled with `market_data_mode="synthetic"` or
    `market_data_mode="unavailable"` and no live/current/official quote claim.
  - No frontend, provider, agent-team, LLM, broker, route-expansion,
    migration, external API, or real-data work was added.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
    passed with `71 passed in 0.59s`.
  - Codex B review (2026-05-27): **PASS**. The existing
    `GET /users/{uid}/dashboard-account-summary` endpoint was safely refined
    without creating a duplicate endpoint. New fields are display-label-only
    and backend-owned; `privacy_display_mode="amounts_hidden"` is the safe
    default; broker snapshot freshness and market quote freshness remain
    separate; synthetic/demo responses stay clearly labelled and hidden. No
    frontend, agent/LLM, provider, route-expansion, migration, external API, or
    real-data work was added. Independent verification:
    `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
    -> `71 passed in 0.33s`; `git diff --check` -> clean.
  - 2026-05-27 Claude A frontend consumption of reviewed P20D-T1 contract:
    - Updated `frontend/src/types/dashboard.ts`:
      - Added `DashboardAccountSummaryDataMode`, `DashboardAccountDisplayScope`,
        `DashboardValuationBasis`, `DashboardMarketDataMode`, and
        `DashboardPrivacyDisplayMode` enum literal types mirroring backend.
      - Updated `DashboardAccountSummaryRead` interface with all P20D-T1 fields:
        `display_scope`, `valuation_basis`, `market_data_mode`,
        `privacy_display_mode`, `stock_etf_exposure_label`,
        `options_exposure_label`, `collateral_usage_label`,
        `portfolio_shape_label`, `position_count_label`.
      - Changed `data_mode` type from `Phase20BDataMode` to
        `DashboardAccountSummaryDataMode`.
      - Kept `stock_exposure_label` and `option_exposure_label` as deprecated
        compatibility aliases.
    - Updated `frontend/src/pages/DashboardPage.tsx` AccountSummaryPanel:
      - Panel tag now uses dynamic `display_scope` instead of static `"book-value"`.
      - KV rows now render all backend-owned labels verbatim: total value, cash,
        stock/ETF exposure, options exposure, collateral usage, portfolio shape,
        positions, valuation basis, market data mode, privacy display mode.
      - Prefers new `stock_etf_exposure_label` / `options_exposure_label` fields
        with fallback to compatibility aliases.
      - Shows `amounts hidden` Badge when `privacy_display_mode === "amounts_hidden"`.
      - Shows `caveat_codes` as stale-toned badges when present.
    - No new endpoints, localStorage/sessionStorage writes, financial computation,
      provider calls, agent/LLM changes, or forbidden wording added.
    - Verification: `npm run typecheck` PASS, `npm run lint -- --max-warnings 0`
      PASS, `npm run build` PASS (103 modules, 888ms), `git diff --check` clean.
  - Codex B frontend consumption re-review (2026-05-27): **PASS** after
    Claude A replaced the only invented account-summary note with neutral
    wording: `Market data unavailable.` The Dashboard no longer claims book
    value, broker-snapshot value, market value, current value, live data, or
    official quote status unless provided by backend-owned fields. Type
    fidelity, verbatim label rendering, privacy mode, freshness separation,
    compatibility aliases, caveat rendering, no new endpoints, no storage
    writes, no frontend financial computation, and no Agent Console / Phase
    21A activation remain intact.
- Status: `done`.

### P20D-T2 - Dashboard Cockpit Cleanup From Reviewed Contracts

- Task id: `P20D-T2`
- Title: Dashboard Cockpit Cleanup From Reviewed Contracts
- Owner: Claude A implementation, Codex B contract/safety review, Claude B UX/safety review if requested
- Objective: Reorganize the existing Dashboard into a compact
  review-readiness cockpit using only reviewed contracts and existing
  frontend-safe fields, reducing demo-card clutter without adding backend
  fields, endpoints, provider data, or a new Claude Design concept.
- Dependencies:
  - completed `P20D-T0` content decision
  - completed `P20D-T1` backend contract and frontend consumption
  - completed Phase 20C Dashboard wiring checkpoint
- Files expected to inspect or change:
  - `frontend/src/pages/DashboardPage.tsx`
  - `frontend/src/types/dashboard.ts`, only if needed to remove stale imports
    or preserve exact current contract types
  - `docs/shared/implementation_plan.md`, verification notes only
- Explicitly out of scope:
  - backend changes, new endpoints, new API clients, market/news/symbol search,
    Alpaca/P22A display, reports/profile contracts, Agent Console changes,
    Phase 21A activation, Claude Design import, or new prototype translation
- Implementation direction:
  - Keep the first viewport focused on:
    - clear `New trade review` action;
    - review-readiness summary;
    - separate broker snapshot and market quote/data limitations;
    - compact account summary using P20D-T1 backend labels;
    - optional portfolio context support if it stays clearly secondary.
  - Reduce, collapse, or visually demote synthetic/demo-only activity panels
    such as recent reviews and risk alerts so they do not feel like real user
    history or urgent portfolio warnings.
  - Remove or collapse `What's running` unless it can be presented as a
    non-live, non-activity summary without implying active runs.
  - Keep portfolio context as supporting context, not a large fake-data
    surface.
  - Preserve visible `demo · not yet connected` labeling wherever backend
    `data_mode` remains `synthetic_demo`.
  - Preserve separate broker snapshot freshness, market quote freshness,
    market-data mode, privacy display mode, valuation basis, and caveat codes.
- Acceptance criteria:
  - Dashboard reads as a risk-and-review cockpit, not a brokerage mirror,
    quote terminal, watchlist, options screener, market-data viewer, or AI
    recommendation feed.
  - All displayed account-summary values are backend-owned labels rendered
    verbatim; no frontend numeric parsing, formatting, computation, or
    inference.
  - Synthetic recent reviews and risk alerts are not presented as real user
    history or real risk urgency.
  - No raw holdings, raw positions, quantities, raw cash balances, buying
    power, raw account values, account/broker/provider ids, raw payloads,
    thresholds, prompts, LLM traces, or provider traces are introduced.
  - No execution, order, advice, guaranteed-return, `safe to trade`,
    `ready to trade`, live-provider, buy-now, or sell-now wording.
  - No localStorage/sessionStorage writes beyond existing approved UI keys.
  - No new endpoint paths, API clients, provider calls, or agent/LLM changes.
  - Responsive layout remains usable at 1024, 1280, and 1440 px.
- Verification:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint -- --max-warnings 0`
  - `cd frontend && npm run build`
  - `git diff --check`
  - Browser smoke if a dev server is available: `/` in light/dark at 1024,
    1280, and 1440 px; no horizontal overflow; demo labels visible on
    synthetic panels; no new network calls beyond existing Dashboard
    endpoints.
- Rollback notes:
  - Revert only the Dashboard page and P20D-T2 verification notes.
  - Preserve P20D-T1 contract/types unless a separate contract review requires
    changes.
- Status: `done`.
- Claude A frontend implementation verification (2026-05-27):
  - **Neutral header**: Removed personalized greeting `Good morning, ${displayName}.`
    and verbose sub-text. Title is now `"Dashboard"`, sub is
    `"Review readiness, account summary, and portfolio context. Manual decision support only."`
    Removed unused `displayName` const.
  - **Column swap**: Left column (primary) now holds Account Summary + Portfolio Context.
    Right column (secondary) holds Quick Reviews + demoted Recent Reviews + demoted Risk Alerts.
  - **WhatsRunningPanel removed**: Entire function and its styles (`facts`, `factRow`,
    `factLabel`) deleted. This panel duplicated readiness strip info and implied active runs.
  - **Synthetic demo reviews collapsed**: When `isDemoMode && status === "success"`,
    `RecentReviewsPanel` renders a compact note instead of the full table. Tag changes
    from `"last 7 days"` to `"demo"`. DemoChip always visible.
  - **Synthetic demo risk alerts collapsed**: Same pattern — compact note when demo.
    Tag changes from `"deterministic"` to `"demo"`. DemoChip always visible.
  - **Grid proportions updated**: Body grid from `1.6fr 1fr` to `1.2fr 1fr`.
  - **New style**: `collapsedNote` for collapsed demo panel text.
  - `tsc --noEmit`: clean.
  - `eslint DashboardPage.tsx`: clean.
  - `vite build`: 103 modules, no warnings.
  - Scoped static checks: no `WhatsRunning`/`displayName`/`factRow`/`factLabel` references
    remain; no `Good morning`/personalized greeting; no forbidden order/execute/localStorage
    patterns outside safety JSDoc; no frontend financial computation.
  - Browser smoke (no-user state): Neutral `"Dashboard"` title renders correctly at
    1024px light and 1440px dark. Safety strip intact. No horizontal overflow.
  - Full cockpit smoke (Docker Compose stack):
    - `docker compose up --build -d`: postgres healthy, backend up on :8000, frontend on :5173.
    - `/health` → 200 `{"status":"ok"}`.
    - `/` → 200 Vite HTML.
    - `/api/users` → 200 JSON (user "Local Trader" auto-selected).
    - Dashboard at 1024px light: two-column layout, no overflow, all panels rendered with
      backend data, DemoChips visible, collapsed demo reviews + alerts show compact notes.
    - Dashboard at 1280px dark: same — clean rendering, no overflow.
    - Dashboard at 1440px dark: same — clean rendering, no overflow.
    - Account Summary shows all P20D-T1 fields verbatim: display_scope, amounts_hidden
      badge, source_label, value labels, valuation_basis, market_data_mode, privacy,
      caveat_codes.
    - No WhatsRunningPanel in DOM.
    - No personalized greeting in DOM.
    - Safety strip visible at page bottom.
    - `docker compose down`: clean shutdown.
  - File: `frontend/src/pages/DashboardPage.tsx` — 608 lines (down from 624).
  - No other files changed. No backend changes. No new endpoints or API clients.

### P20D-T3 - Dashboard Visual/Content Polish

- Task id: `P20D-T3`
- Title: Dashboard Visual/Content Polish With Real Local Smoke Testing
- Owner: Claude A implementation, Codex B contract/safety review
- Objective: Polish the Dashboard as a compact risk-and-review cockpit:
  improve readiness strip density, Account Summary readability, Quick Review
  button fidelity, and collapsed demo panel clarity without changing backend
  contracts, endpoints, types, or safety boundaries.
- Dependencies:
  - completed `P20D-T2` Dashboard cockpit cleanup
  - completed `P20D-T1` account summary contract and frontend consumption
- Files changed:
  - `frontend/src/pages/DashboardPage.tsx`
  - `docs/shared/implementation_plan.md` (this verification block)
- Explicitly out of scope:
  - backend changes, new endpoints, new API clients, type changes,
    Agent Console, Phase 21A, market/news/symbol search, reports/profile,
    Claude Design import, `../TradingAgents`
- Changes made:
  - **Readiness strip**: Equal-width tiles (`repeat(3, 1fr)` grid). Replaced
    verbose KV rows with `FreshnessDial` for as-of labels. Added `readRow`
    flex layout for badge + dial on one line. Removed redundant status/as-of
    KV pairs.
  - **Account Summary**: Structured into three visual sections separated by
    rules. Uses `Stat` component for headline total value when amounts are
    visible. Position breakdown KV rows in middle section. Data provenance
    (valuation basis, market data, privacy) in compact bottom section. Source
    label rendered as Stat sub-line or standalone KV when amounts hidden.
  - **Quick Reviews**: Added semantic MpIcon SVGs to buttons (spark, alert,
    shield, lock — matching prototype icon mapping). Buttons now use row
    layout with icon + column for label/sub. Sub text uses uppercase
    letter-spacing for scanability. Added `quickReviewIcon` helper.
  - **Collapsed demo panels**: Added MpIcon (info, shield) alongside compact
    notes. Wrapped in `collapsedRow` flex container. Improved review history
    note wording to guide users toward starting a review.
  - **New styles**: `readRow`, `kvSection`, `collapsedRow`, `quickContent`.
    Updated `quickBtn` from column to row layout. Updated `quickSub` with
    uppercase styling. Added `lineHeight` to `readSub`.
  - All backend display labels remain verbatim. No frontend financial
    computation. No new endpoints, API clients, localStorage/sessionStorage
    writes, or forbidden wording.
- Verification:
  - `npm run typecheck`: clean.
  - `npm run lint -- --max-warnings 0`: clean.
  - `npm run build`: 103 modules, no warnings.
  - `git diff --check`: clean.
  - Static checks: no forbidden trading/advice wording, no localStorage,
    no new fetch/endpoint, no frontend numeric formatting, no emoji.
  - Docker Compose stack (`docker compose up --build -d`):
    - `/health` → 200.
    - `/` → 200 Vite HTML.
    - `/api/users` → 200 JSON.
    - Dashboard at 1024px light: no overflow, all panels readable.
    - Dashboard at 1280px light: clean, Account Summary structured sections
      visible, Quick Review icons render, collapsed panels with MpIcon.
    - Dashboard at 1280px dark: clean.
    - Dashboard at 1440px dark: clean, all panels above fold.
    - Other pages verified: `/trade-review`, `/agent-team-analysis`,
      `/portfolio-context`, `/settings` — no regressions.
    - `docker compose down`: clean shutdown.
  - File: `frontend/src/pages/DashboardPage.tsx` — 138 lines added, 97 removed.
- Status: `done`.

### P20D-T4 - Dashboard Claude Design Visual Refinement

- Task id: `P20D-T4`
- Title: Dashboard Claude Design Visual Refinement From Reviewed Contracts
- Owner: Claude A implementation, Codex B contract/safety review
- Objective: Implement only "Available now" visual refinements from the Claude
  Design feasibility review — better first-viewport hierarchy, action context
  surfacing, readiness section structure, and account summary section labeling.
  No new backend fields, endpoints, types, or safety boundary changes.
- Dependencies:
  - completed `P20D-T3` Dashboard visual/content polish
  - completed Claude Design feasibility review (panel inventory memo)
  - completed `P20D-T1` account summary and readiness contracts
- Files changed:
  - `frontend/src/pages/DashboardPage.tsx`
  - `docs/shared/implementation_plan.md` (this verification block)
- Explicitly out of scope:
  - backend changes, new endpoints, new API clients, type changes
  - market/news widgets, watchlist, options chain browser, symbol search
  - charts, sparklines, percentage changes, financial computation
  - Claude Design prototype JavaScript paste
  - Agent Console, Phase 21A, `../TradingAgents`
- Changes made:
  - **Action context bar** (new): Renders `recommended_user_action_label`
    and `overall_review_mode` badge from the reviewed `ReviewReadinessRead`
    contract. Accent-tinted background (`--mp-accent-soft`) with accent
    border (`--mp-accent-line`), matching Claude Design v2 dashboard
    prototype. MpIcon("review"), flexbox layout with badge right-aligned.
    Only appears when readiness data is loaded.
  - **Readiness section restructure**: Added section label row ("REVIEW
    READINESS") with DemoChip at section level instead of per-card. Cards
    now use header row layout: eyebrow left + status Badge right. Removed
    per-card DemoChip (redundant with section-level chip). Removed unused
    `isDemoMode` prop from `ReadinessTile`. Tighter card padding (space-3
    vertical, space-4 horizontal) with 6px internal gap.
  - **Account summary section headers**: Added "POSITION BREAKDOWN" and
    "DATA PROVENANCE" uppercase section headers above existing KV sections.
    Increased section padding-top from space-2 to space-3 for visual weight.
  - **reviewModeTone helper** (new): Maps `ReviewReadinessMode` enum values
    to `MpTone` for the overall review mode badge.
  - **Density refinements**: Page gap reduced from space-6 to space-5.
    Body column gap reduced from space-6 to space-5. Primary button gets
    letter-spacing. Quick review content gap increased from 1px to 2px.
    Styles block reorganized with section comments.
  - All backend display labels remain verbatim. No frontend financial
    computation. No new endpoints, API clients, localStorage/sessionStorage
    writes, or forbidden wording.
- Verification:
  - `npx tsc --noEmit`: clean (0 errors after removing unused isDemoMode prop).
  - `npx vite build`: 103 modules, no warnings.
  - Docker Compose stack (`docker compose up --build -d`):
    - Frontend: 200 Vite HTML.
    - Backend: 200 docs endpoint.
    - Dashboard at 1024px light: action bar visible, readiness section label
      visible, account summary section headers readable, two-column holds.
    - Dashboard at 1280px light: clean, all P20D-T4 additions visible.
    - Dashboard at 1280px dark: clean, all tokens respect dark theme.
    - Dashboard at 1440px light: compact, everything above fold.
    - Other pages verified: `/trade-review`, `/agent-console` — no regressions.
    - `docker compose down`: clean shutdown.
  - File: `frontend/src/pages/DashboardPage.tsx` — 724 lines total.
- Status: `done`.

### P20D-T5 - Dashboard Product B Pressure-Test Cleanup

- Task id: `P20D-T5`
- Title: Dashboard Product B Pressure-Test Cleanup
- Owner: Claude A implementation, Codex B contract/safety review
- Trigger: Requires explicit Codex A activation. This entry records accepted
  PM direction from the 2026-05-29 Stock Rover persona pressure test; it does
  not authorize immediate code work by itself.
- Objective: Apply remaining accepted Dashboard visual/copy cleanup from the
  Stock Rover heavy-user pressure test using only existing reviewed frontend
  contracts. The goal is to strengthen first-glance trust without adding new
  backend fields, endpoints, providers, or product surfaces.
- Dependencies:
  - completed `P20D-T4`
  - Codex A 2026-05-29 Dashboard pressure-test decisions in
    `docs/codex-a-product/DASHBOARD_CONTENT_DECISION.md`
- Files expected to inspect or change if activated:
  - `frontend/src/pages/DashboardPage.tsx`
  - `frontend/src/types/dashboard.ts`, only if stale imports/types need cleanup
  - `docs/shared/implementation_plan.md`, verification notes only
- Accepted cleanup direction:
  1. Keep complement-not-replace positioning: the Dashboard is a
     review-readiness cockpit, not a Stock Rover replacement, research
     terminal, screener, watchlist, holdings grid, fair-value surface, or
     market terminal.
  2. Promote the backend-owned plain-English readiness verdict above
     supporting readiness tiles if it is not already the first meaningful
     Dashboard answer.
  3. Move agent-provider readiness off the first viewport. It may remain in
     Settings, Agent Console, or a thin operational status row.
  4. Ensure `synthetic_demo` account summaries do not render plausible
     headline account values as if they might be real. Use hidden amounts or
     unmistakable non-real placeholder copy.
  5. Ensure quick-review presets either prefill the corresponding reviewed
     flow or are removed/reduced so they do not look actionable while doing
     nothing.
- Explicitly out of scope:
  - backend changes, schemas, routes, API clients, new storage keys, provider
    calls, market-data display, report/profile contracts, Agent Console,
    Phase 21A, `../TradingAgents`, Claude Design prototype import, generic
    company news, watchlists, holdings tables, screeners, or execution UI
- Acceptance criteria:
  - No rendered Dashboard field traces to an invented frontend value.
  - All account-detail values remain backend-formatted display labels rendered
    verbatim; no frontend financial computation.
  - Synthetic/demo account values are hidden or unmistakably non-real in the
    normal cockpit.
  - Agent-provider status no longer competes with broker snapshot and market
    quote readiness in the first viewport.
  - Quick-review controls either route with a reviewed prefill state or are
    removed/reduced.
  - No raw holdings, raw positions, quantities, raw cash balances, buying
    power, raw account values, account/broker/provider ids, raw payloads,
    thresholds, prompts, LLM traces, advice, execution, `safe to trade`,
    `ready to trade`, or guaranteed-return wording.
- Verification if activated:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint -- --max-warnings 0`
  - `cd frontend && npm run build`
  - `git diff --check`
  - Browser smoke for the Dashboard at 1024, 1280, and 1440 px in light/dark.
- Rollback notes:
  - Revert only the Dashboard page/type cleanup and this task's verification
    notes. Preserve `P20D-T1` through `P20D-T4` unless Codex A replaces the
    broader Dashboard decision.
- Verification notes (2026-05-30, Claude A — proposed, pending Claude B review):
  - Files changed: `frontend/src/pages/DashboardPage.tsx` only. No backend,
    schema, route, API-client, storage-key, or type changes (the existing
    `ReviewReadinessRead.recommended_user_action_label` and
    `DashboardAccountSummaryRead` fields were sufficient, so
    `frontend/src/types/dashboard.ts` was left untouched).
  - Acceptance item 1 (promote readiness verdict): the backend-owned
    plain-English `recommended_user_action_label` is now rendered verbatim in a
    prominent `ReadinessVerdict` hero block (eyebrow "Review readiness" +
    `overall_review_mode` badge + demo chip) placed immediately under the header
    as the first meaningful answer, above the supporting freshness tiles. The
    verdict also owns the readiness loading/error states.
  - Acceptance item 2 (agent provider off first viewport): the agent-provider
    tile was removed from the first-viewport readiness band (now relabeled
    "Data freshness" with only the distinct broker-snapshot and market-quote
    tiles). Agent-provider readiness now renders in a thin, muted, single-line
    operational `AgentProviderStatusRow` near the page bottom, just above the
    safety strip — it no longer competes with broker/market freshness.
  - Acceptance item 3 (synthetic amounts): in `synthetic_demo` the account
    headline shows the unmistakable placeholder "Connect a portfolio to see your
    value." instead of a plausible dollar figure, and the monetary breakdown
    rows (cash amount, stock/ETF exposure, options exposure, collateral usage)
    are suppressed; only safe qualitative context remains (cash state, portfolio
    shape, position counts). Real-source `amounts_hidden` privacy behavior is
    unchanged. All shown values remain backend display labels rendered verbatim.
  - Acceptance item 4 (quick-review presets): the dead flow-specific
    "Quick reviews" preset panel (4 buttons that only navigated to a blank Trade
    Review form) was removed, along with its now-unused `DEMO_QUICK_REVIEWS`
    import, `quickReviewIcon` helper, and styles. The header "New trade review →"
    action remains the single honest start-review entry point. (True per-flow
    prefill was not wired because it would require modifying the reviewed Trade
    Review form, which is outside this task's expected files — see deferred.)
  - Acceptance item 5 (cockpit identity preserved): no market terminal,
    watchlist, holdings grid, option-chain, screener, fair-value/rating, generic
    news, or recommendation UI added; no order/execution controls; no frontend
    financial computation; broker vs market freshness kept distinct; demo
    labeling preserved on all displayed synthetic surfaces; the P24A economic-
    awareness panel was left intact.
  - Verification: `cd frontend && npm run typecheck` clean; `npm run lint --
    --max-warnings 0` clean; `npm run build` clean; `git diff --check` clean.
    Browser smoke (Claude Preview, synthetic_demo) at 1024/1280/1440 in light and
    dark with no horizontal page overflow: confirmed the verdict hero, the
    "Data freshness" two-tile band, the "Connect a portfolio…" placeholder with
    no fake amounts, the removed quick-review panel, and the thin bottom
    agent-provider row.
  - Deferred polish: wiring true per-flow prefill into the Trade Review form
    (map preset flow → form `flowGroup` via router state) is a possible future
    enhancement; it requires a small change to the reviewed Trade Review form and
    so was kept out of this DashboardPage-only cleanup.
- Claude B contract/safety review (2026-05-30): PASS. Reviewed the full
  `frontend/src/pages/DashboardPage.tsx` (762 lines) against all acceptance
  criteria. Confirmed:
  - Acceptance 1: `recommended_user_action_label` rendered verbatim
    (`DashboardPage.tsx:226`) in the first-rendered `ReadinessVerdict` hero
    (`:155`, before strip/body/agent row); hero owns readiness loading/error
    (`:201-206`).
  - Acceptance 2: agent provider removed from the first-viewport "Data
    freshness" band (broker + market tiles only, `:262-277`) and demoted to a
    thin muted single-line `AgentProviderStatusRow` near the page bottom
    (`:185`, `:234-244`).
  - Acceptance 3: in `synthetic_demo`, headline shows the unmistakable
    placeholder "Connect a portfolio to see your value." (`:327`) with monetary
    breakdown rows suppressed; only qualitative cash-state/shape/counts remain
    (`:339-343`). Real-source `amounts_hidden` path preserved (`:315-319,
    :330-332`). No plausible synthetic dollars rendered.
  - Acceptance 4: dead quick-review preset panel removed; header
    "New trade review →" is the single start entry (`:148-151`). No unused
    imports/helpers/styles remain. True per-flow prefill correctly deferred
    (out of expected files).
  - Acceptance 5: cockpit identity preserved — no terminal/watchlist/holdings/
    screener/fair-value/news/recommendation/execution UI; broker vs market
    freshness distinct; demo labels on all synthetic surfaces; P24A economic
    panel intact (`:171`).
  - Safety: no invented frontend values — all account-detail values are backend
    display labels rendered verbatim; the only computation is relative-time
    formatting for review timestamps (`formatTimestamp`, `:606-620`) and
    `String()` of backend counts — no financial computation. No localStorage/
    sessionStorage. No private account detail routed to agents/LLMs (page only
    renders readiness/summary/context labels). Forbidden-wording scan clean —
    the sole "recommend*" occurrence is the backend-owned field name
    `recommended_user_action_label` rendered verbatim, whose text safety is the
    backend contract's responsibility (correct boundary). `types/dashboard.ts`
    confirmed unchanged.
  - Re-confirmed Claude A's checks are appropriate (typecheck / lint
    `--max-warnings 0` / build / `git diff --check` / browser smoke at
    1024/1280/1440 light+dark, no horizontal overflow).
  - Non-blocking follow-up (do not gate this task): confirm any unrelated
    multi-task worktree changes are grouped intentionally during commit/push
    cleanup. The `MpIcon.tsx` refresh glyph delta belongs to the economic
    calendar refresh UI, not to P20D-T5.
- Status: `done` (2026-05-30, Claude B contract/safety review PASS).

## Phase 21A - Realtime Agent Console backend contract

Phase goal, if reactivated later: define and implement the backend foundation required for the prototype Agent Console's persisted transcript, ordered progress stream, follow-up input, direct-to-agent routing, broadcast-to-team routing, and quick-question suggestions.

PM pause decision (2026-05-25): Phase 21A is paused before backend implementation while the founder studies agentic AI patterns and evaluates which workflow, routing, memory, critique, evaluation, and human-in-the-loop concepts belong in Portfolio Copilot. The architecture draft is retained for future discussion only. The Agent Console follow-up composer must remain disabled.

Ownership update (2026-06-01): if Codex A reactivates an agentic AI workflow slice, Claude E owns design/coding and Codex B reviews the result. Codex C should not implement the agentic AI system workflow unless Codex A later changes ownership explicitly.

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
  - PM direction update (2026-05-25): paused further agentic/realtime design expansion before implementation while the founder studies agentic AI. Draft contract and ADR remain reference material only; disabled composer stays disabled.
  - Ownership update (2026-06-01): Claude E is the implementation owner for any future approved agentic workflow slice; Codex C is not assigned to this lane.

### P21A-T1 - Safe run, transcript, event, and persistence mapping contracts

- Task id: `P21A-T1`
- Title: Safe run, transcript, event, and persistence mapping contracts
- Owner: Claude E, with Codex B architecture/safety review
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
- Owner: Claude E, with Codex B architecture/safety review
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
- Owner: Claude E, with Codex B architecture/safety review
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
- Owner: Claude E, with Codex B architecture/safety review
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

PM follow-up decision (2026-05-26): **APPROVE WITH REVISIONS** for
`P22A-T4 - Alpaca Basic Local/Internal Evaluation Adapter`. Commercial vendor
comparison and RFI material are parked as future references; no outreach,
licensing negotiation, pricing negotiation, or production-provider selection
is active. `P22A-T4` authorizes a backend-only, injected/mock-client mapping
adapter with indicative/limited-source, analysis-only semantics; it does not
authorize an external/API smoke test.

Architecture reference:

- `docs/codex-b-architecture/PHASE_22A_MARKET_DATA_EVALUATION_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_22A_ALPACA_BASIC_EVALUATION_ADAPTER_CONTRACT.md`
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

### P22A-T4 - Alpaca Basic Local/Internal Evaluation Adapter

- Task id: `P22A-T4`
- Title: Alpaca Basic Local/Internal Evaluation Adapter
- Owner: Codex C
- Objective: Implement a backend-only, app-owned mapping adapter that uses
  injected fake clients and synthetic Alpaca-shaped responses to test whether
  Alpaca Basic can exercise existing provider-neutral stock/ETF and
  listed-options market-data contracts without creating any live/default
  provider path.
- Dependencies:
  - completed `P22A-T1` provider-neutral snapshot contracts and tests
  - completed `P22A-T3` early-evaluation assessment
  - Codex A approval dated 2026-05-26
  - `docs/codex-b-architecture/PHASE_22A_ALPACA_BASIC_EVALUATION_ADAPTER_CONTRACT.md`
- Expected bounded modules to inspect or change:
  - `backend/app/services/market_data/interfaces.py`
  - `backend/app/services/market_data/models.py`
  - `backend/app/services/market_data/freshness.py`
  - `backend/app/services/market_data/snapshots.py`
  - new `backend/app/services/market_data/alpaca_evaluation_provider.py`, or
    an equivalently narrow app-owned adapter module
  - `backend/app/services/market_data/__init__.py`, only for safe exports
  - focused tests under `backend/tests/services/market_data/`
  - `backend/tests/unit/test_market_data_schemas.py` and
    `backend/tests/unit/test_risk_schemas.py`, only if a narrowly necessary
    typed provenance/read alignment is added
  - `docs/shared/implementation_plan.md`, verification notes only
- Explicitly excluded files/surfaces:
  - frontend files, routes, migrations, agent-team services, LLM/provider
    config, `../TradingAgents`, `.env` files, credentials, API keys, and any
    external provider client setup
- Contract gap to resolve or report:
  - Alpaca Basic evaluation data must be represented as `indicative`, with
    `limited_source` captured through safe typed coverage/provenance language
    where needed. Existing `DataMode` intentionally does not treat
    `limited_source` as quote truth. Codex C must not hide this limitation in
    untyped prose or represent it as `live`; propose the smallest
    backend-only typed refinement or stop with a blocker.
- Implementation steps:
  1. Read the P22A contracts, amended ADR 0003, existing market-data
     interfaces/models/freshness/snapshot code, and focused tests.
  2. Add a narrow Alpaca evaluation adapter behind an injected client
     boundary. Default tests use fake clients and fixed synthetic responses
     only.
  3. Map stock/ETF underlying quote, option quote, and option-chain responses
     into existing provider-neutral snapshots with distinct freshness scopes.
  4. Preserve IV and Greeks provenance or explicit missing/unavailable states;
     do not calculate or invent provider values.
  5. Apply backend-owned freshness/actionability semantics so indicative or
     limited-source input remains `analysis_only` unless a stricter existing
     blocked state applies.
  6. Add deterministic tests for supported, incomplete, unavailable, stale,
     and injected-client failure cases, plus typed limitation provenance.
  7. Confirm there is no route, frontend surface, credential loader, runtime
     provider selector, default network path, agent ingestion, or raw payload
     exposure.
- Acceptance criteria:
  - Adapter is app-owned, backend-only, snapshot-oriented, and provider-neutral
    at its output boundary.
  - Tests construct it only with injected fakes; no external API request,
    credential, SDK setup, provider account, or live smoke test is introduced.
  - Alpaca-derived evaluation results are never labelled `live`, official, or
    current market truth.
  - Equity and options responses carry `indicative` semantics and safe
    `limited_source` coverage/provenance where required.
  - Underlying quote, option quote, and option-chain freshness stay distinct;
    broker snapshot freshness remains separate.
  - IV/Greeks values are mapped only when present and have explicit
    provenance; absent/unsupported values degrade safely.
  - Provider errors and incomplete data produce safe unavailable/blocked or
    analysis-only behavior under existing backend policy, without raw
    exception/provider payload exposure.
  - No frontend, route, migration, provider credential/config, agent/LLM,
    Phase 21A, TradingAgents, execution, or commercial-provider work is added.
- Tests to run:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/market_data tests/unit/test_market_data_schemas.py tests/unit/test_risk_schemas.py -q`
  - If actionability integration changes: `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review/test_actionability.py tests/services/agents/ tests/services/trade_review/test_trade_review_snapshots.py -q`
  - `git diff --check`
- Rollback notes:
  - Revert only the Alpaca evaluation adapter, any narrowly justified
    provider-neutral limitation-provenance refinement, focused tests, and its
    verification notes.
  - Preserve completed P22A-T1 synthetic/replay contracts and P22A-T2/T3
    reference documents.
- Status: `done` (no external/API smoke test or frontend/agent consumption authorized).
- Verification notes (2026-05-26, Codex C):
  - Added `backend/app/services/market_data/alpaca_evaluation_provider.py` as a backend-only mapping adapter that requires an injected client boundary. It adds no SDK import, credential/config loader, runtime provider selector, route, persistence, frontend surface, or network implementation.
  - Added provider-neutral `coverage_status` vocabulary (`unknown`, `limited_source`, `unavailable`) to quote/chain snapshots and frozen snapshot references. Alpaca Basic-shaped mapped inputs are represented as `data_mode="indicative"` plus `coverage_status="limited_source"`; missing or failed inputs use `unavailable`. The limitation is typed and is never encoded as `live`.
  - Preserved `underlying_quote`, `option_quote`, and `option_chain` freshness scopes. Frozen risk/report references continue to use aggregate `freshness_scope="market_quote"` while retaining granular `input_freshness_scope` and now `coverage_status`.
  - Mapped IV and Greeks only when present in injected synthetic payloads with `provider` provenance under the same limited-source boundary; absent supported quote fields use `missing`, while unavailable/failed quote inputs use `unavailable`. No calculated or invented provider metrics were added.
  - Added synthetic adapter coverage for indicative underlying/option/chain mapping, no-call capability inspection, limited-source provenance, missing and incomplete fields, missing IV/Greeks, stale indicative input, sanitized injected-client failure, and risk/report snapshot-reference compatibility.
  - Files changed for this task: `backend/app/services/market_data/alpaca_evaluation_provider.py`, `backend/app/services/market_data/models.py`, `backend/app/services/market_data/snapshots.py`, `backend/app/services/market_data/manual_provider.py`, `backend/app/services/market_data/__init__.py`, `backend/app/schemas/market_data.py`, `backend/app/schemas/risk.py`, `backend/tests/services/market_data/test_alpaca_evaluation_provider.py`, `backend/tests/services/market_data/test_domain_models.py`, `backend/tests/unit/test_market_data_schemas.py`, `backend/tests/unit/test_risk_schemas.py`, and this verification note.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data tests/unit/test_market_data_schemas.py tests/unit/test_risk_schemas.py -q` -> `56 passed in 0.16s`; compatibility run `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review/test_actionability.py tests/services/agents/ tests/services/trade_review/test_trade_review_snapshots.py tests/services/risk tests/unit/test_risk_schemas.py -q` -> `142 passed in 0.18s`; `git diff --check` -> clean.
  - Codex B blocker fix-up (2026-05-26): chain mapping now accepts an injected `symbol` as `occ_symbol` only when it is a normalized OCC-format identity matching the mapped underlying, expiration, call/put side, and strike; malformed/provider-looking identifiers are omitted and cannot become frozen contract reference keys. Numeric mapping now rejects malformed and non-finite (`NaN`/`Infinity`) values without raising, so unusable underlying, option, and chain inputs degrade to existing unavailable/blocked semantics without raw error disclosure. Added synthetic regressions in `backend/tests/services/market_data/test_alpaca_evaluation_provider.py`. Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/market_data tests/unit/test_market_data_schemas.py tests/unit/test_risk_schemas.py -q` -> `58 passed in 0.15s`; `cd backend && ./.venv/bin/python -m pytest tests/services/trade_review/test_actionability.py tests/services/agents/ tests/services/trade_review/test_trade_review_snapshots.py tests/services/risk tests/unit/test_risk_schemas.py -q` -> `142 passed in 0.21s`; `git diff --check` -> clean. Status remains `in_progress` pending Codex B re-review.
  - Codex B re-review conclusion supplied to Codex A (2026-05-26): **PASS**.
    The symbol-boundary blocker is resolved through validated normalized OCC
    identity and an app-owned fallback identity; malformed/non-finite numeric
    inputs safely degrade without exception. Valid mapping remains
    `data_mode="indicative"`, `coverage_status="limited_source"`, and
    analysis-only. Offline suites passed with `58 passed` and `142 passed`;
    `git diff --check` was clean. No live API/network/provider, frontend, or
    agent expansion is authorized by administrative closure.

## Phase 23A - Symbol Lookup / Instrument Reference Foundation

Phase goal: add a backend-owned, provider-neutral symbol lookup and validation
foundation for Trade Review input ergonomics and later Dashboard quick entry.
The initial slice is synthetic/replay-first and backend-only.

Shared Phase 23A rules:

- No live provider, SDK, credential, `.env`, external API, frontend, market
  quote, option-chain browser, watchlist, screener, agent, or TradingAgents
  work in the initial slice.
- Symbol lookup is public reference data, not quote truth, broker tradability,
  or a recommendation.
- Return safe display/reference fields only. Do not expose raw provider
  payloads, entitlement metadata, broker/account data, or private portfolio
  context.
- Frontend autocomplete may start only after Codex B reviews the backend
  contract.

### P23A-T1 - Symbol Search And Validation Contracts With Synthetic Fixtures

- Task id: `P23A-T1`
- Title: Symbol Search And Validation Contracts With Synthetic Fixtures
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Implement backend contracts for ticker/instrument lookup and exact
  validation using deterministic synthetic/replay fixtures. The contract should
  support typeahead suggestions such as `NV` -> `NVDA` and a clear `Symbol Not
  Found` response when no supported match exists.
- Dependencies:
  - completed Phase 20D Dashboard content boundary
  - completed Phase 22A provider-neutral market-data evaluation foundation
  - architecture contract:
    `docs/codex-b-architecture/PHASE_23A_SYMBOL_LOOKUP_CONTRACT.md`
- Files expected to inspect or change:
  - `backend/app/schemas/`
  - `backend/app/services/`
  - `backend/app/api/routes/`
  - `backend/tests/`
  - `docs/shared/implementation_plan.md` verification notes only
- Suggested endpoint shape:
  - `GET /symbols/search?q={query}`
  - `GET /symbols/validate?symbol={symbol}`
- Conceptual response fields:
  - search wrapper: `query`, `normalized_query`, `data_mode`,
    `source_label`, `as_of_label`, `items`, `no_match`, `message`
  - item: `symbol`, `name`, `asset_class`, `exchange`, `region`,
    `currency`, `is_supported`, `match_type`, `score_label`,
    `source_label`, `as_of_label`
  - validation: `symbol`, `normalized_symbol`, `is_found`, `is_supported`,
    `asset_class`, `exchange`, `name`, `data_mode`, `source_label`,
    `as_of_label`, `message`
- Implementation steps:
  1. Define typed backend schemas for search and validation.
  2. Add a deterministic synthetic/replay symbol reference service with a small
     fixture set sufficient for prefix, exact, unsupported, and no-match tests.
  3. Add read-only routes using the app's existing protected/local API
     posture.
  4. Normalize case and whitespace consistently in backend service code.
  5. Return backend-owned `Symbol Not Found` style copy for no-match states.
  6. Add forbidden-field and forbidden-wording tests.
  7. Document any contract gaps; do not add frontend wiring.
- Acceptance criteria:
  - `NV` returns deterministic safe suggestions such as `NVDA` from fixtures.
  - Unknown input returns a safe no-match response without raising.
  - Exact validation distinguishes found/supported, found/unsupported, and
    not-found symbols.
  - Responses include data mode, source label, and as-of label.
  - Responses do not include quotes, prices, volumes, rankings as
    recommendations, broker/account data, raw provider payloads, credentials,
    or execution/order language.
  - Default tests make no external calls.
- Tests:
  - backend schema tests for response shape and enum literals
  - service tests for prefix, exact, alias/contains if included, no-match,
    unsupported, case/whitespace normalization
  - API tests for route behavior and local access guard
  - forbidden-field and forbidden-wording sweep
  - `git diff --check`
- Rollback notes:
  - Revert only symbol lookup schemas, service, routes, tests, and verification
    notes.
  - Preserve Phase 22A market-data contracts; symbol lookup is not a quote
    provider.
- Verification notes:
  - 2026-05-27 Codex C added provider-neutral symbol lookup schemas,
    service/provider contracts, and protected read routes for
    `GET /symbols/search?q={query}` and
    `GET /symbols/validate?symbol={symbol}`.
  - Added `backend/app/schemas/symbols.py` with typed
    `SymbolSearchRead`, `SymbolSearchItemRead`, and `SymbolValidationRead`
    contracts. Responses expose normalized display-safe symbol reference
    fields only: symbol/name, asset class, exchange, region, currency,
    support status, match type, data mode, source label, as-of label,
    no-match state, and backend-owned messages.
  - Added `backend/app/services/symbols.py` with a `SymbolProvider`
    protocol, deterministic `DemoSymbolProvider`, and `SymbolService` for
    normalization, strict prefix matching, ordering, deduplication, exact
    validation, unsupported/test-issue filtering, and sanitized provider
    failure behavior.
  - Added `backend/app/api/routes/symbols.py` and registered it through the
    existing protected FastAPI router path. The implementation is offline
    synthetic/demo-provider only: no frontend changes, live provider, SDK,
    network path, Nasdaq file fetch, market quote, option chain, news,
    agent/LLM, TradingAgents, broker, order, or execution behavior was added.
  - Added tests in `backend/tests/services/test_symbol_lookup.py` and
    `backend/tests/api/test_symbols.py` for strict prefix behavior, case and
    whitespace normalization, no fuzzy/contains matching, no-match display,
    ETF/stock labels, duplicate handling, unsupported/test-issue filtering,
    provider failure sanitization, response shape, forbidden-field/wording
    sweeps, and local access guard.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/api/test_symbols.py -q`
    passed with `14 passed in 0.08s`; `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
    passed with `71 passed in 0.40s`; full backend
    `cd backend && ./.venv/bin/python -m pytest -q` passed with
    `699 passed, 92 skipped, 1 deselected in 2.87s`.
- Status: `done`

### P23A-T2 - Trade Review Symbol Autocomplete Frontend

- Task id: `P23A-T2`
- Title: Trade Review Symbol Autocomplete Frontend
- Owner: Claude A implementation, Codex B frontend contract review
- Objective: Wire the reviewed symbol search/validation contracts into Trade
  Review symbol inputs with typeahead suggestions and `Symbol Not Found`
  handling.
- Dependencies:
  - completed and Codex B-reviewed `P23A-T1`
- Status: `done`
- Verification notes:
  - Files created:
    - `frontend/src/types/symbols.ts` — TypeScript mirror of backend
      `SymbolSearchItemRead`, `SymbolSearchRead`, `SymbolValidationRead`,
      plus `SymbolLookupDataMode`, `SymbolAssetClass`, `SymbolMatchType`
      enum literals.
    - `frontend/src/api/symbols.ts` — provider-neutral API wrapper using
      `apiClient.get`. `symbolsApi.search(query, limit)` →
      `GET /symbols/search`, `symbolsApi.validate(symbol)` →
      `GET /symbols/validate`. No direct broker/market-data calls.
    - `frontend/src/components/trade-review/SymbolAutocomplete.tsx` —
      reusable combobox autocomplete with 250 ms debounced search,
      keyboard navigation (ArrowDown/Up/Enter/Escape), mouse selection,
      outside-click close, active-item scroll-into-view, ARIA combobox
      pattern (`role="combobox"`, `aria-expanded`, `aria-autocomplete`,
      `aria-controls`, `aria-activedescendant`). Uses MP design tokens.
  - Files modified:
    - `frontend/src/components/trade-review/TradeReviewForm.tsx` — replaced
      plain `<TextField>` for Symbol and Underlying fields with
      `<SymbolAutocomplete>`. No changes to form submission logic,
      validation, or request payload shapes.
  - Form fields wired: Symbol (stock/ETF flows), Underlying (option flows).
  - UX states implemented:
    - Typing prefix → debounced search → suggestion dropdown with symbol,
      name, asset class, exchange, supported status.
    - No-match → backend `message` rendered verbatim (e.g. "Symbol Not
      Found").
    - Loading → "Searching…" indicator.
    - Error → error message displayed in dropdown.
    - Selection → fills field, closes dropdown, no re-search.
    - No dropdown on mount despite default values (`hasInteractedRef`
      gates search until user focus/type).
  - Safety checks:
    - No `localStorage` / `sessionStorage` writes (verified: 0 keys).
    - No prices, quotes, volume, or market data displayed.
    - No frontend fuzzy matching or recommendation ranking.
    - Results are not ranked as recommendations.
    - Backend-owned messages rendered verbatim.
    - No order/execute/place/cancel controls added.
  - Commands run:
    - `cd frontend && npx tsc --noEmit` — clean (0 errors).
    - `cd frontend && npx eslint --max-warnings 0 src/types/symbols.ts
      src/api/symbols.ts src/components/trade-review/SymbolAutocomplete.tsx
      src/components/trade-review/TradeReviewForm.tsx` — clean (0 warnings).
    - `cd frontend && npx vite build` — clean (105 modules, 962 ms).
    - Docker Compose full-stack smoke test:
      - "NV" → NVDA + NVDL suggestions ✅
      - "ZZZZZ" → "Symbol Not Found" ✅
      - Select NVDA → fills field, closes dropdown ✅
      - Underlying in Covered Call flow → "AA" shows AAPL ✅
      - No dropdown on mount with default "XYZ" ✅
      - 0 localStorage / 0 sessionStorage keys ✅
  - Codex B review — blocker fix (disabled-state race):
    - Problem: if the dropdown was open when `disabled` flipped to `true`,
      suggestion rows could still be clicked, `selectItem()` could still
      call `onChange`, and a pending debounce or in-flight search could
      reopen/update the dropdown after disabled mode started.
    - Fix applied to `SymbolAutocomplete.tsx`:
      1. Added `disabledRef` (mutable ref mirroring prop) so async
         callbacks can read the current disabled state.
      2. Added `useEffect` on `disabled`: when true, clears pending
         debounce timer, closes dropdown, resets activeIndex, clears
         suggestions/loading/error state.
      3. `doSearch()` bails immediately if `disabledRef.current` is true
         at call time, and drops results if disabled flipped during the
         await.
      4. `selectItem()` guards on `disabled` — returns immediately if
         true.
      5. Suggestion row `onMouseDown` and `onMouseEnter` handlers guard
         on `disabled`.
    - No backend changes. No payload shape changes. No validation wiring.
      No storage writes. No new endpoints.
    - Post-fix verification:
      - `cd frontend && npx tsc --noEmit` — clean.
      - `cd frontend && npx eslint --max-warnings 0` (4 files) — clean.
      - `cd frontend && npx vite build` — clean (105 modules, 815 ms).

### P23A-T3 - Broad Symbol Directory Search And Recent-List Contract

- Task id: `P23A-T3`
- Title: Broad Symbol Directory Search And Recent-List Contract
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Expand symbol lookup from a tiny synthetic example set into a
  broader provider-neutral symbol directory foundation, while adding the
  backend contract behavior needed for the target autocomplete UX:
  empty input returns a non-search empty state for a future browser-local
  recents layer, and non-empty input returns exact-first, deterministic
  suggestions such as `NOK` -> `NOK` before other `NOK*` / contains matches.
- Desired product behavior:
  - Empty query/focus state:
    - return an empty non-search state from the backend;
    - do not return global default symbols;
    - true recent-symbol history belongs to a later browser/user-local LRU
      layer.
  - Non-empty query:
    - normalize case and whitespace in the backend;
    - return up to five or six symbols;
    - exact symbol match appears first;
    - symbol-prefix matches appear before symbol-contains/name-contains
      matches;
    - no fuzzy/edit-distance matching;
    - no frontend-side ranking.
- Dependencies:
  - completed `P23A-T1`
  - completed `P23A-T2`
  - updated architecture contract:
    `docs/codex-b-architecture/PHASE_23A_SYMBOL_LOOKUP_CONTRACT.md`
- Files expected to inspect or change:
  - `backend/app/schemas/symbols.py`
  - `backend/app/services/symbols.py`
  - `backend/app/api/routes/symbols.py`
  - optional backend-only normalized symbol fixture/parser modules
  - `backend/tests/services/test_symbol_lookup.py`
  - `backend/tests/api/test_symbols.py`
  - `docs/shared/implementation_plan.md` verification notes only
- Implementation steps:
  1. Revisit the `SymbolSearchRead` contract and decide whether existing
     fields are sufficient for recent/search/no-match states or whether a
     narrow backend-owned field such as `result_mode` or `section_label` is
     needed. If a field is added, update backend schemas and tests only in
     this slice; frontend consumption remains a later task.
  2. Add deterministic ordering for non-empty queries:
     exact symbol match first, then symbol prefix, then symbol contains,
     then name contains, with stable tie-breakers.
  3. Keep ordering labels neutral. Use wording like "Exact symbol match",
     "Symbol prefix match", or "Reference match"; never use recommendation,
     popularity, liquidity, or tradability language.
  4. Add a broader normalized symbol reference source. Default tests must use
     synthetic Nasdaq-style fixture rows or checked-in normalized demo rows.
     Do not fetch live provider files or call external APIs.
  5. If a Nasdaq-directory parser is introduced, parse only local fixture
     files in tests and normalize into app-owned records before search. Do
     not expose raw source rows or raw file payloads.
  6. Add an empty-query path that returns no backend symbols and clearly
     signals non-search state. Do not infer recent symbols from holdings,
     accounts, prompts, LLM context, trade history, or portfolio context.
  7. Preserve exact validation behavior from P23A-T1.
  8. Add forbidden-field and forbidden-wording tests.
  9. Document that true recents are deferred to a browser/user-local LRU
     frontend layer.
- Acceptance criteria:
  - Empty query returns an empty non-search state without exposing private,
    user, broker, or global fallback symbol data.
  - Query `NOK` returns an exact `NOK` symbol first when present.
  - Other `NOK*`, symbol-contains, or name-contains matches may follow in a
    deterministic order, capped at five or six items.
  - No fuzzy/edit-distance matching is introduced.
  - No frontend changes are included in this backend slice.
  - Responses remain provider-neutral and contain no quotes, prices, volumes,
    account/broker data, raw provider payloads, credentials, prompts, LLM
    traces, or order/execution/advice language.
  - Default tests make no network or external provider calls.
- Tests:
  - service tests for empty-query non-search state
  - service tests for exact-first ordering
  - service tests for symbol prefix, symbol contains, and name contains
    ordering
  - service tests for no fuzzy/edit-distance behavior
  - service tests for duplicate and unsupported/test-issue filtering
  - API response shape tests
  - provider failure sanitization tests
  - forbidden-field and forbidden-wording sweep
  - compatibility tests for existing P23A-T1 validation behavior
  - `git diff --check`
- Rollback notes:
  - Revert only P23A-T3 symbol schema/service/route/test changes and
    verification notes.
  - Preserve P23A-T1/T2 baseline search/autocomplete if the broader directory
    or recent-list behavior needs to be backed out.
- Verification notes:
  - 2026-05-28 Codex C expanded the backend-only symbol search contract while
    preserving `GET /symbols/search?q={query}&limit={limit}` and
    `GET /symbols/validate?symbol={symbol}`.
  - Added narrow backend-owned `SymbolSearchRead.result_mode` and
    `SymbolSearchRead.section_label` fields to distinguish
    `recent`, `search`, `no_match`, and `unavailable` states without requiring
    frontend-side inference.
  - Superseded by P23B-T5: empty query now returns an empty non-search state.
    True recents belong only to a browser/user-local LRU layer and are not
    inferred from holdings, broker accounts, portfolio context, prompts, LLM
    context, or persisted user history.
  - Non-empty search now uses deterministic backend-owned ordering:
    exact symbol match, symbol-prefix match, symbol-contains match, then
    name/reference match, with stable asset/exchange/symbol tie-breakers and a
    six-result cap. Labels remain neutral (`Exact symbol match`,
    `Symbol prefix match`, `Symbol contains match`, `Reference match`) and do
    not imply recommendation, popularity, liquidity, tradability, or
    performance.
  - Broadened the synthetic Nasdaq-style fixture set with NOK-related rows
    (`NOK`, `NOKBF`, `LNOK`, `NOKPF`, `NKRKY`, `NKRKF`), `NVDA`, `AMD`,
    `IREN`, `DRAM`, and additional stock/ETF/ADR examples to exercise
    exact-first, prefix, contains, name-reference, duplicate, unsupported, and
    test-issue filtering behavior.
  - Preserved exact validation behavior from P23A-T1 and provider failure
    sanitization. No frontend, provider, network file fetch, broker, market
    quote, option chain, watchlist, screener, SDK, credential/config loader,
    LLM, agent, TradingAgents, persistence, localStorage/sessionStorage, or
    execution/order behavior was added.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/api/test_symbols.py -q`
    passed with `21 passed in 0.11s`; `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
    passed with `71 passed in 0.33s`.
- Status: `done`

### P23A-T4 - Autocomplete UX V2 Recent And Contains Search Consumption

- Task id: `P23A-T4`
- Title: Autocomplete UX V2 Recent And Contains Search Consumption
- Owner: Claude A implementation, Codex B frontend contract review
- Objective: After P23A-T3 passes backend review, update the Trade Review
  autocomplete UI so empty focus/input can render the backend empty state and
  non-empty input displays exact-first contains-search results using only
  backend-owned ordering and messages.
- Dependencies:
  - completed and Codex B-reviewed `P23A-T3`
- Status: `done`
- Verification notes (2026-05-28, Claude A):
  - Files changed:
    - `frontend/src/types/symbols.ts` — added `SymbolSearchResultMode`
      union (now `"empty" | "search" | "no_match" | "unavailable"`) and added
      `result_mode` + `section_label` fields to the `SymbolSearchRead`
      interface, in backend field order (between `data_mode` and
      `source_label`). Header comment updated to reference the P23A-T3
      extension. Strictly mirrors `backend/app/schemas/symbols.py`.
    - `frontend/src/components/trade-review/SymbolAutocomplete.tsx` —
      consumes the new backend fields and renders empty / search / no-match
      states verbatim.
  - UX behavior implemented (all backend-owned, no frontend reinterpretation):
    - Superseded by P23B-T5: empty focus / empty input now receives a backend
      empty non-search state. A later frontend LRU layer may show local
      recents before or instead of that empty state.
    - Non-empty input renders backend exact-first search results under the
      backend `section_label` ("Search results"), in backend order, capped
      by the backend.
    - No-match renders the backend "Symbol Not Found" message with no
      section header.
    - Section header is a presentational `<li role="presentation"
      aria-hidden="true">`; it is not focusable and does not shift option
      indexing (active-option scroll uses a stable id lookup, not child
      index).
  - Frontend does NOT rank, sort, filter, fuzzy match, or reinterpret
    results. `items`, `section_label`, `result_mode`, and `message` are
    consumed as returned. No quote, price, volume, % move, market status,
    liquidity, tradability, recommendation, or ranking language rendered.
  - Preserved: Trade Review request payload shape; existing form validation
    and submit behavior; the P23A-T2 disabled-state race fix (debounce
    clear, dropdown close, activeIndex reset, in-flight result drop,
    `selectItem`/mouse-handler guards); ARIA combobox/listbox semantics.
  - Safety: no `symbolsApi.validate` wiring (validation remains a future
    task); no `localStorage`/`sessionStorage` reads or writes; no external
    provider, market-data, broker, or TradingAgents calls; no symbol
    lookup data sent to LLM agents; no backend code modified.
  - Commands run:
    - `cd frontend && npx tsc --noEmit` — clean.
    - `cd frontend && npx eslint --max-warnings 0` (4 files) — clean.
    - `cd frontend && npx vite build` — clean (105 modules).
  - Docker Compose full-stack smoke test (postgres + backend:8000 +
    frontend:5173, Vite proxy injecting `X-Local-Access-Token`):
    - Backend contract via proxy curl: current empty `q` should return
      `result_mode="empty"` with no items; `q=NOK` → `result_mode="search"`, `section_label="Search
      results"`, NOK first; `q=ZZZZZ` → `result_mode="no_match"`,
      `section_label="Symbol Not Found"`.
    - Browser (Claude Preview, historical before P23B-T5): empty focus used
      the backend fallback list. Current direction is empty backend response
      plus future browser-local LRU recents. `NOK` → "Search results" header,
      NOK first ✅; `ZZZZZ` → "Symbol Not Found", no header ✅; select first
      option → fills field with `NOK`, closes dropdown ✅; 0 localStorage / 0
      sessionStorage keys ✅.
    - Network log: only `/api/symbols/search?q=...` calls (empty, NOK,
      ZZZZZ); no `/symbols/validate`, no external/provider calls ✅.
  - No backend, provider, external API, storage, LLM/agent, or
    TradingAgents work was added in this task.

### P23A-T5 - Scheduled Nasdaq Symbol Directory Refresh Provider

- Task id: `P23A-T5`
- Title: Scheduled Nasdaq Symbol Directory Refresh Provider
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Replace the tiny in-code symbol universe with a provider-neutral
  normalized symbol directory backed by public Nasdaq Symbol Directory files,
  with a personal-demo scheduled refresh path. Preserve the existing
  `/symbols/search` and `/symbols/validate` frontend contracts.
- Product goal:
  - support broad U.S. stock/ETF/ADR autocomplete coverage for personal demo
    use;
  - keep autocomplete as symbol reference data only;
  - avoid quote, price, volume, option-chain, broker tradability, and
    recommendation claims.
- Dependencies:
  - completed `P23A-T1`
  - completed `P23A-T2`
  - completed `P23A-T3`
  - completed `P23A-T4`
  - architecture contract:
    `docs/codex-b-architecture/PHASE_23A_SYMBOL_LOOKUP_CONTRACT.md`
- Data source direction:
  - public Nasdaq Symbol Directory text files such as `nasdaqlisted.txt` and
    `otherlisted.txt`;
  - app-owned parser normalizes rows into provider-neutral symbol records;
  - raw source rows are not returned by APIs and should not leak into
    frontend contracts.
- Files expected to inspect or change:
  - `backend/app/schemas/symbols.py`
  - `backend/app/services/symbols.py`
  - new backend-only symbol directory parser/cache/refresh modules if useful
  - `backend/app/api/routes/symbols.py` only if dependency wiring is needed
  - backend app startup/scheduler wiring only if the scheduled job is bounded
    and does not block startup
  - `backend/tests/services/test_symbol_lookup.py`
  - `backend/tests/api/test_symbols.py`
  - new parser/refresh tests using local fixture files
  - `docs/shared/implementation_plan.md` verification notes only
- Implementation steps:
  1. Define normalized app-owned symbol records for imported directory rows.
     Keep the API response shape provider-neutral.
  2. Add a parser for local Nasdaq-style fixture files. Cover at least
     Nasdaq-listed and other-listed row shapes in tests.
  3. Normalize symbol, name, exchange, asset class, test-issue status,
     region/currency, support status, and as-of/source labels.
  4. Add a last-good snapshot cache or storage boundary. Refresh should only
     replace the active snapshot after a successful parse/validation pass.
  5. Add a scheduled refresh job for personal-demo use. It may download public
     Symbol Directory files when the scheduler/job runs, but it must not run
     during unit tests and must not block application startup.
  6. Add a manual refresh function/command entrypoint for debugging the same
     importer path.
  7. Preserve synthetic fallback behavior if no imported snapshot exists or
     refresh fails.
  8. Preserve current symbol search semantics: empty non-search state, exact first,
     prefix next, contains next, name/reference contains after that, no fuzzy
     matching.
  9. Add source/as-of labels that clearly identify symbol reference data and
     do not imply quote truth or broker tradability.
  10. Add forbidden-field and forbidden-wording tests.
- Scheduled refresh rules:
  - allowed for personal-demo symbol reference data only;
  - never fetch quotes, prices, volume, options chains, broker data, news, or
    market-data feeds;
  - never require credentials, API keys, `.env`, broker accounts, or paid
    provider setup;
  - never expose raw source rows or raw downloaded payloads in API responses;
  - failures must be sanitized and must keep the last good normalized snapshot
    active;
  - default tests must use local fixture files and make no network calls;
  - commercial/public use remains subject to later provider/licensing review.
- Acceptance criteria:
  - Existing `/symbols/search` and `/symbols/validate` response contracts stay
    compatible for Claude A's autocomplete.
  - Search can use imported normalized symbol records when a good snapshot is
    available.
  - If the imported snapshot is unavailable or refresh fails, search falls
    back safely to synthetic/reference records or returns a sanitized
    unavailable state.
  - Empty-query backend response remains empty and non-search.
  - Non-empty search remains backend-owned and deterministic.
  - No frontend changes are included.
  - No raw provider payload, account/broker data, credential, prompt, LLM
    trace, quote, price, volume, order/execution/advice wording, or
    tradability claim is introduced.
- Tests:
  - parser tests for local Nasdaq-listed fixture rows
  - parser tests for local other-listed fixture rows
  - parser tests for footer/header/as-of handling
  - parser tests for ETF/stock/ADR/test-issue normalization
  - snapshot activation tests: successful refresh replaces active snapshot
  - failure tests: malformed/download failure keeps last good snapshot and
    sanitizes errors
  - service/API compatibility tests for existing search and validation
  - no-network default test assertion or dependency injection guard
  - forbidden-field and forbidden-wording sweep
  - `git diff --check`
- Rollback notes:
  - Revert only importer/cache/scheduler wiring and P23A-T5 verification
    notes.
  - Preserve P23A-T1 through P23A-T4 provider-neutral API and synthetic search
    behavior as fallback.
- Verification notes:
  - 2026-05-28 Codex C added a backend-only Nasdaq Symbol Directory
    parser/importer/cache/refresh foundation while preserving the existing
    `/symbols/search` and `/symbols/validate` response shape consumed by
    P23A-T4 autocomplete.
  - Files changed for this task: `backend/app/services/symbol_directory.py`,
    `backend/app/services/symbols.py`,
    `backend/tests/services/test_symbol_directory.py`,
    `backend/tests/services/test_symbol_lookup.py`,
    `backend/tests/api/test_symbols.py`, and this plan note.
  - Parser/importer design: `symbol_directory.py` parses local
    Nasdaq-style `nasdaqlisted.txt` and `otherlisted.txt` rows into
    app-owned `SymbolRecord`s. It extracts footer file-creation labels,
    normalizes symbol/name/exchange/asset class/test-issue/support fields,
    and never returns raw source rows or raw file payloads through API
    schemas.
  - Provider integration: `SymbolService()` now prefers an active last-good
    `SymbolDirectorySnapshot` via `SymbolDirectorySnapshotProvider` with
    `data_mode="provider_reference"`, `source_label="Nasdaq Symbol
    Directory"`, and safe file/import as-of labels. If no imported snapshot
    exists, the synthetic `DemoSymbolProvider` remains the fallback.
  - Last-good behavior: `SymbolDirectorySnapshotStore` replaces the active
    snapshot only after successful fetch/parse/normalization/validation.
    Failed refreshes raise a sanitized `SymbolDirectoryRefreshError` and keep
    the previous active snapshot.
  - Manual refresh entrypoint: `manual_refresh_nasdaq_symbol_directory_snapshot`
    runs the same importer path with an injected fetcher boundary for local
    demo/debug use.
  - Scheduled refresh design: `SymbolDirectoryRefreshJob` is a
    dependency-free scheduled hook with `enabled=False` by default. It never
    runs at import time, never blocks app startup, and performs no network
    work unless local deployment wiring explicitly enables and invokes the
    job. No scheduler dependency was added.
  - Preserved current symbol search semantics: empty query non-search state,
    exact-first deterministic ordering, prefix/contains/name-reference ordering,
    validation behavior, unsupported/test-issue filtering, provider failure
    sanitization, forbidden-field/wording protections, and local access guard.
  - No frontend, broker, quote, price, volume, option-chain, watchlist,
    screener, market-data SDK, credential/config loader, LLM/agent,
    TradingAgents, persistence, localStorage/sessionStorage, order/execution,
    advice, recommendation, tradability, or raw provider-payload behavior was
    added. Tests use local fixture strings/files only and make no network
    calls.
  - Tests: `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `29 passed in 0.17s`; requested compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/api/test_symbols.py -q`
    passed with `21 passed in 0.09s`; `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
    passed with `71 passed in 0.33s`.
  - Codex B review (2026-05-28): PASS. No blockers. Deferred polish only:
    update the stale route docstring that still says strict-prefix suggestions,
    and optionally strip footer padding delimiters from Nasdaq file-time labels
    for cleaner display.
- Status: `done`

## Phase 23B - Complete Symbol Lookup Personal Demo

Phase goal: finish the symbol lookup feature end-to-end for a personal demo:
the app should use a refreshed broad Nasdaq-style symbol directory when
available, keep a last-good normalized snapshot across backend restarts, keep
autocomplete provider-neutral, and make symbol inputs uppercase in the UI and
submitted payloads.

Shared Phase 23B rules:

- Symbol lookup remains public instrument-reference data only.
- Do not fetch or display quotes, prices, volume, option chains, watchlists,
  screeners, broker tradability, recommendations, or performance signals.
- Do not expose raw downloaded rows, raw source files, provider payloads,
  credentials, `.env`, broker/account data, prompts, LLM traces, or agent
  context.
- Default tests must be offline and use fixture/injected fetch paths.
- Automatic refresh must be opt-in for local/personal demo and must not block
  application startup.
- Frontend must not call Nasdaq or any provider directly; it consumes only the
  backend `/symbols/*` contracts.
- The refreshed symbol directory is global app reference data shared by all
  users; any "recently selected/viewed" list is user/browser-specific state and
  must not be inferred from holdings, broker accounts, portfolio context,
  prompts, LLM context, or trade history.
- Commercial/public use of refreshed symbol-reference data remains subject to
  later licensing/provider review.

### P23B-T1 - Persistent Last-Good Symbol Directory Snapshot

- Task id: `P23B-T1`
- Title: Persistent Last-Good Symbol Directory Snapshot
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Persist the normalized last-good Nasdaq Symbol Directory snapshot
  locally so the backend can restore broad symbol coverage after restart
  without re-fetching at startup.
- Dependencies:
  - completed `P23A-T5`
  - architecture contract:
    `docs/codex-b-architecture/PHASE_23A_SYMBOL_LOOKUP_CONTRACT.md`
- Recommended storage posture:
  - Prefer a small backend-owned local JSON snapshot file or SQLite table
    under an app-data boundary.
  - Do not store raw source files or raw provider rows.
  - Store only normalized app-owned symbol records plus safe source/as-of
    metadata.
- Files expected to inspect or change:
  - `backend/app/services/symbol_directory.py`
  - `backend/app/services/symbols.py`
  - backend settings/app-data helper modules only if an existing pattern exists
  - `backend/tests/services/test_symbol_directory.py`
  - `backend/tests/services/test_symbol_lookup.py`
  - `backend/tests/api/test_symbols.py`
  - `docs/shared/implementation_plan.md` verification notes only
- Implementation steps:
  1. Add a persistence boundary for normalized `SymbolDirectorySnapshot`
     records and safe metadata.
  2. Add load/save helpers that reject malformed snapshots and never expose
     raw source rows.
  3. Ensure `SymbolService()` can use a restored valid snapshot before falling
     back to `DemoSymbolProvider`.
  4. Ensure failed or malformed persisted snapshots fall back safely to the
     synthetic provider.
  5. Preserve existing `/symbols/search` and `/symbols/validate` response
     shape.
- Acceptance criteria:
  - A saved normalized snapshot can be restored after process restart in tests.
  - Malformed snapshot data is ignored or reported through sanitized internal
    errors without breaking search/validation.
  - Synthetic fallback still works when no persisted snapshot exists.
  - No raw source rows, raw files, provider payloads, credentials, quotes,
    prices, broker data, order/execution/advice wording, or frontend changes
    are introduced.
- Tests:
  - persistence save/load round trip with normalized records
  - restart-style restore test
  - malformed snapshot fallback test
  - existing symbol search/validation compatibility tests
  - forbidden-field/wording sweep
  - `git diff --check`
- Rollback notes:
  - Revert only snapshot persistence/load helpers and verification notes.
  - Preserve P23A-T5 in-memory parser/refresh behavior.
- Verification notes:
  - 2026-05-28 Codex C added normalized last-good symbol directory snapshot
    persistence in `backend/app/services/symbol_directory.py`.
  - Persistence design: a bounded JSON snapshot file stores only
    app-owned normalized `SymbolRecord` fields plus safe `source_label`,
    `as_of_label`, and `imported_at` metadata. It does not store raw
    downloaded files, raw provider rows, provider payloads, credentials,
    broker/account data, quotes, prices, volume, prompts, LLM traces, or
    agent context.
  - Added `save_symbol_directory_snapshot`,
    `load_symbol_directory_snapshot`, and
    `restore_active_symbol_directory_snapshot`. Malformed or missing
    persisted snapshots return `None` and allow `SymbolService` to fall back
    to `DemoSymbolProvider` without changing `/symbols/search` or
    `/symbols/validate` response shapes.
  - Added default repo-local cache path
    `cache/symbol_directory_snapshot.json`, which is covered by the existing
    `/cache/` `.gitignore` boundary and is not written during normal tests.
  - Tests added/updated in `backend/tests/services/test_symbol_directory.py`,
    `backend/tests/services/test_symbol_lookup.py`, and
    `backend/tests/api/test_symbols.py` for save/load round trip,
    restart-style restore, malformed snapshot fallback, synthetic fallback,
    forbidden-field/wording sweeps, and existing search/validation
    compatibility.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `39 passed in 0.16s`; requested compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/api/test_symbols.py -q`
    passed with `24 passed in 0.12s`; `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
    passed with `71 passed in 0.30s`.
- Status: `done` (2026-05-28, Codex B reviewed PASS)

### P23B-T2 - Opt-In Local Symbol Directory Refresh Wiring

- Task id: `P23B-T2`
- Title: Opt-In Local Symbol Directory Refresh Wiring
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Wire a local/personal-demo refresh trigger that can fetch public
  Nasdaq Symbol Directory files, parse them through the reviewed importer, save
  the normalized last-good snapshot, and keep the app running on the previous
  snapshot if refresh fails.
- Dependencies:
  - completed `P23B-T1`
- Allowed trigger shape:
  - a backend-only CLI/helper function, or
  - a guarded local-admin endpoint if and only if it uses the existing local
    access posture and returns sanitized status only.
- Scheduled refresh:
  - may be added behind an explicit opt-in flag/config;
  - disabled by default in tests and default app startup;
  - must not block startup;
  - must not make network calls unless explicitly invoked/enabled.
- Files expected to inspect or change:
  - `backend/app/services/symbol_directory.py`
  - backend route/CLI modules only if needed for the chosen trigger
  - `backend/tests/services/test_symbol_directory.py`
  - `backend/tests/api/test_symbols.py` or route tests only if a route is added
  - `docs/shared/implementation_plan.md` verification notes only
- Implementation steps:
  1. Reuse `refresh_nasdaq_symbol_directory_snapshot` and the same injected
     fetch boundary.
  2. Save the normalized snapshot only after successful parse/validation.
  3. Preserve and continue serving the previous last-good snapshot on failure.
  4. Return only sanitized status metadata from any manual trigger.
  5. Add no frontend consumption in this task.
- Acceptance criteria:
  - Manual local refresh can be exercised in tests with injected fixture
    fetchers.
  - Refresh failure keeps the last-good snapshot active and persisted.
  - Default tests and default startup make no network calls.
  - No credentials, `.env`, provider SDK, quotes, prices, broker data,
    watchlists, recommendations, frontend changes, agents, or TradingAgents
    scope is introduced.
- Tests:
  - successful opt-in refresh with injected fixtures
  - failed refresh keeps active and persisted snapshot
  - disabled scheduler does not call fetch
  - startup/import no-network assertion
  - existing symbol search/validation compatibility tests
  - `git diff --check`
- Rollback notes:
  - Revert only refresh trigger/scheduler wiring and verification notes.
  - Preserve persistent last-good snapshot helper if `P23B-T1` remains useful.
- Verification notes:
  - 2026-05-28 Codex C added opt-in local refresh wiring that reuses the
    reviewed Nasdaq Symbol Directory parser/importer path and persists only
    the normalized last-good snapshot after full success.
  - Refresh trigger design: added `refresh_and_persist_nasdaq_symbol_directory_snapshot`
    and `manual_refresh_and_persist_nasdaq_symbol_directory_snapshot`. These
    build a snapshot through the injected fetch boundary, save the normalized
    JSON snapshot, and only then activate it. If any step fails, a sanitized
    `SymbolDirectoryRefreshError` is raised and the active/persisted
    last-good snapshot remains unchanged.
  - Added protected opt-in route `POST /symbols/directory/refresh` returning
    sanitized status only (`status`, `data_mode`, `source_label`,
    `as_of_label`, `imported_at`, `record_count`, `message`). The route uses
    the existing app-level local access guard and a dependency-injected
    refresh runner for offline tests.
  - Scheduler wiring remains dependency-free and disabled by default through
    `SymbolDirectoryRefreshJob(enabled=False)`. No app startup hook, default
    import path, or test path performs a network call or blocks startup.
  - No frontend, broker, quote, price, volume, option-chain, watchlist,
    screener, market-data SDK, credential/config loader, `.env`, LLM/agent,
    TradingAgents, localStorage/sessionStorage, order/execution, advice,
    recommendation, tradability, or raw provider-payload behavior was added.
  - Tests added/updated for successful opt-in refresh with injected fixture
    fetchers, failed refresh preserving active and persisted last-good
    snapshots, disabled scheduler no-fetch behavior, refresh route success
    and sanitized failure, local access guard, and default no-network service
    path.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `39 passed in 0.16s`; requested compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/api/test_symbols.py -q`
    passed with `24 passed in 0.12s`; `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
    passed with `71 passed in 0.30s`.
- Status: `done` (2026-05-28, Codex B reviewed PASS)

### P23B-T3 - Trade Review Autocomplete Uppercase And Recent Selection Polish

- Task id: `P23B-T3`
- Title: Trade Review Autocomplete Uppercase And Recent Selection Polish
- Owner: Claude A implementation, Codex B frontend contract review
- Objective: Finish the Trade Review autocomplete UX so Symbol and Underlying
  inputs are always displayed/submitted uppercase, empty focus respects the
  backend empty non-search state, search consumes backend ordering exactly,
  and no-match still shows backend-owned `Symbol Not Found`.
- Dependencies:
  - completed and Codex B-reviewed `P23B-T2`
- Files expected to inspect or change:
  - `frontend/src/components/trade-review/SymbolAutocomplete.tsx`
  - `frontend/src/components/trade-review/TradeReviewForm.tsx`
  - `frontend/src/types/symbols.ts` only if backend contract fields changed
  - `frontend/src/api/symbols.ts` only if route contract changed
  - `docs/shared/implementation_plan.md` verification notes only
- Implementation steps:
  1. Force uppercase in the visible input value as the user types.
  2. Ensure `onChange` and submitted Trade Review payload values for symbol
     and underlying are uppercase.
  3. Preserve backend-owned search/ranking: no frontend sorting, fuzzy
     matching, scoring, filtering, or provider-specific parsing.
  4. Preserve backend-owned `section_label`, `result_mode`, and `message`,
     including the empty non-search state for empty query.
  5. Preserve disabled-state race protections from `P23A-T2`.
  6. Keep recent symbols non-private for this slice: no inference from
     holdings, broker accounts, portfolio context, prompts, LLM context, or
     trade history.
- Acceptance criteria:
  - Typing lowercase `nvda` displays/submits `NVDA`.
  - Typing `nok` displays/submits `NOK`; exact `NOK` remains first because the
    backend orders it first.
  - Empty focus does not fabricate recents; true recents are deferred to a
    browser-local LRU follow-up.
  - Unknown input shows backend-owned `Symbol Not Found`.
  - No frontend provider calls, quotes, prices, volume, recommendations,
    tradability claims, localStorage/sessionStorage writes, or form payload
    shape changes.
- Tests:
  - frontend typecheck
  - frontend lint on changed files with `--max-warnings 0`
  - frontend build
  - browser smoke: lowercase typing uppercases; empty focus empty state;
    `NOK` exact first; no-match state; no storage keys; only `/symbols/search`
    network calls for autocomplete.
- Rollback notes:
  - Revert only autocomplete/form polish and verification notes.
  - Preserve backend symbol contracts and refresh functionality.
- Status: `done` (2026-05-28, Codex B reviewed PASS)
- Verification notes (2026-05-28, Claude A):
  - Files changed:
    - `frontend/src/components/trade-review/SymbolAutocomplete.tsx` — the
      input `onChange` now emits `e.target.value.toUpperCase()`, so the
      controlled value, the debounced search query, and (via the parent)
      the submitted payload are all uppercase. Header comment updated to
      describe the P23B-T3 uppercase behavior.
  - Files reviewed, not changed:
    - `frontend/src/components/trade-review/TradeReviewForm.tsx` — already
      uppercased submitted symbol/underlying via `.trim().toUpperCase()`
      (lines 135/141); kept as defense-in-depth. No payload shape change.
    - `frontend/src/types/symbols.ts`, `frontend/src/api/symbols.ts` — no
      backend contract change, left untouched.
  - Behavior verified (Docker full-stack: postgres + backend:8000 +
    frontend:5173, Vite proxy injecting `X-Local-Access-Token`):
    - Typing lowercase `nvda` → input displays `NVDA`; search fires with
      `q=NVDA`.
    - Typing lowercase `nok` → input displays `NOK`; backend "Search
      results" with exact `NOK` first (`[NOK, NOKBF, NOKPF, LNOK, NKRKF,
      NKRKY]`).
    - Superseded by P23B-T5: empty focus/input now receives an empty
      non-search state from the backend. True recents are deferred to a
      browser-local LRU follow-up.
    - Unknown `zzzzz` → backend `Symbol Not Found` rendered verbatim, no
      section header.
    - Selecting a result fills the uppercase symbol (`NOK`) and closes the
      dropdown.
  - Ordering: backend order consumed verbatim; no frontend sort, rank,
    filter, score, or fuzzy match added.
  - Disabled-state protections from P23A-T2 preserved (debounce clear,
    dropdown close, in-flight result drop, `selectItem`/mouse-handler
    guards) — untouched by this change.
  - Safety: no `symbolsApi.validate` wiring; 0 localStorage / 0
    sessionStorage keys observed; autocomplete network calls hit only
    `/api/symbols/search` (`q=NVDA`, `q=NOK`, `q=ZZZZZ`, `q=` empty) — no
    `/symbols/validate`, no external/provider calls; no quotes, prices,
    volume, tradability, recommendation, advice, or execution language; no
    Trade Review payload shape change; no backend code modified.
  - Commands run:
    - `cd frontend && npx tsc --noEmit` — clean.
    - `cd frontend && npx eslint --max-warnings 0` (4 files) — clean.
    - `cd frontend && npx vite build` — clean (105 modules).

### P23B-T4 - Automatic Broad Nasdaq-Traded Directory Refresh For Local Demo

- Task id: `P23B-T4`
- Title: Automatic Broad Nasdaq-Traded Directory Refresh For Local Demo
- Owner: Codex B implementation/review
- Objective: Make symbol autocomplete function against the broad public Nasdaq
  Trader symbol directory in the Docker personal-demo flow without requiring a
  manual terminal refresh command.
- Dependencies:
  - completed `P23B-T1`
  - completed `P23B-T2`
  - completed `P23B-T3`
- Scope:
  - Switch the default public directory source to `nasdaqtraded.txt` so the
    normalized app-owned directory covers Nasdaq-traded cross-market symbols
    such as `INTC`, `GLD`, and `SLV`.
  - Add opt-in Docker startup refresh through
    `SYMBOL_DIRECTORY_REFRESH_ON_STARTUP=true`, preserving no-network default
    behavior for tests and non-Docker imports.
  - Persist the normalized last-good snapshot under `backend/cache/`, which is
    gitignored, so Docker volume mounts can reuse it after backend restart.
- Safety boundaries:
  - Public symbol-reference data only; no quotes, prices, volumes, options
    chains, broker tradability claims, provider credentials, API keys, broker
    data, LLM/agent/TradingAgents integration, localStorage/sessionStorage, or
    order/execution/advice/recommendation behavior.
  - If refresh fails, startup must not crash; the app restores the last-good
    snapshot if available or falls back to the synthetic provider.
- Verification notes (2026-05-28, Codex B):
  - Files changed:
    - `backend/app/services/symbol_directory.py` — added
      `NASDAQ_TRADED_URL`, made `nasdaqtraded.txt` the default source, mapped
      `Listing Exchange` values including `Q -> NASDAQ`, moved the default
      normalized snapshot cache to `backend/cache/symbol_directory_snapshot.json`,
      and added a safe opt-in startup refresh helper.
    - `backend/app/main.py` — added startup hook that only runs when
      `SYMBOL_DIRECTORY_REFRESH_ON_STARTUP` is true.
    - `docker-compose.yml` — enables that startup refresh by default for the
      local Docker personal-demo flow.
    - `.gitignore` — ignores `backend/cache/`.
    - `backend/tests/services/test_symbol_directory.py` — added coverage for
      `nasdaqtraded.txt`, `INTC`/`GLD`/`SLV`, default source selection,
      backend-local cache path, due-refresh behavior, and disabled-by-default
      startup refresh hook.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `44 passed in 0.19s`; compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
    passed with `71 passed in 0.42s`; `git diff --check` passed.
  - Status: `done`.

### P23B-T5 - Symbol Recents Boundary And Default Suggestions Contract Cleanup

- Task id: `P23B-T5`
- Title: Symbol Recents Boundary And Default Suggestions Contract Cleanup
- Owner: Codex C backend contract cleanup, Claude A frontend follow-up
- Objective: Stop presenting any backend global fallback list as true
  user-specific "Recently viewed" history, and define the safe boundary for a
  future frontend/browser LRU recent-symbol list.
- Dependencies:
  - completed `P23B-T4`
- Problem statement:
  - The backend previously returned a fixed empty-query list
    (`NVDA`, `AAPL`, `QQQ`, `SPY`, `AMD`) under `section_label="Recently viewed"`.
  - This list was not built from the current user's searches or selections.
    Product direction now says empty query should return no backend symbols;
    true recents belong to current-user/browser-local state only.
  - True recents should be current-user/browser-specific LRU state, updated
    only on intentional selection or successful form submit.
- Backend contract cleanup scope for Codex C:
  1. Rename the empty-query backend response away from "recent" semantics and
     do not return a fixed global symbol list.
  2. Use a truthful empty state such as `result_mode="empty"` with no items;
     true recent symbols are supplied by a later frontend/browser LRU layer.
  3. Preserve the existing provider-neutral symbol directory search and
     validation behavior for non-empty queries.
  4. Do not add user history persistence, localStorage, browser storage,
     frontend changes, broker/account inference, trade-history inference, or
     backend per-user recents in this task.
  5. Keep response safety unchanged: no prices, quotes, volume, tradability,
     recommendations, advice, order/execution wording, raw source rows, raw
     provider payloads, credentials, broker/account data, prompts, LLM traces,
     or agent context.
- Frontend follow-up scope for Claude A after Codex C review:
  - Implement true per-browser LRU recents in the autocomplete using a UI-only
    local key such as `poa-symbol-recents`.
  - Update recents only when the user selects a backend suggestion or
    successfully submits a valid uppercase symbol/underlying.
  - Never update recents from mere typing, search results, broker holdings,
    portfolio context, prompts, LLM context, or trade history.
  - Show local LRU recents on empty focus; if none exist, show an empty state
    and do not backfill symbols from the backend.
  - Capacity should be 5 symbols, newest first, deduplicated by moving an
    existing symbol to the top.
- Acceptance criteria for Codex C:
  - Empty query no longer labels or returns a backend global default list as
    "Recently viewed".
  - Backend tests assert the new empty `result_mode`, empty item list, and
    non-search semantics.
  - Non-empty search ordering, `Symbol Not Found`, validation, provider
    fallback, and directory refresh behavior remain unchanged.
  - No frontend, storage, user-history, broker, agent, provider-call, quote,
    price, order/execution, advice, or recommendation behavior is added.
- Tests:
  - symbol lookup service tests
  - symbol API tests
  - route/schema contract tests for the empty-query result mode
  - compatibility tests for non-empty search and validation
  - `git diff --check`
- Verification notes (2026-05-28, Codex C):
  - Backend empty-query symbol search now returns `result_mode="empty"`,
    `items=()`, and `no_match=false`; the fixed global fallback list
    `[NVDA, AAPL, QQQ, SPY, AMD]` was removed from the empty-query path.
  - Updated schema vocabulary, symbol service behavior, service tests, and API
    tests; non-empty search ordering, no-match behavior, validation, provider
    failure, and directory snapshot behavior are unchanged.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/api/test_symbols.py -q`
    passed with `24 passed in 0.20s`; `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_directory.py -q`
    passed with `20 passed in 0.06s`; `git diff --check` passed.
- Codex B review (2026-05-28): PASS. Empty query returns
  `result_mode="empty"`, `items=[]`, `no_match=false`, and no backend
  recents/default symbols. Non-empty search ordering, validation,
  provider-reference/synthetic/unavailable behavior, provider failure
  sanitization, and offline tests remain intact. Docs were corrected to remove
  stale active-plan language that implied backend-generated recent/default
  symbols. Frontend TypeScript/comment follow-up is still required so Claude A
  can consume `result_mode="empty"` and implement browser-local LRU recents.
- Rollback notes:
  - Revert only empty-query naming/schema cleanup and tests.
  - Preserve broad directory refresh and uppercase autocomplete behavior.
- Status: `done` (2026-05-28, Codex B reviewed PASS).

### P23B-T6 - Browser-Local Symbol Recents LRU For Trade Review Autocomplete

- Task id: `P23B-T6`
- Title: Browser-Local Symbol Recents LRU For Trade Review Autocomplete
- Owner: Claude A (frontend)
- Objective: Implement the frontend follow-up promised by `P23B-T5` — a true
  per-browser LRU "Recently viewed" symbol list owned entirely by the frontend,
  now that the backend empty-query path returns `result_mode="empty"` with no
  backend recents/defaults.
- Dependencies:
  - completed `P23B-T5` (Codex B reviewed PASS)
  - completed `P23B-T3` (uppercase autocomplete polish)
- Scope implemented:
  1. `frontend/src/types/symbols.ts`: `SymbolSearchResultMode` narrowed to
     `"empty" | "search" | "no_match" | "unavailable"`; removed stale `"recent"`
     literal; header comments updated to note recents are browser-local.
  2. New `frontend/src/lib/symbolRecents.ts`: localStorage LRU under the single
     UI-only key `poa-symbol-recents`, capacity 5, newest-first, deduped by
     moving an existing symbol to the top. Persists ONLY the 7 public reference
     fields (`symbol, name, asset_class, exchange, region, currency,
     is_supported`) via a `sanitize()` whitelist. No prices, quotes, volume,
     account/portfolio/broker context, prompts, LLM context, or trade history.
     All storage access is try/catch-wrapped (degrades to `[]` on
     unavailable/SSR storage).
  3. `SymbolAutocomplete.tsx`: empty focus shows browser-local recents under a
     "Recently viewed" section label; with no recents it shows a neutral empty
     state (`No recent symbols yet. Start typing to search.`) — never backend
     symbols and never "Symbol Not Found". Non-empty backend search renders the
     backend `section_label`/`message` verbatim with backend-owned ordering.
     Recents are recorded only on intentional selection (`addSymbolRecent`).
  4. `TradeReviewForm.tsx`: on successful submit, `promoteSymbolRecent` moves an
     already-known recent to the top (no fabrication, no payload-shape change).
- Preserved: uppercase input/payload (`P23B-T3`); backend-owned ordering; no
  frontend ranking/sorting/fuzzy/filtering of backend results; disabled-state
  race guards; ARIA combobox/listbox; Trade Review payload shape.
- Tests / verification (2026-05-28, Claude A):
  - `cd frontend && npx tsc --noEmit` clean.
  - `npx eslint --max-warnings 0` clean on types/symbols, api, lib/symbolRecents,
    SymbolAutocomplete, TradeReviewForm.
  - `npx vite build` clean (106 modules).
  - Browser smoke (Claude Preview): empty focus with no recents → neutral empty
    state (no fake `NVDA/AAPL/QQQ/SPY/AMD`); LRU ordering verified
    (DELL → INTC → GLD → SLV → INTC re-promote); capacity capped at 5 (oldest
    dropped); stored object keys are exactly the 7 whitelisted fields; only
    `poa-symbol-recents` present (0 sessionStorage keys); empty focus with
    recents → "Recently viewed" list; promote-on-submit moved an existing symbol
    to the top with no duplicate. Network listing showed autocomplete hit only
    `/api/symbols/search` (uppercase `q`), no `/symbols/validate`, no external
    or provider calls.
- Safety confirmation: no backend changes, no new endpoints, no external/
  provider calls, no LLM/agent/TradingAgents integration, no quotes/prices/
  volume/tradability/recommendation/advice/order/execution language, no
  broker/account data. Exactly one storage key (`poa-symbol-recents`); no other
  localStorage/sessionStorage key added.
- Follow-up (deferred): creating a brand-new recent from a typed-but-never-
  selected symbol at submit time is intentionally deferred — it would require
  wiring `symbolsApi.validate` to obtain validated public display fields rather
  than fabricating them. Current submit path only promotes already-known
  recents.
- Codex B review (2026-05-28): PASS. Frontend type mirrors backend
  `result_mode="empty"`; local LRU recents are isolated to the single
  UI-only `poa-symbol-recents` key; persisted fields are public symbol
  reference fields only; empty focus no longer shows backend default symbols;
  non-empty search remains backend-ordered; disabled-state guards, uppercase
  behavior, ARIA combobox/listbox behavior, and Trade Review payload shape are
  preserved. Submit-time creation of a never-selected typed symbol remains
  deferred until a validation/display-field path is approved. Verification:
  `cd frontend && npx tsc --noEmit` clean; focused eslint clean; `cd frontend
  && npx vite build` clean; `git diff --check` clean.
- Status: `done` (2026-05-28, Codex B reviewed PASS). Do not mark broader
  Phase 23B complete unless asked.

### P23B-T7 - Symbol Offline Fixture Cleanup

- Task id: `P23B-T7`
- Title: Symbol Offline Fixture Cleanup
- Owner: Codex B cleanup
- Objective: Make the backend fallback symbol records clearly test/dev-only so
  they cannot be confused with the broad Nasdaq directory, backend recents, or
  production reference data.
- Scope implemented:
  - Moved the small fallback symbol records out of `symbols.py` into
    `backend/app/services/symbol_fixtures.py`.
  - Renamed fallback labels to `Offline symbol fallback fixture` /
    `Offline fixture · not live market data`.
  - Trimmed the fallback set to only records needed for deterministic unit
    tests; broad symbols such as `INTC`, `GLD`, and `SLV` must come from the
    imported Nasdaq-traded directory snapshot, not from hardcoded examples.
  - Added a regression test that the offline fallback is not treated as a
    broad directory.
- Verification:
  - `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `45 passed in 0.21s`.
  - `git diff --check`
    passed.
- Status: `done` (2026-05-28).

### P23B-T8 - Agent Console Symbol Autocomplete Parity

- Task id: `P23B-T8`
- Title: Agent Console Symbol Autocomplete Parity
- Owner: Claude A implementation, Claude B frontend safety/design review
- Objective: Bring the Trade Review symbol-entry experience (debounced
  `SymbolAutocomplete` against the existing `/symbols` lookup, keyboard
  selection, empty/loading/error states) to the Agent Console symbol input(s).
- Dependencies:
  - completed `P23B-T6` (Trade Review autocomplete + browser-local recents)
  - existing Phase 19A Agent Console (`POST /agent-team/trade-review-analysis/preview`)
- Scope:
  - Frontend only. No new backend endpoints, schemas, routes, or API-client
    surfaces. No storage writes, provider/LLM calls, or financial computation.
  - Do not modify the shared Trade Review form behavior or regress it.
- Finding (2026-05-30, Claude A — no code change required):
  - The Agent Console (`frontend/src/pages/AgentTeamAnalysisPage.tsx`) does not
    own a plain symbol input. In both its pre-run and re-run layouts it reuses
    the shared `TradeReviewForm`, which already wires `SymbolAutocomplete` into
    the stock/ETF "Symbol" field (`TradeReviewForm.tsx` ~L299) and the option
    "Underlying" field (~L319) — identical component, props, debounce, keyboard
    navigation, and loading/empty/error behavior to Trade Review.
  - Symbol / quantity / price defaults are already empty (`useState("")`), so
    there are no prefilled `XYZ`/`100`/`50.00` demo values; the empty state is a
    valid, non-submitting state.
  - The only inline `<input>` in the agent-team components is the intentionally
    disabled follow-up composer (`AgentTeamComposerPlaceholder.tsx`), which is
    not a symbol field and must remain inert (Phase 21A paused).
  - The console continues to consume only the existing
    `POST /agent-team/trade-review-analysis/preview` contract; no request fields
    added.
  - Implementing the task literally would require either modifying the shared
    `TradeReviewForm` (forbidden by the task / would affect Trade Review) or
    duplicating a console-only symbol input (contradicts component reuse), so no
    change was made. PM (user) decision 2026-05-30: close as already-satisfied;
    do not relax the "don't modify the form" constraint or clear the option-flow
    numeric demo defaults (expiration/strike/contracts/premium/multiplier).
  - Verification of current (unchanged) state: `cd frontend && npm run typecheck`
    clean; `npm run build` clean. No diff produced by this task.
- Claude B frontend safety/design review (2026-05-30): PASS — confirmed the
  "no code change required" conclusion by source inspection (not a diff):
  - Parity present via the shared form: `AgentTeamAnalysisPage.tsx` imports
    `TradeReviewForm` (L4) and renders it in both the re-run rail (L97) and the
    pre-run layout (L116), each with `hideSyntheticMode`. `TradeReviewForm` wires
    `SymbolAutocomplete` for the stock/ETF "Symbol" field (L299) and the option
    "Underlying" field (L319) — same component/props/states; no console-only
    plain symbol input exists.
  - Defaults empty: `symbol`/`quantity`/`priceAssumption`/`underlying` are all
    `useState("")` (L77–79, L82) — no `XYZ`/`100`/`50.00`.
  - No hidden symbol input: the remaining `TradeReviewForm` `<input>`s are review-
    mode/context radios (L184/197/218/229) and the numeric/date `TextField`
    helper (L383); the only agent-team inline `<input>` is the disabled follow-up
    composer (`AgentTeamComposerPlaceholder.tsx:63`: `disabled`, `tabIndex={-1}`,
    aria "not yet active"), which stays inert (Phase 21A paused).
  - Request path unchanged: `handleSubmit` → `agentTeamApi.previewTradeReviewAnalysis`
    → `POST /agent-team/trade-review-analysis/preview` (page header comment L26);
    no new fields. `git` shows no diff for this task.
  - No safety regression (no change): analysis-only framing, mock/provider
    labeling (`AgentTeamRunSummary`), disabled composer, and broker-vs-market
    freshness separation all intact.
  - Accepted as-is per PM 2026-05-30: shared form not modified; option-flow
    numeric demo defaults (expiration 2026-06-19 / strike 45 / contracts 1 /
    premium 1.85 / multiplier 100) intentionally retained. Minor non-blocking
    inconsistency noted (stock fields empty, option numerics prefilled); deferred.
  - Browser smoke not required for a zero-diff task; optional one-time check
    suggested for the `SymbolAutocomplete` dropdown inside the narrow re-run
    `mp-ac-rail` layout (L94–98) to confirm the popover doesn't clip — not a gate.
  - Plan hygiene follow-up (2026-05-30, Codex B): renumbered this no-diff parity
    task from the duplicate `P23B-T7` id to `P23B-T8`; `P23B-T7` remains the
    completed Symbol Offline Fixture Cleanup task.
- Status: `done` (2026-05-30, Claude B review PASS; no code change — parity
  already satisfied via the shared `TradeReviewForm`).

## Phase 24A - Economic Calendar Awareness Foundation

Phase goal: add a backend-owned economic calendar feature for Dashboard display
that resembles a Forex Factory-style macro calendar while using FMP Economic
Calendar as the personal-demo provider path. Ticker/company news is explicitly
out of scope for this phase and belongs to a later agent/tool design.

Shared Phase 24A rules:

- FMP Economic Calendar is approved for local/personal-demo evaluation only,
  behind backend abstractions and opt-in network paths.
- Synthetic/replay fixtures remain the first backend contract and default test
  path.
- No Forex Factory scraping, ticker/company news provider, Bloomberg, Yahoo,
  Google, LLM, broker, market-data quote, TradingAgents, WebSocket, or streaming
  implementation in Phase 24A.
- No trading-signal, recommendation, advice, buy/sell, safe-to-trade,
  ready-to-trade, guaranteed-return, or urgency language.
- Do not personalize events from private holdings, broker accounts, portfolio
  context, prompts, LLM context, or trade history.
- Do not send economic calendar data to LLM agents without a later approved
  sanitized evidence contract.
- Dashboard display must always include source/freshness and "not a trading
  signal" semantics.

### P24A-T1 - Economic Calendar Contracts And Synthetic Fixtures

- Task id: `P24A-T1`
- Title: Economic Calendar Contracts And Synthetic Fixtures
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Define the provider-neutral backend contracts for a macro
  economic calendar table, with deterministic synthetic/replay fixtures that
  exercise high/medium/low/unknown importance, actual/forecast/previous labels,
  empty states, and unavailable states.
- Dependencies:
  - completed Phase 20D Dashboard content boundary
  - architecture contract:
    `docs/codex-b-architecture/PHASE_24A_ECONOMIC_NEWS_AWARENESS_CONTRACT.md`
- Endpoint shape:
  - `GET /economic-calendar/events`
- Conceptual response fields:
  - wrapper:
    - `data_mode`
    - `source_label`
    - `as_of_label`
    - `freshness_label`
    - `window_start`
    - `window_end`
    - `timezone`
    - `importance_source`
    - `items`
    - `demo_notice`
    - `is_trading_signal`
    - `limitations`
  - item:
    - `event_reference`
    - `event_date_label`
    - `event_time_label`
    - `event_title`
    - `event_type`
    - `importance`
    - `importance_source`
    - `country`
    - `currency`
    - `actual_label`
    - `forecast_label`
    - `previous_label`
    - `unit_label`
    - `source_label`
    - `freshness_label`
    - `is_trading_signal`
    - `data_mode`
- Enum direction:
  - `data_mode`: `synthetic`, `replay`, `provider_reference`, `unavailable`
  - `importance`: `high`, `medium`, `low`, `unknown`
  - `importance_source`: `provider`, `app_classified`, `unavailable`
  - `event_type`: `economic_release`, `central_bank`, `holiday`, `speech`,
    `other`
- Implementation steps:
  1. Define typed backend schemas for the economic calendar list and items.
  2. Add a provider protocol and deterministic synthetic provider.
  3. Add synthetic fixtures shaped like a macro calendar day: CPI/PCE/FOMC/jobs
     style high-impact events, medium-impact releases, speeches, and unknown
     impact examples.
  4. Add app-owned references that do not expose raw provider IDs.
  5. Add a read-only protected route.
  6. Enforce `is_trading_signal=false` in schemas/tests.
  7. Add forbidden-field and forbidden-wording tests.
  8. Do not add FMP integration, frontend wiring, agent ingestion, WebSocket,
     scheduler, or persistence in this slice.
- Acceptance criteria:
  - Synthetic calendar responses look ready for a Forex Factory-like table but
    are clearly synthetic/demo-labelled.
  - Actual/forecast/previous are display labels only; no frontend or schema
    expects numeric calculation.
  - Importance is typed and source-labelled.
  - Empty and unavailable states are deterministic and safe.
  - No private portfolio/account/broker data, raw provider payloads,
    credentials, prompts, LLM traces, quotes, prices, or order/execution/advice
    wording appears.
  - Default tests make no external calls.
- Tests:
  - schema and API contract tests
  - service tests for populated calendar, empty state, unavailable state,
    high/medium/low/unknown importance
  - invariant tests that wrapper and every item have `is_trading_signal=false`
  - forbidden-field and forbidden-wording sweep
  - local access guard
  - `git diff --check`
- Rollback notes:
  - Revert only economic calendar schemas, service, route, tests, and
    verification notes.
  - Preserve Dashboard, symbol lookup, market data, and agent-team surfaces.
- Verification notes (2026-05-29, Codex C):
  - Added provider-neutral economic calendar read schemas:
    `EconomicCalendarEventListRead`, `EconomicCalendarEventRead`, and
    `EconomicCalendarRefreshStatusRead` with typed `data_mode`,
    `importance`, `importance_source`, and `event_type` vocabularies.
  - Added `SyntheticEconomicCalendarProvider` and `EconomicCalendarService`
    with deterministic synthetic macro fixtures covering high/medium/low/
    unknown importance, economic releases, central-bank events, speeches,
    holidays, empty state, unavailable state, source/freshness labels, and
    `is_trading_signal=false` invariants.
  - Added protected routes `GET /economic-calendar/events` and
    `POST /economic-calendar/refresh`; default refresh route is disabled/
    sanitized until explicitly injected/configured.
  - Files changed: `backend/app/schemas/economic_calendar.py`,
    `backend/app/services/economic_calendar.py`,
    `backend/app/api/routes/economic_calendar.py`, `backend/app/main.py`,
    `backend/tests/services/test_economic_calendar.py`, and
    `backend/tests/api/test_economic_calendar.py`.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
    passed with `25 passed in 0.19s`; symbol compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `45 passed in 0.21s`; `git diff --check` passed.
- Codex B review (2026-05-29): PASS. Contract shape, synthetic/default
  behavior, safety invariants, protected route registration, empty/unavailable
  states, and no-external-call boundary verified.
- Status: `done` (2026-05-29, Codex B reviewed PASS).

### P24A-T2 - Deterministic Economic Event Importance Classifier

- Task id: `P24A-T2`
- Title: Deterministic Economic Event Importance Classifier
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Add a backend-owned deterministic classifier for provider events
  whose source lacks a usable Forex Factory-style impact label. This lets FMP
  data support a red/yellow/orange style UI without pretending the importance
  label is provider truth.
- Dependencies:
  - completed and Codex B-reviewed `P24A-T1`
- Scope:
  - App-owned rule/table classifier only.
  - Output must set `importance_source="app_classified"`.
  - Unknown or unmapped events degrade to `importance="unknown"`.
  - No LLM classification, sentiment, market reaction prediction, or urgency
    language.
- Suggested high-importance families:
  - FOMC/Fed rate decision
  - CPI / Core CPI
  - PCE / Core PCE
  - Nonfarm Payrolls / Unemployment Rate
  - GDP headline releases
  - ISM/PMI headline releases
  - Retail Sales headline releases
- Suggested medium-importance families:
  - Durable Goods
  - Jobless Claims
  - Housing/New Home Sales
  - Industrial Production
  - Consumer Confidence
  - central-bank speeches
- Acceptance criteria:
  - Classifier is deterministic and unit-tested.
  - Classifier does not use portfolio context, ticker symbols, user holdings,
    LLMs, or provider private metadata.
  - Classifier output is explicitly labelled as app-classified.
  - Existing synthetic contract behavior remains compatible.
- Tests:
  - high/medium/low/unknown classification tests
  - case/whitespace/punctuation normalization tests
  - no-advice/no-urgency wording tests
  - `git diff --check`
- Verification notes (2026-05-29, Codex C):
  - Added deterministic `classify_economic_event(...)` and
    `infer_economic_event_type(...)` helpers. The classifier is table/rule
    based only, uses no portfolio/ticker/broker/LLM context, and labels
    classifier output as `importance_source="app_classified"`.
  - Coverage includes FOMC/Fed rate decision, CPI/PCE, Nonfarm Payrolls,
    unemployment/GDP/ISM/PMI/Retail Sales, Durable Goods, Jobless Claims,
    Housing/New Home Sales, Industrial Production, Consumer Confidence,
    central-bank speeches, holidays, and unknown fallback.
  - Verification is included in the focused Phase 24A test run:
    `25 passed in 0.19s`; `git diff --check` passed.
- Codex B review (2026-05-29): PASS. Classifier is deterministic/table-based,
  labelled `importance_source="app_classified"`, and does not use LLMs,
  portfolio, ticker, broker, holdings, or provider-private metadata.
- Status: `done` (2026-05-29, Codex B reviewed PASS).

### P24A-T3 - FMP Economic Calendar Evaluation Adapter

- Task id: `P24A-T3`
- Title: FMP Economic Calendar Evaluation Adapter
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Add a backend-only FMP Economic Calendar adapter that maps FMP
  calendar responses into the provider-neutral `P24A-T1` contracts for
  personal-demo evaluation.
- Dependencies:
  - completed and Codex B-reviewed `P24A-T1`
  - completed and Codex B-reviewed `P24A-T2`
- Scope:
  - Backend-only.
  - Injected/mock client tests first.
  - No network call in default tests or module import.
  - No frontend code.
  - No WebSocket/streaming.
  - No ticker/company news.
  - No agent ingestion.
  - No raw FMP payload exposure.
- Provider mapping rules:
  - Map event date/time, country, currency, event name, actual, forecast, and
    previous fields into backend-owned display labels.
  - Use provider importance only if FMP supplies a documented compatible field;
    otherwise apply `P24A-T2` classifier and label `importance_source`.
  - Emit `data_mode="provider_reference"` only for explicit opt-in evaluation
    paths.
  - Missing actual/forecast/previous values render as `null` or safe display
    dashes through the read model; never fabricate values.
  - Malformed provider rows are skipped or degraded safely without raw payload
    leakage.
- Credential/config rules:
  - No key in frontend code, docs, tests, fixtures, logs, or committed files.
  - Any future local key must be read only by backend runtime configuration.
  - Missing key returns unavailable/synthetic fallback, not crash.
- Acceptance criteria:
  - Adapter maps representative FMP-shaped synthetic payloads into the stable
    internal contract.
  - Failure, malformed rows, missing values, and rate-limit-like errors degrade
    to sanitized unavailable state.
  - No raw provider response, exception body, URL containing credentials, or
    provider-private identifier is exposed.
  - No external calls in default tests.
- Tests:
  - injected-client mapping tests
  - malformed/missing value tests
  - provider failure sanitization tests
  - importance classifier integration tests
  - contract compatibility tests against `P24A-T1`
  - `git diff --check`
- Verification notes (2026-05-29, Codex C):
  - Added `FmpEconomicCalendarProvider` behind an injected
    `FmpEconomicCalendarClient` protocol. No FMP SDK, credential loader,
    frontend code, startup fetch, or default network path was added.
  - Adapter maps FMP-shaped synthetic rows for date/time, title, country,
    currency, actual, forecast, previous, optional unit, and optional
    provider-compatible importance. Missing actual/forecast/previous values
    remain `null`; malformed rows are skipped; provider failures raise a
    sanitized `EconomicCalendarRefreshError`.
  - Provider output uses `data_mode="provider_reference"` and source/freshness
    labels such as `FMP Economic Calendar evaluation` and
    `Provider reference · not a trading signal`; app classification is used
    when provider importance is unavailable.
  - Verification is included in the focused Phase 24A test run:
    `25 passed in 0.19s`; `git diff --check` passed.
- Codex B review (2026-05-29): PASS. FMP adapter is backend-only behind an
  injected client boundary, has no SDK/credential/startup/network default path,
  maps provider-shaped rows into normalized records, and sanitizes malformed
  rows/failures without raw payload leakage.
- Status: `done` (2026-05-29, Codex B reviewed PASS).

### P24A-T4 - Opt-In Economic Calendar Refresh And Last-Good Snapshot

- Task id: `P24A-T4`
- Title: Opt-In Economic Calendar Refresh And Last-Good Snapshot
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Make FMP-backed economic calendar data usable in the personal
  Docker demo through an opt-in refresh path and normalized last-good cache.
- Dependencies:
  - completed and Codex B-reviewed `P24A-T3`
- Scope:
  - Backend-only.
  - Store normalized app-owned event records only.
  - Do not persist raw FMP payloads.
  - Disabled by default outside explicit local/demo configuration.
  - No startup crash if refresh fails.
  - No frontend changes.
- Suggested behavior:
  - Refresh today plus a short forward window, such as today through the next
    7 calendar days.
  - Optional backward window for same-day events, if needed for actual values.
  - Cache under `backend/cache/`, which is gitignored.
  - Preserve previous last-good snapshot on failure.
  - Surface `freshness_label`, `as_of_label`, and `data_mode`.
- Suggested optional route:
  - `POST /economic-calendar/refresh`
  - protected by existing local access guard
  - returns sanitized status only
- Acceptance criteria:
  - Successful refresh parses, validates, persists normalized records, then
    activates the snapshot.
  - Failed refresh preserves active and persisted last-good snapshot.
  - No raw provider payload, raw exception, credential, or private metadata is
    persisted or returned.
  - Default tests/import path make no network call.
- Tests:
  - refresh success with injected fixture client
  - refresh failure preserves last-good snapshot
  - restore after restart from normalized cache
  - missing/malformed cache fallback
  - protected refresh route success/failure/local-access tests
  - `git diff --check`
- Verification notes (2026-05-29, Codex C):
  - Added normalized last-good snapshot persistence under
    `backend/cache/economic_calendar_snapshot.json`. The cache stores only
    app-owned event records and safe metadata (`source_label`, `as_of_label`,
    `freshness_label`, window, timezone, importance source, data mode,
    imported timestamp, limitations); no raw FMP payloads are persisted.
  - Added in-memory active snapshot store, restore/load/save helpers, and
    `refresh_and_persist_economic_calendar_snapshot(...)` that parses and
    persists before activation. Refresh failure preserves active and persisted
    last-good state and returns sanitized status through the route.
  - Added protected opt-in `POST /economic-calendar/refresh`; the default
    runner is intentionally unconfigured and returns a sanitized failure unless
    tests or future local/demo wiring inject a provider-backed runner.
  - No WebSocket/streaming, frontend, ticker/company news, agent ingestion,
    LLM/TradingAgents, market quote, broker, credential, or live provider
    behavior was added.
  - Verification: focused Phase 24A tests passed with `25 passed in 0.19s`;
    symbol compatibility tests passed with `45 passed in 0.21s`;
    `git diff --check` passed.
- Codex B review (2026-05-29): PASS. Opt-in refresh route returns sanitized
  status only; default runner is intentionally unconfigured; normalized
  last-good cache stores app-owned records and safe metadata under
  `backend/cache/`; refresh failures preserve active/persisted last-good state.
- Status: `done` (2026-05-29, Codex B reviewed PASS).

### P24A-T5 - Dashboard Economic Calendar Panel

- Task id: `P24A-T5`
- Title: Dashboard Economic Calendar Panel
- Owner: Claude A implementation, Codex B frontend contract review
- Objective: Add a Dashboard panel that renders the reviewed economic calendar
  contract in a compact table inspired by Forex Factory, without scraping or
  copying provider UI.
- Dependencies:
  - completed and Codex B-reviewed `P24A-T1`
  - completed and Codex B-reviewed `P24A-T4` if live personal-demo provider
    display is desired; otherwise may consume synthetic contract only
- Display direction:
  - Table columns: time, currency/region, impact, event, actual, forecast,
    previous, source/freshness.
  - Use our MP design tokens and typed icons; no emoji.
  - Red/orange/yellow-style impact visual may be used, but must have text
    labels and must not imply trading urgency.
  - Always show "Economic awareness" / "not a trading signal" copy.
  - Show demo/provider/reference/freshness labels visibly.
- Safety boundaries:
  - No ticker/company news.
  - No market quotes, prices, volume, charts, watchlist, or screener.
  - No personalized filtering by holdings or account.
  - No LLM/agent use.
  - No execution/advice wording.
  - No frontend provider calls; frontend consumes backend only.
- Acceptance criteria:
  - Loading, error, empty, unavailable, synthetic, and provider-reference states
    are handled.
  - Actual/forecast/previous labels render verbatim from backend.
  - Importance labels render with `importance_source` visible or accessible.
  - No frontend calculation or classification.
  - No new storage keys.
  - No new endpoints beyond reviewed backend calendar endpoints.
- Tests:
  - frontend typecheck
  - frontend lint on changed files with `--max-warnings 0`
  - frontend build
  - browser smoke at 1024/1280/1440 light/dark
  - `git diff --check`
- Verification notes (2026-05-29, Claude A):
  - Files changed: new `frontend/src/types/economicCalendar.ts` (mirrors
    `EconomicCalendarEventListRead`/`EconomicCalendarEventRead` and the four
    enums); new `frontend/src/api/economicCalendar.ts` (wraps only
    `GET /economic-calendar/events`; the POST refresh endpoint is intentionally
    not wrapped); new
    `frontend/src/components/economic-calendar/EconomicCalendarPanel.tsx`
    (self-fetching panel); `frontend/src/pages/DashboardPage.tsx` (import +
    render in the left body column).
  - Endpoint consumed: `GET /api/economic-calendar/events` only. Browser network
    listing confirmed no `/economic-calendar/refresh` and no external/provider
    calls; every request was GET under `/api`.
  - States: loading → `LoadingSkeleton`; error → `ErrorState` with Retry
    (failure stays local to the panel and does not break the Dashboard); empty
    (`items.length === 0`) and `data_mode === "unavailable"` → `EmptyState`;
    synthetic/`demo_notice` → `DemoChip` + "Synthetic fixture" badge;
    `provider_reference`/`replay` → mode badge plus source/freshness/as-of line.
  - actual/forecast/previous render backend labels verbatim (null → "—"); no
    parsing, numeric comparison, or value-based color-coding. Importance uses a
    text-labelled tone badge (high/medium/low/unknown — never color-only) with
    `importance_source` shown via an "app classified" row label, a table
    caption, and a per-badge title attribute. "Economic awareness only · Not a
    trading signal" plus backend `limitations` are always visible.
  - No frontend calculation/classification, no ticker/company news, quotes,
    prices, volume, charts, watchlist, screener, holdings/account
    personalization, LLM/agent use, storage writes, or new endpoints/storage
    keys. No forbidden execution/advice/urgency wording.
  - Tests: `cd frontend && npm run typecheck` clean; `npx eslint
    --max-warnings 0` clean on the 4 changed files; `npm run build` clean
    (108 modules); `git diff --check` clean.
  - Browser smoke (Claude Preview, synthetic fixture, 8 events): panel renders
    at 1024/1280/1440 in light and dark mode with no horizontal page overflow
    (the wide table scrolls inside its own container); loading/empty/unavailable
    states and source/freshness/not-a-trading-signal labels are readable; other
    Dashboard panels do not regress.
- Deferred polish: live `provider_reference` rendering is exercised only against
  the synthetic fixture in this slice (the backend currently returns
  `data_mode="synthetic"`); the provider-reference branch is implemented but not
  yet visually verified against a live personal-demo provider.
- Status: `done` (2026-05-29, Codex B frontend contract review PASS). Do not
  mark broader Phase 24A complete.

### P24A-T6 - FMP Runtime Refresh Wiring For Personal Demo

- Task id: `P24A-T6`
- Title: FMP Runtime Refresh Wiring For Personal Demo
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Make the reviewed economic calendar path actually usable in the
  local Docker demo by wiring `POST /economic-calendar/refresh` to FMP when
  `FMP_API_KEY` is present in the backend environment.
- Dependencies:
  - completed and Codex B-reviewed `P24A-T1` through `P24A-T5`
  - `.env.example` includes backend-only `FMP_API_KEY` placeholder
- Scope:
  - Backend-only.
  - No frontend changes.
  - No startup network call.
  - No scheduler, WebSocket, polling, or streaming.
  - No ticker/company news endpoints.
  - No LLM/agent/TradingAgents ingestion.
  - No market quotes, prices, volume, watchlists, screeners, or options data.
- Required behavior:
  - Read `FMP_API_KEY` from backend environment only.
  - If `FMP_API_KEY` is missing, `POST /economic-calendar/refresh` returns the
    existing sanitized failure response and preserves any last-good snapshot.
  - If `FMP_API_KEY` is present, `POST /economic-calendar/refresh` fetches FMP
    economic calendar rows for the configured window, normalizes them through
    the existing `FmpEconomicCalendarProvider`, persists the normalized
    last-good snapshot, activates it, and returns sanitized refresh status.
  - `GET /economic-calendar/events` continues to read active/restored
    normalized snapshots, falling back to synthetic/unavailable behavior as
    already reviewed.
  - Fetch window defaults to today through the next 7 calendar days, with an
    optional same-day/backward allowance only if needed for actual values.
  - Provider output remains `data_mode="provider_reference"` and
    `is_trading_signal=false`.
  - Actual/forecast/previous values remain backend display labels.
  - FMP errors, malformed responses, rate-limit responses, and network failures
    are sanitized; no raw exception body, raw URL with API key, or raw provider
    payload is returned or persisted.
- Implementation notes:
  - Prefer a tiny app-owned HTTP client using the standard library or an
    already-present backend dependency; do not add a dependency unless truly
    necessary.
  - Keep the existing injected client boundary testable. Unit tests must use
    fake/injected clients and must not call FMP.
  - Do not log the API key or include it in errors.
  - Do not add `.env` reads to frontend/Vite.
- Acceptance criteria:
  - With no `FMP_API_KEY`, refresh is a safe sanitized failure and no network
    call is attempted.
  - With a test-injected FMP client/transport, refresh succeeds, persists only
    normalized app-owned records plus safe metadata, and `GET
    /economic-calendar/events` returns provider-reference records.
  - Provider failure preserves active and persisted last-good snapshot.
  - Malformed provider rows are skipped/degraded through existing normalization.
  - Route remains protected by the existing local access guard.
  - No raw FMP payload, API key, URL-with-key, raw exception body, credential,
    provider private identifier, advice, recommendation, urgency, or execution
    wording leaks.
- Tests:
  - focused economic calendar service/API tests
  - route test for missing key safe failure
  - route/service test for successful injected provider refresh
  - route/service test for provider failure preserving last-good snapshot
  - regression test that imports/app startup do not fetch
  - `git diff --check`
- Verification notes (2026-05-29, Codex C):
  - Added backend-only FMP runtime refresh wiring. `POST
    /economic-calendar/refresh` now builds a refresh runner from backend
    environment: missing `FMP_API_KEY` returns the existing sanitized failure;
    present `FMP_API_KEY` creates a tiny standard-library
    `FmpEconomicCalendarHttpClient`, maps rows through the reviewed
    `FmpEconomicCalendarProvider`, persists only normalized app-owned records,
    activates the last-good snapshot, and returns sanitized status.
  - `GET /economic-calendar/events` remains unchanged: it reads active/restored
    normalized snapshots and otherwise falls back to the reviewed synthetic
    provider path. No startup network call, scheduler, frontend, LLM/agent,
    TradingAgents, broker, market-data, news-tool, WebSocket, or streaming work
    was added.
  - Runtime client behavior: FMP URL/API-key usage stays backend-only; tests use
    fake/injected transports only; raw URLs with keys, raw provider payloads,
    raw exception bodies, credentials, and provider-private metadata are not
    returned or persisted.
  - Files changed: `backend/app/services/economic_calendar.py`,
    `backend/app/api/routes/economic_calendar.py`,
    `backend/tests/services/test_economic_calendar.py`,
    `backend/tests/api/test_economic_calendar.py`, and this plan.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
    passed with `29 passed in 0.20s`; symbol compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `45 passed in 0.42s`; `git diff --check` passed.
- Codex B review (2026-05-29): PASS. Runtime refresh is backend-only,
  explicit-refresh only, safe on missing key, and preserves normalized
  last-good behavior. Deferred polish: verify the exact FMP endpoint URL with
  the user's key and add an env override if needed.
- Status: `done` (2026-05-29, Codex B reviewed PASS).

### P24A-T7 - Dashboard Economic Calendar Refresh Controls

- Task id: `P24A-T7`
- Title: Dashboard Economic Calendar Refresh Controls
- Owner: Codex B implementation
- Objective: Make the Dashboard economic calendar panel trigger the reviewed
  backend refresh path automatically on page load and expose a manual circular
  refresh control in the panel header.
- Dependencies:
  - completed and Codex B-reviewed `P24A-T6`
- Scope:
  - Frontend only.
  - No frontend API key access.
  - No direct FMP/provider calls.
  - No scheduler, polling loop, WebSocket, or background interval.
  - No ticker/company news, quotes, prices, watchlists, screeners, agents, or
    LLM ingestion.
- Behavior:
  - On first panel mount, call `POST /economic-calendar/refresh`, then call
    `GET /economic-calendar/events`.
  - Manual circular-arrow refresh button calls the same refresh-then-load path.
  - If refresh fails or is unconfigured, show the sanitized backend message and
    still load the last available/synthetic/unavailable event view.
  - Existing event display remains contract-driven: actual/forecast/previous
    labels render verbatim and importance remains backend/provider labelled.
- Verification notes (2026-05-29, Codex B):
  - Added `EconomicCalendarRefreshStatusRead` frontend type.
  - Added `economicCalendarApi.refresh()` wrapping only
    `POST /economic-calendar/refresh`.
  - Added typed `MpIcon` `refresh` glyph.
  - Updated `EconomicCalendarPanel` to auto-refresh once on mount and provide a
    disabled-while-refreshing manual refresh button.
  - Refresh failures remain local to the panel and use sanitized backend/API
    messages; the Dashboard still loads events afterward.
  - Tests: `cd frontend && npm run typecheck` clean; targeted `npx eslint
    --max-warnings 0` clean on changed frontend files; `npm run build` clean;
    `git diff --check` clean.
- Status: `done` (2026-05-29).

### P24A-T8 - Economic Calendar US Window And Timing Contract

- Task id: `P24A-T8`
- Title: Economic Calendar US Window And Timing Contract
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Refine the economic calendar backend contract so the Dashboard can
  show a clean US-only macro calendar for a user-selected date window.
- Dependencies:
  - completed and Codex B-reviewed `P24A-T6`
- Scope:
  - Backend only.
  - No frontend changes.
  - No ticker/company news.
  - No quotes, prices, volume, watchlists, screeners, options data, broker data,
    LLM/agent use, TradingAgents, WebSocket, streaming, or scheduling.
- Required behavior:
  - `GET /economic-calendar/events` accepts optional `start_date` and
    `end_date` query params as ISO dates.
  - Default query window is the current app date only.
  - Maximum query window is 7 calendar days inclusive; invalid or too-large
    ranges return a safe 400 response.
  - Backend filters economic events to US-only macro events by normalized
    country/currency semantics (`US`/`USD`) before returning records.
  - Backend preserves the existing refresh/cache path. If the active snapshot
    contains more than the requested window, the read endpoint filters it.
  - Add safe machine-readable timing fields to each event:
    - `event_datetime_utc: str | None`
    - `event_has_occurred: bool | None`
  - Keep existing display labels for compatibility:
    `event_date_label` and `event_time_label`.
  - `event_has_occurred` is backend-owned and computed from
    `event_datetime_utc` against current UTC time when the timestamp is known.
  - Actual/forecast/previous remain backend-owned display labels. Do not add
    numeric parsing or comparison behavior.
- Contract boundaries:
  - Do not add source/freshness/currency display changes in backend for UI
    convenience; frontend will remove those columns in `P24A-T9`.
  - Do not expose raw FMP payloads, raw provider URLs, API keys, provider IDs,
    raw exception bodies, advice/recommendation/urgency/execution wording, or
    trading signals.
  - Keep `is_trading_signal=false` on wrapper/items.
  - Keep `data_mode`, `source_label`, `as_of_label`, and `freshness_label` in
    the response for provenance, even if the frontend chooses a compact display.
- Tests:
  - default today-only window
  - explicit valid 1-day and 7-day windows
  - invalid date format, reversed range, and range greater than 7 days
  - US/USD filtering excludes non-US/non-USD rows
  - event timestamp and occurred flag for past/future/unknown-timed events
  - refresh/cache compatibility with filtered reads
  - no raw provider payload/secret/advice wording leakage
  - `git diff --check`
- Verification notes (2026-05-29, Codex C):
  - Added optional `start_date` / `end_date` query params to
    `GET /economic-calendar/events`. The default route window is the current
    app date only; valid explicit windows may cover up to 7 calendar days
    inclusive. Invalid date format, reversed ranges, and longer ranges return
    safe 400 responses.
  - Added backend US macro filtering for returned reads using normalized
    `country == "US"` or `currency == "USD"` semantics. Raw provider fields
    remain hidden.
  - Added machine-readable event timing fields to
    `EconomicCalendarEventRead`: `event_datetime_utc` and
    `event_has_occurred`. Display labels `event_date_label` and
    `event_time_label` remain unchanged. Occurrence state is backend-owned and
    becomes `null` when the timestamp is unknown.
  - Preserved refresh/cache behavior: `POST /economic-calendar/refresh` still
    refreshes/persists normalized records, while GET filters active/restored
    snapshots to the requested window. Synthetic fallback remains available.
  - Files changed: `backend/app/schemas/economic_calendar.py`,
    `backend/app/services/economic_calendar.py`,
    `backend/app/api/routes/economic_calendar.py`,
    `backend/tests/services/test_economic_calendar.py`,
    `backend/tests/api/test_economic_calendar.py`, and this plan.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
    passed with `37 passed in 0.84s`; symbol compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `45 passed in 0.51s`; `git diff --check` passed.
  - Blocker fix (2026-05-29, Codex C): `event_datetime_utc` now interprets
    `event_date_label` + `event_time_label` in the calendar timezone
    (`America/New_York`) using standard-library `zoneinfo`, then converts to
    true UTC. Regression coverage asserts `2026-05-29 08:30` ET serializes as
    `2026-05-29T12:30:00Z`, `16:00` ET serializes as
    `2026-05-29T20:00:00Z`, occurrence comparison uses true UTC, and unknown
    times remain `null`/`null`. Verification after fix:
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
    passed with `37 passed in 0.52s`; symbol compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `45 passed in 0.45s`; `git diff --check` passed.
- Claude B safety review (2026-05-29): PASS. Verified timezone conversion
  (`08:30` ET → `12:30:00Z`, `16:00` ET → `20:00:00Z` via `zoneinfo`),
  occurrence comparison against true UTC, unknown-time → `null`/`null`,
  US/USD filtering excludes non-US/non-USD rows, window resolution
  (today-only default, ≤7 days inclusive, reversed/invalid/too-wide → safe
  400), `is_trading_signal=false` invariant across record/schema/read layers,
  injected-transport-only tests (no live FMP), FMP key backend-only, and
  refresh fail-closed to last-good. Re-ran `37 passed` / `45 passed`;
  `git diff --check` clean.
- Claude B fixes applied (2026-05-29, granted by user):
  - I1 (hardening): `FmpEconomicCalendarHttpClient.fetch_events` now raises the
    sanitized `EconomicCalendarRefreshError` with `from None` so the
    API-key-bearing request URL can never enter `__cause__`/`__context__` and
    reach a traceback/log. Added regression asserting `__cause__ is None` and
    `__suppress_context__ is True`.
  - D1 (defense-in-depth): aligned `PROHIBITED_ECONOMIC_CALENDAR_PHRASES` with
    the contract's broader substrings — added `trade signal`, broadened
    `market will move` → `market will` and `guaranteed return` → `guaranteed`
    (verified no false-positive against `is_trading_signal` field name or
    backend labels; full suite still `37 passed`).
  - Files changed by fix: `backend/app/services/economic_calendar.py`,
    `backend/app/schemas/economic_calendar.py`,
    `backend/tests/services/test_economic_calendar.py`.
  - Deferred to P24A-T9 (frontend): add `event_datetime_utc` /
    `event_has_occurred` to `frontend/src/types/economicCalendar.ts` when the
    table consumes them; review the auto-`POST /refresh`-on-mount behavior
    (`EconomicCalendarPanel.tsx`) so a configured FMP key is not hit on every
    Dashboard mount. DST gap/ambiguous wall-time handling relies on `zoneinfo`
    default fold — acceptable for macro release times; note only.
- Status: `done` (2026-05-29, Claude B safety review PASS; I1/D1 fixes applied
  and verified). Codex B architecture/integration signoff may proceed.
- Contract amendment (2026-05-29, during P24A-T9, user-authorized): the
  **7-calendar-day maximum query window was removed**. `GET /economic-calendar/events`
  now accepts any valid ordered window; only invalid date format and reversed
  ranges (`end < start`) still return 400. `resolve_economic_calendar_window` no
  longer raises on long ranges and `MAX_ECONOMIC_CALENDAR_WINDOW_DAYS` was
  deleted. The GET path still only *filters the cached snapshot* to the window
  (it does not fetch from the provider), so a wider window does not amplify FMP
  load; `POST /refresh` still uses its own default fetch window. Backend tests
  updated accordingly (former >7-day 400 cases replaced with wide-window 200 /
  successful-resolution assertions). Flagged here for Codex B architecture
  awareness since this changes the T8 windowing contract. Follow-up: to surface
  events beyond the cached snapshot for very wide windows, the refresh fetch
  window would need widening (separate task).

### P24A-T9 - Dashboard Economic Calendar Table Polish

- Task id: `P24A-T9`
- Title: Dashboard Economic Calendar Table Polish
- Owner: Claude A implementation, Claude B frontend safety/UX review
  (Claude B owns the T9 review gate; Codex B optional architecture signoff
  only if a backend-contract concern surfaces during review)
- Objective: Make the Dashboard economic calendar panel behave like a compact
  US macro calendar: today by default, user-selectable date window, local-time
  display, cleaner table, and muted past rows.
- Dependencies:
  - completed and Codex B-reviewed `P24A-T8`
- Scope:
  - Frontend only.
  - No backend schema invention.
  - No direct FMP/provider calls and no frontend API key access.
  - No localStorage/sessionStorage writes.
  - No ticker/company news, quotes, prices, watchlists, screeners, LLM/agent
    use, TradingAgents, WebSocket, streaming, or polling loop.
- Required behavior:
  - Default panel query is current day.
  - Add a date/date-range picker that allows at most 7 calendar days.
  - Call `GET /economic-calendar/events?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
    for the selected window.
  - Keep the existing manual circular-arrow refresh control; after refresh,
    reload the selected date window.
  - Display event time in the user's browser timezone using
    `event_datetime_utc`; include AM/PM in the Time column.
  - If `event_datetime_utc` is unavailable, fall back to backend
    `event_time_label` and do not fabricate timezone conversion.
  - Remove the Currency / region column.
  - Remove the Source / freshness column.
  - Keep columns focused on: time, impact, event, actual, forecast, previous.
  - Filtered backend results are US-only; frontend should not add its own
    country/currency filtering except defensive display fallback.
  - If `event_has_occurred` is true, render the whole row with a muted grey
    background.
  - Remove noisy demo/source/freshness/limitations clutter from the visible
    panel body. Keep only a compact, non-dominant status/provenance indicator
    when data is synthetic, unavailable, or refresh failed.
  - Keep "not a trading signal" visible but compact.
- Safety/contract requirements:
  - Render actual/forecast/previous labels verbatim.
  - Do not compute surprises, compare actual vs forecast, color values by
    outcome, rank events, or imply trading urgency.
  - Importance badge must include text label, not color-only.
  - No advice/recommendation/order/execution/safe-to-trade/ready-to-trade
    wording.
- Tests:
  - frontend typecheck
  - targeted lint with `--max-warnings 0`
  - frontend build
  - browser smoke at 1024/1280/1440 in light and dark modes
  - verify today default, 7-day max, AM/PM local time display, no currency/source
    columns, and grey past rows
  - `git diff --check`
- Verification notes (2026-05-29, Claude A — proposed, pending Claude B gate):
  - Files changed (frontend only): `frontend/src/types/economicCalendar.ts`
    (added `event_datetime_utc: string | null` and
    `event_has_occurred: boolean | null` to `EconomicCalendarEventRead`,
    mirroring the T8 backend fields exactly); `frontend/src/api/economicCalendar.ts`
    (`events()` now accepts an optional `{ startDate, endDate }` window and
    appends `start_date`/`end_date` query params; `refresh()` unchanged);
    new `frontend/src/components/economic-calendar/EconomicCalendarRangePicker.tsx`
    (single dual-month range calendar); rewritten
    `frontend/src/components/economic-calendar/EconomicCalendarPanel.tsx`.
    `DashboardPage.tsx` unchanged (panel is self-contained, no props).
  - Date window: a single flight-ticket-style two-month range calendar replaces
    the From/To inputs. Click a start date, then an end date; the inclusive span
    highlights (with hover preview), and days beyond `start + 6` are disabled so
    the window can never exceed 7 days. The backend remains authoritative (a
    >7-day request still returns 400, surfaced via `ErrorState`). The trigger
    shows the applied window label; a "Today" action and prev/next month nav are
    included; outside-click/Escape close the popover (`width: max-content` keeps
    the two months side by side, `maxWidth` allows wrap on small screens).
  - Refresh semantics (per user revision): every refresh shows the current day.
    On mount (incl. browser page refresh) the panel loads today via the read
    endpoint only (no `POST /refresh`). The manual circular-arrow Refresh button
    snaps the window back to today, calls `POST /economic-calendar/refresh`, then
    reloads today; a `failed` refresh shows a compact dashed notice and keeps the
    last-good snapshot. No polling, no auto-refresh-on-mount.
  - Table: a Date column is the first column (browser-local weekday + date),
    shown once per date group. Rows are ordered chronologically by date then
    time using the backend `event_datetime_utc` instant (neutral ordering, not
    importance/outcome ranking). Rows are zebra-grouped by calendar date: all
    rows of one date share one background; consecutive dates alternate between
    two neutral surfaces (`transparent` / `--mp-paper-2`). The Time column formats
    `event_datetime_utc` into browser-local AM/PM time (e.g. `12:30Z → 7:30 AM`,
    `18:00Z → 1:00 PM`), falling back to `event_time_label` when null with no
    fabricated conversion. `event_has_occurred === true` rows keep a text "past"
    marker so occurrence is never color-only. Columns: Date · Time · Impact ·
    Event · Actual · Forecast · Previous (Currency/region and Source/freshness
    removed). Demo/source/freshness sit in a compact provenance row shown only
    for synthetic/unavailable data; "Economic awareness only · Not a trading
    signal" stays compact.
  - Safety: actual/forecast/previous rendered verbatim (null → "—"); no surprise
    computation, actual-vs-forecast comparison, value-based coloring, or urgency.
    Row background encodes calendar date only — never value/outcome. Importance
    badge keeps a text label (not color-only). No frontend country/currency
    filtering (US-only is backend-owned). No advice/recommendation/order/
    execution/safe-to-trade/ready-to-trade wording. No provider calls or API
    keys in React; no localStorage/sessionStorage; no LLM/agent/streaming.
  - Tests: `cd frontend && npm run typecheck` clean; `npx eslint
    --max-warnings 0` clean on the 4 changed files; `npm run build` clean
    (109 modules); `git diff --check` clean.
  - Browser smoke (Claude Preview, synthetic fixture): verified at 1024/1280/1440
    in light and dark modes with no horizontal page overflow (the dual-month
    popover sits side by side and stays within the viewport). Confirmed
    today-default mount load (`GET …/events?start_date=…&end_date=…` only, no
    `POST /refresh`); range picker applying `May 12–18` and `May 29–Jun 4`
    windows; the 7-day cap disabling days past `start + 6` with inclusive
    range/hover highlighting; chronological date-then-time ordering; zebra
    grouping (`May 29` transparent, `May 30` `rgb(238,240,245)`, `Jun 2`
    transparent, `Jun 3` grey, `Jun 4` transparent with its two rows sharing one
    color and the date shown once); local AM/PM times; the "past" marker on the
    occurred row; and the Refresh button snapping back to today. The
    refresh-failed inline notice was also observed live (backend `POST /refresh`
    returned `failed`; the panel showed "…last good snapshot was preserved." and
    kept today's data). DST gap/ambiguous wall-time handling is backend-owned
    (`zoneinfo`), per T8.
- Follow-up revision (2026-05-29, Claude A — user-requested):
  - Labeling: the header chip previously rendered the shared `DemoChip`
    ("demo · not yet connected"), which was misleading — the panel IS wired to
    the backend; the data is merely synthetic because the live FMP provider is
    not configured in this environment. Replaced it with an accurate "Synthetic
    data" `Badge` (tooltip explains the provider is not connected here). The
    compact provenance footer still shows `Synthetic fixture · …not live calendar
    data · As of …`. When an FMP key is configured backend-side the same endpoint
    returns `data_mode="provider_reference"` and the labels switch automatically.
  - 7-day cap removed (backend + frontend): see the T8 "Contract amendment" note
    above for the backend change. Frontend: `EconomicCalendarRangePicker`
    `maxDays` is now optional; the panel passes no cap, so no calendar days are
    disabled and the "up to N days" hint is hidden. The picker still requires an
    ordered range (clicking before the start restarts the selection).
  - Verification: `cd backend && ./.venv/bin/python -m pytest -q` → `766 passed,
    92 skipped` (DB-destructive skips only); economic-calendar suite
    `36 passed`. Frontend `npm run typecheck` / `eslint --max-warnings 0`
    (picker + panel) / `npm run build` (109 modules) clean; `git diff --check`
    clean. Browser smoke (synthetic fixture): the 8-day window `May 29–Jun 5`
    now loads all 8 events (previously 400-capped), a ~48-day window returns 200,
    the picker shows 0 disabled days after a start pick, and the header reads
    "Synthetic data". Local-time grouping stays internally consistent (a midnight-
    ET Jun 5 holiday correctly displays as 11:00 PM local on Jun 4 and groups
    there, since the Date column, sort, and zebra all key off the same local
    instant).
- Proposed status: implementation complete and self-verified by Claude A
  (including the user's range-calendar / refresh-to-today / date-column +
  zebra-grouping revision, the synthetic-data labeling fix, and the
  user-authorized 7-day-cap removal). **Handed off to Claude B for the T9
  frontend safety/UX review gate; the backend windowing-contract amendment is
  flagged for Codex B architecture awareness.** Do not mark `done` until Claude
  B returns PASS. Status remains `not_started` → propose `in_review` pending that
  gate. Do not mark broader Phase 24A complete.

## Phase 24B - FRED Economic Awareness Migration

Phase goal: replace the failed free-tier FMP economic-calendar path with a
backend-owned FRED foundation for official U.S. macro data and release
awareness, while preserving the existing Dashboard "Economic awareness" surface
and all analysis-only boundaries.

Why this phase exists:

- FMP Economic Calendar proved unsuitable for the free personal-demo path: the
  current FMP stable economic-calendar endpoint is restricted to an upgraded
  plan, while legacy endpoints are deprecated/blocked.
- FRED is approved for the next personal-demo evaluation because it is an
  official macroeconomic data source with a free API key, broad U.S. macro
  series coverage, release metadata, and clear attribution requirements.
- FRED is not a Forex Factory clone: it does not provide consensus forecast
  values or red/orange/yellow impact labels. Portfolio Copilot must keep its
  own deterministic event registry and importance classifier.

Shared Phase 24B rules:

- Backend-only FRED access. The frontend must never receive or use
  `FRED_API_KEY` and must not call FRED directly.
- Live FRED smoke calls are allowed only through explicit backend commands or
  tests that require the developer's local `.env`; default tests must use
  injected fake clients and no network.
- Respect FRED's published API throttling behavior. FRED documents `429 Too
  Many Requests`; the current error documentation states up to 2 requests per
  second is allowed before 429. Backend refresh must therefore batch/cache
  conservatively, avoid burst fan-out, and degrade to last-good/unavailable on
  throttling.
- Include the required FRED notice anywhere user-facing FRED-backed data is
  displayed: "This product uses the FRED® API but is not endorsed or certified
  by the Federal Reserve Bank of St. Louis."
- Some FRED series may have third-party restrictions. Start only with
  official/public U.S. macro series that can be displayed safely for a personal
  demo; keep questionable series behind caveats or out of the initial registry.
- Forecast values remain unavailable/null unless a separate licensed forecast
  source is approved later.
- No ticker/company news, holdings-personalized news, market quotes, option
  chains, watchlists, screeners, LLM/agent ingestion, TradingAgents work,
  advice/recommendation, urgency, or execution language.

### P24B-T1 - FRED Backend Provider And Official Macro Snapshot

- Task id: `P24B-T1`
- Title: FRED Backend Provider And Official Macro Snapshot
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Add a backend-only FRED provider path that maps a small
  app-owned U.S. macro event/series registry into the existing
  economic-awareness contract, replacing FMP as the practical personal-demo
  provider while preserving synthetic fallback and last-good cache behavior.
- Dependencies:
  - completed Phase 24A economic-calendar contracts and Dashboard panel
  - `FRED_API_KEY` placeholder in `.env.example`; real key remains local only
  - official FRED API docs and terms/attribution requirements
- Expected files/modules:
  - `backend/app/services/economic_calendar.py` or a small split provider module
    if Codex C finds the file too large
  - `backend/app/schemas/economic_calendar.py`, only if additive fields are
    needed for FRED attribution/provenance
  - `backend/app/api/routes/economic_calendar.py`
  - `backend/tests/services/test_economic_calendar.py`
  - `backend/tests/api/test_economic_calendar.py`
  - `.env.example`, only if key naming/comments need refinement
  - `docs/shared/implementation_plan.md`, verification notes only
- Initial registry:
  - CPI / Core CPI candidates: `CPIAUCSL`, `CPILFESL`
  - PCE / Core PCE candidates: `PCEPI`, `PCEPILFE`
  - GDP candidates: `GDP`, `A191RL1Q225SBEA`
  - Payrolls / unemployment candidates: `PAYEMS`, `UNRATE`
  - Initial jobless claims candidate: `ICSA`
  - Retail sales candidate: `RSAFS`
  - Durable goods candidate: `DGORDER`
  - Treasury/rate context candidates: `DGS2`, `DGS10`, `T10Y2Y`,
    `DFF`, `DFEDTARU`, `DFEDTARL`
  - ISM/PMI and FOMC date support should be caveated or deferred if FRED
    licensing/source/timing semantics are unclear.
- Implementation steps:
  1. Add a `FredEconomicCalendarProvider` / client boundary using injected
     transport in tests and `FRED_API_KEY` only at explicit runtime refresh.
  2. Add a compact deterministic macro registry mapping event keys to display
     names, categories, importance (`high|medium|low|unknown`), FRED
     release/series candidates, caveats, and expected display units.
  3. Fetch only the minimum observations/metadata needed per registered series;
     do not fan out faster than the documented FRED throttle. Handle 429 as a
     sanitized unavailable/last-good-preserved state.
  4. Normalize FRED observations into backend-owned display labels:
     `actual_label`, `previous_label`, `unit_label`, `source_label`,
     `freshness_label`, `as_of_label`, and attribution/disclaimer text.
  5. Keep `forecast_label=None` unless a future licensed forecast source is
     approved.
  6. Preserve `is_trading_signal=false` on wrapper and every item.
  7. Keep app-owned importance classification clearly labelled; never imply a
     trade signal or market-moving guarantee.
  8. Preserve synthetic fallback, last-good cache, and sanitized refresh
     failure behavior.
  9. Add one explicit live-smoke command/test path that is skipped by default
     unless an opt-in environment flag is present. It may verify one or two low-
     cost FRED requests only; it must not print or leak the key.
- Acceptance criteria:
  - Default tests use fake FRED responses and make no network calls.
  - Explicit live smoke is opt-in, low-request-count, and sanitized.
  - Missing/invalid key, 401/400/429/500, malformed data, third-party caveat,
    and empty/no-observation scenarios degrade safely.
  - No raw FRED payloads, raw URLs with keys, credentials, exception bodies, or
    provider-private metadata leak to responses/log-style strings/tests.
  - Response remains source-labelled, attribution-labelled, analysis-only, and
    not a trading signal.
  - Existing `GET /economic-calendar/events` frontend contract remains
    compatible unless Codex B approves a tiny additive field.
- Tests:
  - Focused economic-calendar service/API tests.
  - Existing symbol lookup tests to ensure route registration did not regress.
  - `git diff --check`.
- Rollback notes:
  - Revert only FRED provider/client/registry additions and related tests/notes;
    keep existing Phase 24A synthetic/FMP-safe fallback unless PM explicitly
    removes it.
- Verification notes (2026-05-31, Codex C):
  - Added backend-only FRED macro snapshot support without schema changes. FRED
    attribution is carried through existing `limitations` using the required
    notice: "This product uses the FRED® API but is not endorsed or certified
    by the Federal Reserve Bank of St. Louis."
  - Added `FredEconomicCalendarClient`, `FredEconomicCalendarHttpClient`,
    `FredEconomicCalendarProvider`, and a compact deterministic FRED macro
    registry covering CPI/Core CPI, PCE/Core PCE, GDP/real GDP growth,
    payrolls/unemployment, jobless claims, retail sales, durable goods, and
    Treasury/fed-funds rate context. ISM/PMI and exact FOMC date support remain
    deferred.
  - Runtime `POST /economic-calendar/refresh` now uses `FRED_API_KEY` through
    backend-only environment wiring. Missing key returns sanitized failure;
    present key creates a standard-library FRED observations client, fetches
    observations sequentially with conservative throttling, maps normalized
    app-owned records, persists the last-good snapshot, and returns sanitized
    status. FMP adapter code remains present for rollback/historical
    compatibility but is no longer the active runtime refresh path.
  - FRED-backed records use `data_mode="provider_reference"`,
    `source_label="FRED macro snapshot"`, `forecast_label=None`, backend-owned
    `actual_label` / `previous_label` / `unit_label`, and
    `is_trading_signal=false`. Raw FRED payloads, raw URLs with keys, API keys,
    raw exception bodies, credentials, provider-private metadata, broker data,
    prompts, LLM traces, advice, urgency, and execution wording are not
    returned or persisted.
  - Tests added/updated for fake FRED success mapping, missing
    `FRED_API_KEY`, malformed/no-observation degradation, 429/throttled
    response sanitization, required FRED attribution, null forecasts, route
    refresh with fake transport, and existing synthetic fallback.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
    passed with `41 passed in 9.10s`; symbol compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `45 passed in 0.20s`; `git diff --check` passed.
- Blocker fix-up (2026-05-31, Codex C): FRED fetch, HTTPError, provider,
  and refresh/persist failure wrappers now raise sanitized
  `EconomicCalendarRefreshError` instances without retaining raw exception
  causes or contexts that could include `api_key=...`, raw provider URLs, or
  raw payload text. Added regressions for injected transport failures,
  FRED `HTTPError`/429 paths, provider-level wrapping, and route-level
  sanitized failure responses. Verification:
  `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
  passed with `45 passed in 9.03s`; symbol compatibility run
  `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
  passed with `45 passed in 0.13s`; `git diff --check` passed.
- Codex B review (2026-05-31): PASS. Confirmed backend-only FRED access,
  unchanged read schema, `data_mode="provider_reference"` mapping,
  `forecast_label=None`, required FRED notice in `limitations`, sanitized
  missing-key/failure responses, and no raw key/URL/payload leakage through
  response strings or exception chains. Default tests use injected fake
  clients/transports and make no live FRED calls. Verification:
  `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
  passed with `47 passed`; symbol compatibility run
  `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
  passed with `45 passed`; full backend run
  `cd backend && ./.venv/bin/python -m pytest -q` passed with
  `777 passed, 92 skipped, 1 deselected`; `git diff --check` passed.
- End-to-end backend smoke (2026-05-31, Codex C): started the local Docker
  stack without reading `.env`, then ran the backend FRED refresh runner inside
  the backend container so `FRED_API_KEY` was read only by runtime code and was
  never printed. Sanitized result: refresh returned `status="refreshed"`,
  `data_mode="provider_reference"`, `source_label="FRED macro snapshot"`, and
  `record_count=17`. `EconomicCalendarService().list_events(...)` then served
  provider-reference rows from the last-good snapshot with `item_count=17`,
  FRED attribution in `limitations`, `forecast_label=None`, backend display
  `actual_label` / `previous_label`, `event_time_label="Time TBD"`,
  `event_datetime_utc=None`, and `is_trading_signal=false` on wrapper/items.
  Required fake/injected suites were re-run after the smoke:
  `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
  passed with `47 passed in 0.16s`; symbol compatibility run
  `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
  passed with `45 passed in 0.19s`; `git diff --check` passed.
- Status: `done`.

### P24B-T1A - FRED Refresh Resilience And Partial Success

- Task id: `P24B-T1A`
- Title: FRED Refresh Resilience And Partial Success
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Make FRED-backed economic-awareness refresh resilient enough for
  the personal demo when individual configured FRED series throttle or fail,
  without weakening backend-only key handling, sanitized failures, attribution,
  or analysis-only language.
- Dependencies:
  - `P24B-T1` FRED provider/client path
  - Codex B local verification that direct FRED observations can succeed while
    a full registry refresh may hit a throttled series
- Expected files:
  - `backend/app/services/economic_calendar.py`
  - `backend/tests/services/test_economic_calendar.py`
  - `backend/tests/api/test_economic_calendar.py`
  - `docs/shared/implementation_plan.md`, verification notes only
- Implementation steps:
  1. Increase default FRED sequential request spacing while preserving injected
     sleep support so tests remain fast and deterministic.
  2. Add bounded retry/backoff for sanitized FRED throttling failures only.
  3. Allow `FredEconomicCalendarProvider` to return a provider-reference
     partial-success snapshot when at least one configured series maps to a
     valid normalized record and one or more other series fail.
  4. Add a safe partial-success limitation: "Some FRED macro series were
     unavailable during refresh."
  5. Preserve full failure behavior when all series fail or no valid records
     are produced so last-good snapshots remain protected.
- Acceptance criteria:
  - Retry behavior never exposes raw URLs, raw payloads, exception bodies, or
    API keys through response strings, exception strings, causes, or contexts.
  - Successful FRED snapshots keep `data_mode="provider_reference"`,
    `forecast_label=None`, FRED attribution, and `is_trading_signal=false`.
  - Partial-success snapshots expose only normalized successful records and a
    safe limitation; no failed series raw details are returned.
  - Default tests make no live FRED or external calls.
- Verification notes (2026-05-31, Codex C):
  - Increased FRED default pacing to 1.1 seconds between sequential runtime
    requests and added bounded retry/backoff for sanitized throttling failures
    only; tests keep fake/injected sleep so no real delay is required.
  - `FredEconomicCalendarProvider` now skips failed individual series and
    returns a provider-reference partial-success snapshot when at least one
    normalized record is valid, appending the safe limitation
    `Some FRED macro series were unavailable during refresh.` All-series-failed
    or zero-valid-record cases still raise sanitized refresh failure so
    last-good snapshots are preserved.
  - Tests added/updated for throttled-series retry success, permanent
    per-series failure plus other successful series, all-series failure,
    sanitized retry/exception metadata, route-level sanitized failure, and
    unchanged fake FRED success mapping. No live FRED calls were made.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
    passed with `47 passed in 0.23s`; symbol compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `45 passed in 0.17s`; `git diff --check` passed.
- Codex B review (2026-05-31): PASS. Confirmed default FRED pacing is more
  conservative, retry/backoff is bounded and limited to sanitized throttling
  failures, partial-success snapshots expose only normalized successful
  records plus the safe limitation, all-series/zero-valid-record failures
  still preserve last-good behavior, and no frontend/agent/streaming/provider
  scope was added. Verification:
  `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
  passed with `47 passed`; symbol compatibility run
  `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
  passed with `45 passed`; full backend run
  `cd backend && ./.venv/bin/python -m pytest -q` passed with
  `777 passed, 92 skipped, 1 deselected`; `git diff --check` passed.
- Status: `done`.

### P24B-T2 - Dashboard FRED Economic Awareness Consumption

- Task id: `P24B-T2`
- Title: Dashboard FRED Economic Awareness Consumption
- Owner: Claude A implementation, Claude B/Codex B review
- Objective: Adjust the existing Dashboard Economic Awareness panel to consume
  FRED-backed provider-reference responses clearly, without changing the
  frontend endpoint or adding frontend provider calls.
- Dependencies:
  - Codex B PASS on `P24B-T1`
  - existing `frontend/src/components/economic-calendar/EconomicCalendarPanel.tsx`
- Expected files:
  - `frontend/src/types/economicCalendar.ts`, only if `P24B-T1` adds fields
  - `frontend/src/components/economic-calendar/EconomicCalendarPanel.tsx`
  - `frontend/src/components/economic-calendar/EconomicCalendarRangePicker.tsx`,
    only if needed for UX polish
  - `docs/shared/implementation_plan.md`, verification notes only
- Implementation steps:
  1. Keep the frontend calling only `GET /api/economic-calendar/events` and the
     existing refresh endpoint if already reviewed; do not call FRED directly.
  2. Replace any FMP-specific copy with provider-neutral or FRED-aware copy when
     `source_label`/attribution indicate FRED.
  3. Display FRED attribution/disclaimer in a compact, readable way when
     FRED-backed data is shown.
  4. Keep no-forecast behavior honest: null forecast values display as
     unavailable, not missing UI.
  5. Preserve local-time AM/PM display, date selection, past-row styling, and
     "not a trading signal" copy.
  6. Do not add ticker/company news, market quotes, watchlists, charts,
     recommendations, urgency, or agent/news-tool integration.
- Acceptance criteria:
  - Synthetic, unavailable, and FRED provider-reference states are visually
    distinct and not misleading.
  - FRED-backed rows do not appear as forecasts, recommendations, or trading
    alerts.
  - No localStorage/sessionStorage writes, new endpoints, direct provider calls,
    frontend financial calculation, advice/execution wording, or Phase 21A
    changes.
- Verification:
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint -- --max-warnings 0`
  - `cd frontend && npm run build`
  - Browser smoke of synthetic/unavailable/FRED-shaped fixture states if
    possible without live provider calls.
- Rollback notes:
  - Revert only FRED-specific panel copy/type adjustments and verification
    notes; keep the existing Phase 24A panel if it remains contract-compatible.
- Verification notes (2026-05-31, Claude A — proposed, pending review):
  - Files changed: `frontend/src/components/economic-calendar/EconomicCalendarPanel.tsx`
    only. `frontend/src/types/economicCalendar.ts` was left unchanged — P24B-T1
    added no schema fields (FRED attribution and the partial-success notice ride
    in the existing `limitations: string[]`; `data_mode="provider_reference"`,
    `source_label`, `as_of_label`, `freshness_label` already exist). The API
    client (`economicCalendar.ts`), `EconomicCalendarRangePicker.tsx`, and
    `DashboardPage.tsx` were untouched.
  - Endpoint usage unchanged: the panel still calls only
    `GET /api/economic-calendar/events`; the pre-existing manual-refresh control
    (`POST /api/economic-calendar/refresh`, added in P24A-T9) is unchanged and
    no new refresh wiring was added. No FRED/FMP/provider call is made from
    React; browser smoke recorded zero external resource requests.
  - provider_reference rendering: added `isProviderReference`; when
    `data_mode === "provider_reference"` the header shows a neutral
    "FRED · official macro" (or "Official source") `info` badge instead of any
    demo/synthetic chip — "DEMO · NOT YET CONNECTED" never shows for
    provider-reference. The compact provenance row now also renders for
    provider-reference (data-mode badge + `source_label · freshness_label ·
    As of as_of_label`), so synthetic / official / unavailable are visually
    distinct.
  - Attribution + limitations: backend `limitations` are now rendered verbatim
    in a compact, muted list, surfacing the required FRED notice ("This product
    uses the FRED® API but is not endorsed or certified by the Federal Reserve
    Bank of St. Louis.") and the safe partial-success notice ("Some FRED macro
    series were unavailable during refresh.") — visible but not alarming (no
    red/urgent styling).
  - Table/content unchanged and contract-faithful: same US-macro columns (Date,
    Time, Impact, Event, Actual, Forecast, Previous; no currency/region column);
    Time shows browser-local AM/PM only when `event_datetime_utc` is present,
    else the backend `event_time_label` verbatim (e.g. "Time TBD");
    actual/forecast/previous rendered verbatim with null → "—" (FRED forecasts
    stay "—"); no parsing/compare/color-by-value; `event_has_occurred` null does
    not infer past styling.
  - Safety: "Economic awareness only · Not a trading signal." stays visible; no
    advice/recommendation/urgency/order/execution/safe-to-trade/ready-to-trade
    wording; no bullish/bearish/buy/sell; no implication of a real-time news
    feed or consensus forecast calendar; no localStorage/sessionStorage; no
    frontend financial computation; no Phase 21A change. Panel failures stay
    localized (error/retry within the panel).
  - Tests: `cd frontend && npm run typecheck` clean; `npm run lint --
    --max-warnings 0` clean; `npm run build` clean; `git diff --check` clean.
  - Browser smoke (Claude Preview) at 1024/1280/1440 in light + dark, no
    horizontal page overflow (table scrolls inside its container): verified the
    real synthetic fallback (synthetic badge + limitations), and — via an
    in-browser stubbed backend response (no provider call) — the FRED
    provider_reference state (FRED badge, no demo label, FRED attribution +
    partial-success visible, Time "Time TBD", Forecast "—") and the unavailable
    empty state (no FRED/synthetic badge, "Unavailable" provenance).
  - Dependency note: P24B-T1 / P24B-T1A are `in_progress (ready for Codex B
    review)` rather than PASS; this frontend slice consumes only the documented
    contract and a stubbed provider_reference fixture. Final live verification
    against a real FRED-refreshed backend is deferred until Codex B PASSes T1
    and a local refresh is available.
  - Deferred polish: a real-backend FRED smoke (after backend refresh) and any
    copy tuning Claude B/Codex B prefer on the official-source badge wording.
- Claude B frontend safety/design review (2026-05-31): PASS. Verified the only
  code file (`EconomicCalendarPanel.tsx`, 543 lines) against acceptance criteria:
  - States visually distinct & not misleading: `isDemo` (synthetic OR
    `demo_notice`) → mute "Synthetic data" badge; `isProviderReference`
    (`data_mode === "provider_reference"`, L196-197) → `info`
    "FRED · official macro" / "Official source" badge (`providerBadgeLabel`,
    keyed off `/fred/i.test(source_label)`); the two are mutually exclusive by
    `data_mode`, so a FRED snapshot never shows the synthetic/"not connected"
    chip (L219-236). Provenance row (data-mode badge + `source_label ·
    freshness_label · As of as_of_label`) renders for demo/provider_reference/
    unavailable alike (L334-343).
  - Attribution + limitations: backend `limitations[]` rendered verbatim in a
    compact muted list (L348-353, aria "Data notes and attribution") — surfaces
    the FRED notice and the partial-success line; not alarming.
  - Contract-faithful rows: Time = browser-local AM/PM via `formatLocalTime`
    only when `event_datetime_utc` present, else backend `event_time_label`
    verbatim with no fabricated conversion (L86-91, L379); actual/forecast/
    previous rendered verbatim with `?? "—"` (L398-400) so FRED's null forecast
    shows "—"; `occurred = event_has_occurred === true` (L371) so null/false
    never infers past styling; no parse/compare/color-by-value.
  - No new wiring: panel calls only `GET /economic-calendar/events`; the manual
    `POST /economic-calendar/refresh` is the pre-existing P24A-T9 control. Grep
    found no `fetch`/provider/`stlouisfed`/`api_key`/`localStorage`/
    `sessionStorage` and no advice/recommendation/urgency/order/execution/
    safe-to-trade/ready-to-trade/bullish/bearish/buy/sell wording in the panel;
    "Economic awareness only · Not a trading signal." stays visible (L258).
    `types/economicCalendar.ts` confirmed unchanged (no new backend fields).
  - No frontend financial computation; no Phase 21A change; panel failures stay
    localized (in-panel error/retry).
  - Dependency note (not a blocker): P24B-T1/T1A are `in_progress`, not yet
    Codex B PASS. This frontend slice correctly consumes the documented
    `provider_reference` contract; a real-backend FRED smoke after a live refresh
    remains deferred until Codex B PASSes T1. If T1's contract shifts during that
    review, the panel may need a touch-up — contingency only, no current frontend
    defect. Backend FRED contract safety remains Codex B's separate gate.
- Live verification addendum (2026-05-31, Claude A — resolves the deferred
  real-backend FRED smoke now that Codex B PASSed the Phase 24B backend):
  - No frontend code change was required; the existing panel already renders
    real `provider_reference` data correctly. Re-ran static checks clean:
    `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`,
    `git diff --check` (no diff).
  - Triggered a real backend FRED refresh via the manual backend-only path
    (token taken from the backend container env; no secret read/printed):
    `status="refreshed"`, `data_mode="provider_reference"`,
    `source_label="FRED macro snapshot"`, `record_count=17`,
    `message="Economic calendar refresh completed."`. No frontend FRED call.
  - Live browser smoke (Claude Preview, real backend snapshot, current-day
    default window) at 1024/1280/1440 in light + dark, no horizontal page
    overflow (wide table scrolls inside its own container):
    - 17 real FRED macro rows rendered (CPI, Core CPI, PCE, Core PCE, GDP, Real
      GDP growth, payrolls/unemployment, jobless claims, retail sales, durable
      goods, 2Y/10Y Treasury yields, 10Y-2Y spread, effective fed funds, fed
      funds target range upper/lower) with backend-owned importance badges.
    - Header showed the `info` "FRED · official macro" badge; NO "Synthetic
      data" badge and NO "DEMO · NOT YET CONNECTED" for provider_reference.
    - Provenance: "Provider reference" badge + `FRED macro snapshot · FRED
      provider reference · not a trading signal · As of FRED macro snapshot
      imported 2026-05-31T…` (as_of_label rendered verbatim).
    - FRED attribution shown verbatim ("This product uses the FRED® API but is
      not endorsed or certified by the Federal Reserve Bank of St. Louis.").
      No partial-success notice this run (all 17 series succeeded); the
      partial-data line remains wired for when the backend emits it.
    - Time column showed "Time TBD" for every row (`event_datetime_utc` null —
      no fabricated time); Forecast showed "—" for every row (`forecast_label`
      null); `actual_label`/`previous_label`/`unit_label` rendered verbatim
      (e.g. `332.407 (obs 2026-04-01)` / `330.293 (obs 2026-03-01)` / `index`);
      `event_has_occurred` null → no past-row styling inferred.
    - Network confirmed the frontend's only economic-calendar call was
      `GET /api/economic-calendar/events?start_date=…&end_date=…`; zero external
      resource requests; no `POST /refresh` issued from the browser.
  - Synthetic and unavailable branches are unchanged from the reviewed PASS and
    were previously verified; the live state is now real FRED provider_reference.
- Status: `done` (2026-05-31, Claude B frontend safety/design review PASS;
  frontend-only, contract-faithful. Live real-backend FRED `provider_reference`
  smoke completed 2026-05-31 after Codex B PASSed P24B-T1/T1A — the previously
  deferred item is now closed).

### P24B-T3 - FRED Observation-Date Mapping For Date-Range Filtering

- Task id: `P24B-T3`
- Title: FRED Observation-Date Mapping For Date-Range Filtering
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Fix FRED provider-reference records so Dashboard date-range
  filtering uses a real FRED date instead of the refresh/import date. FRED's
  free observations endpoint does not provide a forward-looking release
  calendar or exact publication timestamp, so the backend uses the latest
  observation reference date as the event date while keeping refresh/import
  time in snapshot provenance (`as_of_label` / `imported_at`).
- Context:
  - Claude A confirmed the reviewed frontend renders the backend contract
    faithfully: the panel sends `start_date` / `end_date` and displays returned
    rows. No frontend change is needed if existing `event_date_label` carries
    the backend-approved filter/group date.
  - Prior P24B FRED records were all stamped with the refresh date, which made
    only the current-date picker state show all records and every other date
    appear empty.
- Implementation steps:
  1. Change `_record_from_fred_observations(...)` so `event_date_label` and the
     opaque `event_reference` date input use the latest FRED observation
     reference date (`observation["date"]`), not `imported_at.date()`.
  2. Leave `as_of_label` / `imported_at` as the refresh/import provenance.
  3. Preserve `event_time_label="Time TBD"` and `event_datetime_utc=None`
     because the observations endpoint does not provide an exact event time.
  4. Add regression coverage proving refresh-date windows no longer include
     observation-dated FRED records, while observation-date windows do.
- Acceptance criteria:
  - No response field additions or frontend type changes are required.
  - FRED-backed rows remain `data_mode="provider_reference"`, source-labelled,
    attribution-labelled, `forecast_label=None`, and `is_trading_signal=false`.
  - Broad date-range queries can return records spread across FRED observation
    dates.
  - Backend-only FRED key handling, sanitized failures, partial-success
    behavior, and last-good snapshot behavior remain unchanged.
- Verification notes (2026-05-31, Codex C):
  - Implemented Option A fallback semantics: `event_date_label` is now the FRED
    observation reference date (for example `2026-04-01`) while
    `as_of_label="FRED macro snapshot imported ..."` remains the refresh
    provenance. No schema or frontend contract fields were added.
  - Added focused regression coverage for observation-date filtering. The test
    verifies a refresh-date window returns no record for a CPI observation dated
    `2026-04-01`, while the `2026-04-01` window returns the record.
  - Sanitized live backend smoke through the Docker backend runtime path (key
    read only by backend runtime, never printed): refresh returned
    `status="refreshed"`, `data_mode="provider_reference"`,
    `source_label="FRED macro snapshot"`, `record_count=17`. A broad
    `2026-01-01` → `2026-12-31` service read returned `item_count=17`; first
    rows included CPI/Core CPI/PCE/Core PCE dated `2026-04-01` and GDP dated
    `2026-01-01`, all with `event_time_label="Time TBD"`,
    `event_datetime_utc=None`, `forecast_label=None`, FRED attribution present,
    and `is_trading_signal=false`.
  - Verification: `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
    passed with `48 passed in 0.29s`; symbol compatibility run
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `45 passed in 0.19s`; `git diff --check` passed.
- Status: `in_progress` (ready for Codex B review).

### P24B-T4 - FRED Release-Date Calendar Mapping

- Task id: `P24B-T4`
- Title: FRED Release-Date Calendar Mapping
- Owner: Codex C implementation, Codex B architecture/safety review
- Objective: Replace the observation-date fallback from `P24B-T3` with true
  FRED release-calendar dates so the Dashboard date picker filters macro
  awareness rows by source-published release dates rather than refresh dates or
  economic observation reference dates.
- Context:
  - The prior observation endpoint integration used
    `/fred/series/observations`, which supports `observation_start` /
    `observation_end` style value windows but is value/observation-shaped, not
    release-calendar-shaped.
  - Codex C inspected and tested FRED calendar/metadata candidates before
    integration: `/fred/series/observations`, `/fred/series/release`,
    `/fred/releases/dates`, `/fred/release/dates`, and v2 release-observation
    behavior. The selected runtime path uses `/fred/release/dates` for each
    app-approved macro release id because it is release-calendar-shaped and
    avoids fetching the entire FRED release universe.
- Verification notes (2026-05-31, Codex C):
  - Added FRED release-calendar vocabulary and HTTP-client support for both
    `/fred/releases/dates` (global release-date probe/pagination support) and
    `/fred/release/dates` (runtime release-specific calendar fetches).
  - Runtime `POST /economic-calendar/refresh` now uses the release-specific
    endpoint for the approved macro release allowlist: CPI, Personal Income and
    Outlays, GDP, Employment Situation, weekly unemployment insurance claims,
    retail sales, and M3 manufacturer shipments/orders. Observation support
    remains in code for tested fallback/legacy coverage, but the Dashboard
    calendar source is now release dates.
  - FRED release-calendar records keep the existing frontend read schema:
    `event_date_label` is the FRED release date, `event_time_label="Time TBD"`,
    `event_datetime_utc=None`, `actual_label=None`, `forecast_label=None`, and
    `previous_label=None`. Refresh/import timing stays separate in
    `as_of_label` / `imported_at`; FRED attribution remains in `limitations`.
  - Added fake-client tests for release-calendar mapping, release-specific
    endpoint URL construction, global release-date pagination behavior,
    route-level FRED refresh with release-date rows, and preservation of
    sanitized failure behavior. Default tests make no live FRED or external
    calls.
  - Sanitized runtime smoke through the backend Docker container (key read only
    by backend runtime, never printed): refresh returned
    `data_mode="provider_reference"`, `source_label="FRED macro snapshot"`,
    `record_count=141`, `window_start="2026-01-01"`,
    `window_end="2026-12-31"`. The selected
    `2026-05-25` → `2026-06-05` read returned `selected_window_item_count=7`
    with release-date rows including Personal Income and Outlays, GDP,
    Employment Situation, weekly claims, and M3 survey rows. All sampled rows
    had `event_time_label="Time TBD"`, null actual/forecast values,
    `is_trading_signal=false`, and FRED attribution present.
  - Verification:
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q`
    passed with `52 passed in 0.36s`;
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py -q`
    passed with `45 passed in 0.20s`; `git diff --check` passed.
- Status: `in_progress` (ready for Codex B review).

## Phase 25A - Agentic Workflow Foundation

Status: `active by reviewed slice` — Codex A approved the foundation, and each
task still requires its own scoped implementation/review gate. Owner: Claude E
(agentic systems design/implementation), with Codex B architecture/safety review
and Claude B review for prompt/memory/persistence/provider-sensitive parts.

Phase goal: formalize and unify the app-owned, stage-based agentic spine that
already exists across `backend/app/services/agents/` (Phase 16B deterministic
orchestrator) and `backend/app/services/agent_team/` (Phase 19 mock-first LLM
team) into a single, auditable, deterministic-first review runner with an
app-owned run-state model, a reusable evaluation harness, and a tool-use
governance envelope. Design reference:
`docs/claude-e-agentic/AGENTIC_SYSTEM_DESIGN_MEMO.md`.

Hard boundaries for the whole phase (every task): mock provider default; no
live LLM/provider/tool calls; no external provider calls; no broker actions; no
raw private account data in prompts/tools/state/logs/persistence; no frontend
composer activation; no TradingAgents source copied and no TradingAgents
execution in the portfolio-aware path; deterministic backend services own all
financial metrics; agent commentary stays structurally separate from
deterministic evidence; the stateless `POST /agent-team/trade-review-analysis/
preview` route keeps unchanged external behavior.

Founder/PM decisions still open before T1 starts (see memo §15–§16): whether
MVP ships deterministic-only review first or includes mock LLM commentary;
whether to approve the role rename to review-oriented names as a separate
slice; confirmation that memory stays disabled; whether a bounded
public-evidence-only "considerations for/against" pass is desired; per-run
budget ceilings.

### P25A-T0 - Agentic workflow architecture contract and state/tool/eval design

- Task id: `P25A-T0`
- Title: Agentic workflow architecture contract and state/tool/eval design
- Owner: Claude E, with Codex B architecture/safety review and Codex A approval
- Objective: Define the unified state machine, state model, role model,
  tool-use governance, memory/reflection policy, evaluation/observability plan,
  latency/cost plan, error/partial-success behavior, and security/privacy
  boundaries before any agentic code changes.
- Dependencies:
  - completed Phase 16A/16B deterministic agent components and orchestrator
  - completed Phase 19A/19B/19C agent-team boundaries
  - paused Phase 21A contract/ADR 0007 reviewed as reference
- Files expected to change:
  - `docs/claude-e-agentic/AGENTIC_SYSTEM_DESIGN_MEMO.md`
  - `docs/codex-b-architecture/adr/0008-agentic-orchestration-spine.md`
  - `docs/shared/implementation_plan.md` (this Phase 25A section)
  - minimal routing notes in `docs/shared/current_roadmap.md`,
    `docs/shared/TASKS.md`, `docs/shared/CHANGELOG.md`
- Acceptance criteria:
  - design memo covers state/role/tool/memory/eval/latency/error/security
    sections and a starting-architecture recommendation;
  - reconciliation of the two existing orchestrators is described;
  - the role-taxonomy reconciliation is flagged as a separate reviewed slice;
  - ADR 0008 records the layered-hybrid decision, the reversibility
    classification, engine staging, provider/MCP/tool/parallelism/role-rename/
    memory stances, alternatives, consequences, and block conditions;
  - no implementation is authorized by this task.
- Tests: none (design task).
- Rollback notes: docs-only; revert the memo, ADR 0008, and this section if
  rejected.
- Status: `proposed` / `not_started` (memo revised and ADR 0008 drafted per
  Codex B architecture adjudication; awaiting Codex A go-ahead before P25A-T1
  coding).

### P25A-T1 - App-owned agent review run-state model and mock workflow runner

- Task id: `P25A-T1`
- Title: App-owned agent review run-state model and mock workflow runner
- Owner: Claude E, with Codex B architecture/safety review
- Objective: Add an immutable, validated `AgentReviewRunState` (generalizing
  `AgentTeamAnalysisState`) and a thin deterministic review runner that wraps
  the existing mock orchestrator, adds per-stage timing/budget accounting and
  an early-exit-on-blocked-actionability gate, and returns a persistence-ready
  but not-persisted typed record.
- Dependencies:
  - accepted `P25A-T0`
  - explicit Codex A go-ahead on the first coding slice
- Files expected to change:
  - new `backend/app/services/agent_team/run_state.py`
  - new `backend/app/services/agent_team/review_runner.py`
  - new `backend/tests/services/agent_team/test_run_state.py`
  - new `backend/tests/services/agent_team/test_review_runner.py`
  - touch (additive) `backend/app/services/agent_team/__init__.py`
- Implementation steps:
  - Add `AgentReviewRunState` with per-stage status/timing/budget and an
    `eval_flags` placeholder; run recursive forbidden-field / secret /
    prohibited-phrase / generated-metric validation in `__post_init__`.
  - Add a runner that reuses the existing role loop and mock provider, records
    timing and token/cost budget usage, and short-circuits LLM roles when the
    actionability status is blocked/unknown (deterministic-only review).
  - Structure the role-dispatch boundary as an **async-ready seam** (roles stay
    pure and side-effect-free, dispatched through one function) but execute
    **sequentially** against the mock provider; do not add real concurrency.
  - Keep the existing stateless preview route behavior unchanged.
- Scope constraints (explicit, per ADR 0008):
  - **async-ready dispatch seam only — no real parallel execution**;
  - **no role rename** (keep the Phase 19 role names);
  - **no persistence / no migration**;
  - **no route behavior change** (the stateless preview route is untouched);
  - **no frontend change / no composer activation**;
  - **no live provider calls** (mock provider default);
  - **no MCP, no tool execution, no TradingAgents execution/source copy**.
- Acceptance criteria:
  - mock provider remains default; no live calls; no persistence; no route
    behavior change; no frontend changes; no real parallel execution; no role
    rename;
  - the dispatch seam is async-ready but runs sequentially against mock;
  - separate broker snapshot freshness and market quote freshness survive in
    state; deterministic evidence survives all role/provider failures;
  - blocked actionability skips LLM roles and yields a safe deterministic-only
    run; run resolves to `completed | partially_completed | failed_safe`;
  - recursive privacy/wording/metric validation passes on every state instance.
- Tests:
  - `cd backend && pytest tests/services/agent_team/test_run_state.py tests/services/agent_team/test_review_runner.py`
  - extend `tests/services/agent_team/test_agent_team_scenarios.py` coverage for
    flows × actionability states × provider-failure modes.
- Rollback notes: additive new modules; delete new files and revert the
  `__init__.py` export to roll back. No data/migration impact.
- Status: `in_progress` (implemented; ready for Codex B architecture/safety review).
- Verification notes (2026-06-02, Claude E):
  - Files changed: NEW `backend/app/services/agent_team/run_state.py`
    (`AgentReviewRunState` + `AgentReviewStageStatus`/`AgentReviewRoleOutput`/
    `AgentReviewEvalFlag`/`AgentReviewBudgetSummary`/`AgentReviewTimingSummary`,
    all frozen and validated on construction); NEW
    `backend/app/services/agent_team/review_runner.py` (`ReviewRunner` +
    async-ready sequential `dispatch_roles_sequentially` seam); NEW tests
    `test_run_state.py`, `test_review_runner.py`; additive exports in
    `backend/app/services/agent_team/__init__.py`.
  - `AgentReviewRunState` generalizes `AgentTeamAnalysisState` (does not replace
    it): adds per-stage timing, a budget summary (recorded, not enforced), a
    timing summary, and `eval_flags` (process-level scaffolding; full
    faithfulness harness deferred to P25A-T2). Validates via
    `validate_llm_provider_output` on construction; nested structures validate
    via `validate_agent_team_text` / `validate_llm_provider_output`.
  - Blocked-actionability early exit: when `review_actionability_status`
    starts with `blocked_` (covers `blocked_stale_broker_snapshot`,
    `blocked_stale_market_quote`, `blocked_unknown_freshness`,
    `blocked_provider_error`), the runner skips all LLM role calls and returns a
    deterministic-only safe run (`run_status="completed"`, empty `role_outputs`,
    role stages `gated`, `safety_flags` includes
    `deterministic_only_blocked_actionability`). Non-blocked statuses
    (`analysis_only`, `manual_confirmation_required`, `normal_review`) run the
    mock commentary roles as before.
  - Async-ready seam runs sequentially: public-evidence roles are dispatched as
    one independent batch (future fan-out point), portfolio-aware roles one at a
    time and ordered; results aggregate by stable role key (`AGENT_TEAM_ROLES`
    order). `max_parallelism=1`, `dispatch_mode="sequential"`; no asyncio, no
    threads, no semaphore.
  - Safety confirmations: mock provider default; no live/external/broker calls;
    no persistence/migration; existing stateless preview route and
    `AgentTeamOrchestrator` unchanged (regression test asserts unchanged
    behavior); no frontend/composer change; no LangGraph/MCP/OpenAI Agents
    SDK/TradingAgents; no role rename (Phase 19 names preserved); no real
    parallel execution; recursive privacy/wording/invented-metric validation on
    every state, role output, and eval flag; no raw private data in
    state/tests.
  - Tests run (`cd backend && ./.venv/bin/python -m pytest`):
    `tests/services/agent_team/test_run_state.py
    tests/services/agent_team/test_review_runner.py
    tests/services/agent_team/test_agent_team_scenarios.py` → 36 passed;
    `tests/services/agents/ tests/services/trade_review/test_trade_review_snapshots.py`
    → 56 passed; full `tests/services/agent_team/` → 129 passed.
    `git diff --check` clean.
  - Open/deferred: budget enforcement, real parallel fan-out, the reusable
    `agent_eval` harness (P25A-T2), the tool-governance envelope (P25A-T3), and
    persistence (P25A-T4) remain out of scope here.

### P25A-T2 - Reusable agent evaluation harness

- Task id: `P25A-T2`
- Title: Reusable agent evaluation harness
- Owner: Claude E, with Codex B and Claude B review
- Objective: Generalize the existing safety validators into a reusable
  `agent_eval` harness used by both tests and the runtime `evaluate_run` stage:
  evidence faithfulness, forbidden wording, invented-metric detection,
  role-boundary, prompt privacy, deterministic-evidence consistency, and
  failure classification.
- Dependencies:
  - `P25A-T1`
- Files expected to change:
  - new `backend/app/services/agent_eval/` (faithfulness, boundaries, wording,
    privacy, `__init__.py`)
  - new `backend/tests/services/agent_eval/` test suite
  - touch (additive) `review_runner` to populate `eval_flags`
- Acceptance criteria:
  - faithfulness check flags any LLM-introduced figure not traceable to the
    deterministic projection;
  - role-boundary check proves public roles never receive private/agent-safe
    evidence;
  - prompt-privacy check runs recursive forbidden-key/secret/value scans;
  - harness is import-safe, network-free, and synthetic-fixture-driven;
  - `eval_flags` are recorded on the run and contain no private values.
- Tests: `cd backend && pytest tests/services/agent_eval`.
- Rollback notes: additive; delete the new package and revert the `eval_flags`
  population to roll back.
- Status: `in_progress` (implemented; ready for Codex B/Claude B review).
- Verification notes (2026-06-02, Claude E):
  - Files changed: NEW `backend/app/services/agent_eval/` (`results.py`,
    `checks.py`, `harness.py`, `__init__.py`); NEW
    `backend/tests/services/agent_eval/test_agent_eval.py`; wired into
    `review_runner._evaluate_run` (now delegates to the harness, replacing the
    T1 inline scaffolding).
  - Checks implemented: `forbidden_wording`, `evidence_faithfulness`
    (ungrounded-figure / invented-metric detection on generated text),
    `prompt_privacy_keys`, `prompt_privacy_values` (private value tokens +
    secret-like patterns), composite `generated_output_safety`, `role_boundary`
    (public roles never received agent-safe evidence), `evidence_consistency`
    (run summary matches projection), and `failure_classification`. All reuse
    existing detectors (`find_prohibited_llm_phrases`,
    `GENERATED_METRIC_PATTERNS`, `find_forbidden_keys`,
    `find_forbidden_string_values`, `find_secret_like_values`).
  - Harness is import-safe, network-free, synthetic-driven, and decoupled from
    the run-state types (operates on primitives). `EvalFinding` detail strings
    are fixed safe constants that never echo offending content; findings pass
    `validate_agent_team_text` and are safe inside
    `AgentReviewRunState.eval_flags`.
  - Import-cycle note: `review_runner` imports the harness lazily inside
    `_evaluate_run` (agent_eval imports agent_team safety submodules and
    agent_team/__init__ imports the runner); import smoke confirmed in both
    orders and via `app.main`.
  - Safety: no LLM/live/provider/network calls; no raw prompts/private values in
    outputs/tests; runtime `eval_flags` now `passed` for mock runs
    (faithfulness no longer `deferred`).
  - Tests run: `tests/services/agent_eval` plus the agent_team suite — see the
    aggregate result in the P25A-T3 notes.
- Status confirmation: deterministic evidence and agent commentary remain
  structurally separate; no role rename; no persistence; no route/frontend
  change.

### P25A-T3 - Tool-use governance and safe tool result envelopes

- Task id: `P25A-T3`
- Title: Tool-use governance and safe tool result envelopes
- Owner: Claude E, with Codex B architecture/safety review
- Objective: Define the governed tool registry (per-role allowlist, evidence
  tier, input/output schema, mode, timeout, retry, budget) and the safe
  `ToolResult` envelope and audit-record shapes — schema-only, with no live
  tools and no LLM-invoked tool calls.
- Dependencies:
  - `P25A-T1`
- Files expected to change:
  - new `backend/app/services/agent_team/tools.py`
  - new `backend/tests/services/agent_team/test_tools.py`
- Acceptance criteria:
  - `ToolResult` and audit records pass recursive privacy/wording/metric
    validation;
  - evidence tiers (public / agent-safe / private-forbidden) are enforced by
    role allowlist;
  - no live provider/tool call exists; mode defaults to synchronous + mock;
  - failure/timeout/budget behavior degrades to role-unavailable + partial run.
- Tests: `cd backend && pytest tests/services/agent_team/test_tools.py`.
- Rollback notes: additive schema-only module; delete to roll back.
- Status: `in_progress` (implemented; ready for Codex B/Claude B review).
- Verification notes (2026-06-02, Claude E):
  - Files changed: NEW `backend/app/services/agent_team/tools.py`; NEW
    `backend/tests/services/agent_team/test_tools.py`. Schema-only — no tool
    execution, no MCP, no external/provider/broker/market-data/news/LLM calls.
  - Defines `EvidenceTier` (`public` / `agent_safe` / `private_forbidden`),
    `ToolMode` (`mock`/`sync` only), `ToolStatus`, `ToolDataMode`,
    `ToolRegistryEntry` (role allowlist, tier, timeout/retry/budget metadata),
    `ToolResult` envelope, and `ToolAuditRecord` (status/latency/cost only — no
    inputs/outputs/payload fields), plus registry/degraded-state helpers.
  - Private tier is prohibited: constructing a registry entry or result at
    `private_forbidden` raises (`assert_tool_tier_allowed`). `agent_safe` tools
    may only be allowlisted to portfolio-aware roles; public roles cannot be
    wired to non-public tools. `ToolResult`/`ToolRegistryEntry`/`ToolAuditRecord`
    validate against the privacy/wording/invented-metric boundary. Failure/
    timeout/blocked/budget states degrade to safe empty-payload results
    conceptually (no execution).
  - Tests run (`cd backend && ./.venv/bin/python -m pytest`):
    `tests/services/agent_eval tests/services/agent_team/test_tools.py
    tests/services/agent_team/test_run_state.py
    tests/services/agent_team/test_review_runner.py` → 70 passed; full
    `tests/services/agent_team/ tests/services/agent_eval` → 174 passed;
    regression `tests/services/agents/ tests/services/trade_review/` → 128
    passed. Import smoke (agent_eval-first, agent_team-first, `app.main`) clean.
    `git diff --check` clean.
  - Out of scope (unchanged): no live tool wiring, no MCP runtime, no
    persistence, no routes, no frontend, no role rename, no real parallelism, no
    TradingAgents.
- Blocker fix (2026-06-02, Claude E, Codex B review): `ToolRegistryEntry`
  enforced the role/tier rule but `ToolResult`, `ToolAuditRecord`, and the
  degraded-result builders did not, so a public role could construct an
  `agent_safe` result/audit record. Added shared validators
  `assert_role_tier_allowed(evidence_tier, role_name)` (private prohibited for
  all shapes; `agent_safe` only for portfolio-aware roles; `public` for any
  known role) and `assert_role_data_mode_allowed(role_name, data_mode)` (public
  roles may not carry `agent_safe` data). Applied in `ToolResult.__post_init__`,
  `ToolAuditRecord.__post_init__`, and `_degraded_result(...)` (covering
  `blocked`/`unavailable`/`timeout`/`budget_exceeded` and
  `tool_result_for_disallowed_role`). `ToolRegistryEntry` behavior unchanged. No
  tool execution or runtime wiring added.
  - Added tests: `ToolResult`/`ToolAuditRecord`/degraded helpers reject
    `agent_safe` for public roles; `agent_safe` still works for portfolio-aware
    roles; `public` works for public and portfolio-aware roles; `agent_safe`
    `data_mode` rejected for public roles; private tier rejected across result,
    audit, and degraded paths.
  - Tests run (`cd backend && ./.venv/bin/python -m pytest`):
    `tests/services/agent_team/test_tools.py tests/services/agent_eval
    tests/services/agent_team/test_run_state.py
    tests/services/agent_team/test_review_runner.py` → 80 passed; full
    `tests/services/agent_team/ tests/services/agent_eval` → 184 passed.
    `git diff --check` clean. Left `in_progress` for Codex B re-review.

### P25A-T4 - Persistence / reload boundary (only if needed)

- Task id: `P25A-T4`
- Title: Persistence / reload boundary (only if needed)
- Owner: Claude E, with Codex B architecture/safety review and Claude B privacy
  review
- Objective: If and only if a persisted run/reload need is approved (e.g.
  Phase 21A reactivation), map `AgentReviewRunState` onto existing
  `agent_runs`/`agent_steps` primitives and add safe write/read paths. Stop with
  a mapping memo before any migration.
- Dependencies:
  - `P25A-T1` through `P25A-T3`
  - explicit Codex A reactivation of a persisted-run need
- Acceptance criteria:
  - existing primitives are explicitly mapped before any new table/migration;
  - only safe snapshots are persisted (no raw prompts/payloads/private values);
  - the stateless preview route remains unchanged.
- Tests: persistence/contract tests with synthetic fixtures.
- Rollback notes: deferred by default; no change unless reactivated.
- Status: `proposed` / `not_started` (deferred — do not begin unless a persisted
  need is explicitly approved).

### P25A-T5 - Codex B architecture and safety review

- Task id: `P25A-T5`
- Title: Codex B architecture and safety review
- Owner: Codex B, with Claude B for prompt/memory/persistence/provider parts
- Objective: Review the Phase 25A run-state, runner, eval harness, and tool
  governance for boundary correctness, privacy, deterministic/commentary
  separation, partial-success clarity, and no advice/execution/guarantee
  leakage.
- Dependencies:
  - `P25A-T1` through `P25A-T3` (and `P25A-T4` if reactivated)
- Acceptance criteria:
  - PASS/BLOCKED with cited files/lines and precise fixes;
  - confirms mock default, no live calls, no route behavior change, no composer
    activation, no TradingAgents source copy.
- Status: `ready_for_review` (P25A-T1 implemented and previously reviewed;
  P25A-T2 and P25A-T3 implemented and ready for Codex B architecture/safety
  review, with Claude B for the eval/privacy-sensitive parts. P25A-T4 remains
  deferred/not_started.)

### P25A-T6 - Claude A frontend handoff (after backend review only)

- Task id: `P25A-T6`
- Title: Claude A frontend handoff (after backend review only)
- Owner: Claude A, with Codex B contract review
- Objective: Provide a reviewed read-only contract so the Agent Console can
  display run state and `eval_flags`-derived safety badges. This task does not
  by itself enable the disabled follow-up composer.
- Dependencies:
  - `P25A-T5` PASS
- Acceptance criteria:
  - frontend consumes opaque references and safe read fields only;
  - composer stays disabled until a separate reviewed activation slice exists;
  - deterministic evidence and agent commentary remain visually separate.
- Status: `proposed` / `not_started`.

### P25A-T7 - LLM provider key setup and controlled Gemini live-smoke path

- Task id: `P25A-T7`
- Title: LLM provider key setup and controlled Gemini live-smoke path
- Owner: Claude E, with Codex B architecture/safety review
- Objective: Make real-provider testing possible without complicating local
  setup — backend-only keys in `.env.example`, a concise live-smoke doc, and an
  opt-in Gemini smoke test that exercises the Phase 25A runner through the normal
  safety/eval path. Mock remains default.
- Files changed:
  - `.env.example` (added backend-only `GOOGLE_API_KEY` + backend-only
    `OPENAI_API_KEY`; the OpenAI provider was implemented in P25A-T8 — paid,
    opt-in, never default, mock remains default; internal `POA_LLM_*` knobs
    intentionally omitted)
  - new `docs/claude-e-agentic/LLM_PROVIDER_SMOKE_TEST.md`
  - new `backend/tests/services/agent_team/test_gemini_live_smoke.py`
- Gating: the live test is marked `external`/`slow` (excluded by `pytest.ini`
  `addopts -m "not external and not slow"`) AND `skipif` unless
  `POA_LLM_LIVE_TESTS=1` with `GOOGLE_API_KEY` present. It uses synthetic
  workspace data, resolves the live Google provider via the ADR-0005 gate, runs
  `ReviewRunner`, and asserts a safe run state, live (non-mock) output, present
  `eval_flags`, no forbidden private keys/values, and separate freshness scopes.
  It never logs the key.
- Boundaries: no frontend, routes, persistence, DB, composer, MCP, LangGraph,
  OpenAI Agents SDK, or TradingAgents. No live call in the default suite.
- OpenAI: implemented backend-only in P25A-T8 as an `OpenAILLMProvider` behind the
  existing `LLMProvider` Protocol/factory (plain SDK, no OpenAI Agents SDK) — paid
  API usage, opt-in only, never default (mock remains default). The OpenAI live
  smoke (P25A-T9) requires explicit paid-use acknowledgement and founder approval.
- Acceptance criteria:
  - default suite stays fully offline/mock and passes without keys;
  - live test only runs when explicitly opted in;
  - `.env.example` requires only provider keys for live use.
- Status: `done` (Codex B PASS). Default-suite tests pass offline with no keys;
  the live Gemini smoke test is excluded by default and runs only when opted in.
- Verification notes (2026-06-02, Codex B PASS): `.env.example` exposes only the
  backend-only provider keys (Gemini implemented; OpenAI implemented in P25A-T8 —
  paid, opt-in, never default) with
  `POA_LLM_*` knobs kept out of normal setup; the Gemini live smoke is
  triple-gated (external/slow marker exclusion + `POA_LLM_LIVE_TESTS` opt-in +
  `GOOGLE_API_KEY` presence), uses synthetic data, runs through the safety/eval
  path, and never logs the key. No app code, routes, persistence, frontend,
  composer, MCP, LangGraph, OpenAI Agents SDK, or TradingAgents changes.

### P25A-T8 - OpenAI provider adapter (backend-only, behind the LLMProvider protocol)

- Task id: `P25A-T8`
- Title: OpenAI provider adapter behind the app-owned `LLMProvider` protocol
- Owner: Claude E, with Codex B architecture/safety review
- Objective: Add a backend-only OpenAI provider option behind the existing
  provider Protocol/factory so live OpenAI testing is possible — mock stays
  default, OpenAI is never default, and the OpenAI Agents SDK is not used.
- Files changed:
  - new `backend/app/services/agent_team/openai_provider.py`
    (`OpenAILLMProvider`, `OpenAIChatClient` Protocol, lazy plain-SDK client,
    safe error mapping)
  - `backend/app/services/agent_team/provider_config.py` (provider name
    `openai`, `openai_credential_available`, `DEFAULT_OPENAI_MODEL`, live-mode
    validation, public snapshot, `OPENAI_API_KEY` load)
  - `backend/app/services/agent_team/provider_factory.py` (resolve `openai` only
    when explicitly configured + `OPENAI_API_KEY` present)
  - `backend/app/services/agent_team/__init__.py` (additive export)
  - new `backend/tests/services/agent_team/test_openai_provider.py`;
    extended `test_provider_config.py` / `test_provider_factory.py`
- Safety: lazy SDK import (no eager load; mock mode never imports `openai`);
  injected client Protocol for tests; missing key/config resolves to a safe
  `provider_auth_error`; provider exceptions map to safe statuses by class name
  only (no raw body); output flows through `LLMProviderResponse`/output safety;
  unsafe output degrades to `safety_validation_failed`. No frontend
  provider/model selection. No OpenAI Agents SDK.
- Acceptance criteria:
  - mock remains default; google works when explicitly configured; openai works
    only when explicitly configured with a backend key;
  - no live OpenAI call in default tests; default suite passes without keys;
  - no raw exception/payload/URL/key leakage.
- Tests run (`cd backend && ./.venv/bin/python -m pytest`):
  `tests/services/agent_team/ tests/services/agent_eval` → 206 passed,
  1 deselected; `tests/services/agents/ tests/services/trade_review/` → 128
  passed. App import smoke clean; `openai` SDK not eagerly loaded.
  `git diff --check` clean. No live OpenAI call executed.
- Status: `done` (Codex B PASS). OpenAI provider adapter accepted behind the
  app-owned `LLMProvider` protocol; mock stays default, OpenAI is never default,
  no OpenAI Agents SDK. Live OpenAI smoke remains paid and gated behind explicit
  founder approval.
- Verification notes (2026-06-02, Codex B PASS): lazy plain-SDK client (no eager
  import), injected client Protocol for tests, missing key/config → safe
  `provider_auth_error`, SDK exceptions mapped to safe statuses by class name
  only (no raw body/payload/URL/key), output through
  `LLMProviderResponse`/output safety with unsafe output degrading to
  `safety_validation_failed`. Default suite passes offline with no keys.

### P25A-T9 - Provider live-smoke completion (Gemini run note + gated OpenAI smoke)

- Task id: `P25A-T9`
- Title: Provider live-smoke completion — Gemini run note and gated OpenAI smoke
- Owner: Claude E, with Codex B architecture/safety review
- Objective: Make Gemini the routine manual provider smoke (free-tier friendly,
  rate-limit-safe) and add an opt-in, paid-usage-gated OpenAI live smoke test
  that mirrors the Gemini one without being run by default or without approval.
- Files changed:
  - new `backend/tests/services/agent_team/test_openai_live_smoke.py`
  - `docs/claude-e-agentic/LLM_PROVIDER_SMOKE_TEST.md` (Gemini vs OpenAI smoke,
    separate keys/commands, rate-limit and paid-usage notes)
- Gemini smoke: free-tier/Flash friendly; `rate_limited`/`quota_exceeded`/
  `provider_unavailable` are treated as safe non-blocking provider failures
  (deterministic evidence survives, no secret/raw provider data leaks).
- OpenAI smoke: **paid API usage**; gated behind BOTH `POA_LLM_LIVE_TESTS=1` and a
  dedicated `POA_LLM_OPENAI_LIVE=1` acknowledgement plus `OPENAI_API_KEY`, on top
  of the `external`/`slow` marker exclusion. Model configurable via
  `POA_LLM_MODEL` (falls back to the adapter default `gpt-4o-mini`); the founder
  may set e.g. `POA_LLM_MODEL=gpt-5-nano`.
- Gemini live smoke run (2026-06-02): founder ran the command; result =
  `safely_failed` (safe-degradation path), 1 passed in 0.02s. It did NOT reach a
  real Gemini response because (a) the command used the literal placeholder
  `<your Gemini key>` rather than a real key, and (b) the `google-generativeai`
  SDK is not installed in the venv (`import google.generativeai` raises
  ImportError), so every role degraded to a safe `provider_unavailable` and the
  run resolved partial — exactly the resilient behavior the test asserts. A real
  provider response is still pending: it requires installing the live provider
  SDKs via the `live-llm` extra (`./.venv/bin/pip install ".[live-llm]"`) plus a
  real `GOOGLE_API_KEY` (exported in the founder's shell; agents did not read or
  source `.env`). No secret was read or printed.
- Gemini live smoke run #2 — REAL provider call (2026-06-02): founder installed
  the `live-llm` extra (`pip install ".[live-llm]"` built the backend wheel and
  installed core + provider SDKs cleanly — end-to-end validation of the pyproject
  packaging) and ran with a real `GOOGLE_API_KEY` exported in the shell. Result =
  **PASSED, 1 passed in 2.84s** (vs the earlier 0.02s safe-degradation run),
  confirming a real live Gemini response flowed through `ReviewRunner` →
  output-safety → `agent_eval` with no forbidden private keys/values, `eval_flags`
  present, and separate broker/market freshness scopes. No secret was read or
  printed by any agent. The ~2.84s round-trip plus the SDK deprecation warning
  firing confirm real calls were made (the test asserts the safe terminal path,
  not that every role returned `ok`). **Gemini live smoke = DONE.**
- Known follow-up (SDK deprecation): the run emitted a `FutureWarning` that
  `google.generativeai` is end-of-life and Google recommends the `google-genai`
  package (`google.genai`). `google_provider.py` currently imports
  `google.generativeai`. Tracked as proposed `P25A-T12`; the path works on the
  deprecated SDK until migrated. No code changed here.
- OpenAI live smoke run — REAL paid provider call (2026-06-02, founder-approved
  via "Verify OpenAI API"): founder exported `OPENAI_API_KEY` and ran with both
  opt-in gates (`POA_LLM_LIVE_TESTS=1 POA_LLM_OPENAI_LIVE=1`). Result = **PASSED,
  1 passed in 28.82s** on the default `gpt-4o-mini`. The ~28.8s wall time (5
  sequential provider calls, ~5.8s each) confirms real OpenAI responses flowed
  through `ReviewRunner` → output-safety → `agent_eval` with no forbidden private
  keys/values, `eval_flags` present, and separate broker/market freshness scopes.
  No secret was read or printed by any agent; cost was a fraction of a cent (5
  calls, ≤800 output tokens each). **OpenAI live smoke = DONE.** Both live
  providers (Gemini + OpenAI) are now validated end-to-end behind the safety/eval
  boundary; mock remains default; no frontend/route/persistence/composer change.
- Latency observation (real data): the live multi-persona run is dominated by
  **sequential** provider calls (~5.8s/call for OpenAI; ~0.6s/call for Gemini
  Flash). This is the expected behavior of the P25A-T1 sequential dispatch seam
  and is concrete evidence for the planned future **parallel fan-out** of the
  independent public-evidence roles (async-ready seam, aggregate by stable role
  key) once a real-LLM commentary slice is built. No change now.
- Packaging / dependency management (2026-06-02): migrated the backend to the
  industry-standard PEP 621 `backend/pyproject.toml` (setuptools build backend,
  matching the TradingAgents approach) as the single source of truth. Core deps
  in `[project].dependencies`; test/dev tooling in the `dev` extra; live LLM
  provider SDKs (`google-generativeai`, `openai`) in the optional `live-llm`
  extra (kept out of core so the base install and default offline/mock suite
  stay lean; adapters import SDKs lazily). Removed `backend/requirements.txt` and
  the interim `backend/requirements-llm.txt`; updated `backend/Dockerfile`
  and `backend/README.md`. Install variants: `pip install .`,
  `pip install -e ".[dev]"`, `pip install ".[live-llm]"`. This crossed into the
  devops/build lane and was verified by Codex D.
- Codex D build/lock verification (2026-06-02): selected `uv` for backend
  reproducibility and added `backend/uv.lock`. Updated `backend/Dockerfile` to
  install pinned `uv==0.11.18`, export locked core runtime deps with
  `uv --quiet export --frozen --no-dev --no-emit-project`, install those deps
  into the image, then install the backend package with
  `pip install --no-cache-dir --no-deps .` so dependency resolution stays locked
  while the PEP 517 package build still runs. `docker compose build backend`
  passed; the build reached `Successfully built portfolio-options-agent-backend`
  under build isolation. `docker compose up -d postgres backend` with a
  temporary Codex D override (`POA_LLM_MODE=mock`,
  `SYMBOL_DIRECTORY_REFRESH_ON_STARTUP=false`) passed; logs showed Alembic
  PostgreSQL context, Uvicorn startup, and application startup complete. The
  backend container returned `{"status":"ok"}` from `GET /health` internally.
  Optional live-provider SDKs were confirmed absent from the image
  (`google.generativeai=false`, `openai=false`). Host-side curl to
  `127.0.0.1:8000` failed from the local sandbox despite Compose showing the
  port published, so the runtime proof is container-internal health plus Compose
  status/logs. Default test configuration remains in `backend/pytest.ini`.
- OpenAI live smoke: NOT executed (paid; awaits explicit founder approval).
- Status: `done` (Codex B PASS / close-out 2026-06-02). Packaging migration
  verified by Codex D (uv.lock + Dockerfile); both live smokes passed (Gemini
  2.84s, OpenAI 28.82s) through the safety/eval path with no leakage; docs cleanup
  re-reviewed and the "sourced from .env" wording corrected to "exported in the
  founder's shell." Mock remains default; no route/persistence/frontend/composer
  change. (Follow-up `P25A-T12` tracks the `google-genai` SDK migration.)

### P25A-T10 - Agent persona naming, expert-team positioning, and role-expansion analysis

- Task id: `P25A-T10`
- Title: Agent persona naming / expert-team positioning / role roadmap (analysis)
- Owner: Claude E, with Codex A (product/positioning) and Codex B (architecture)
- Objective: Decide the user-facing specialist personas, how the 12 TradingAgents
  roles map onto a read-only, portfolio-aware, no-advice product, which concepts
  stay internal/deterministic, and the role roadmap — analysis/docs only.
- Inputs / decisions already made (Codex A): clean UI labels with no "Agent"
  (Fundamentals Analyst, News Analyst, Technical Analyst, Risk Manager, Portfolio
  Manager); backend keys may stay unchanged; "specialist review team"
  positioning that stays decision-support, not advice; the no-advice guardrail
  and forbidden product phrases; the conditional "Portfolio Manager" label.
- Files changed:
  - new `docs/claude-e-agentic/AGENT_PERSONA_ROLE_ANALYSIS.md` (full analysis)
  - `docs/shared/implementation_plan.md` (this entry)
- Outcome (analysis):
  - Five MVP personas are sufficient for private alpha (3 public evidence +
    Risk Manager + Portfolio Manager). Note: 3 public personas run on mock/unwired
    evidence today; Risk Manager + Portfolio Manager carry the real value.
  - TradingAgents mapping: adopt News/Fundamentals/Portfolio-Manager-as-synthesis;
    merge Market→Technical and Sentiment→News; Bull/Bear → future "Considerations
    For/Against" sections; Aggressive/Neutral/Conservative → future "Risk Lens"
    sections; reject Trader (→ deterministic Trade Review) and all debate/
    conviction personas; Research Manager is internal-only.
  - Top P1 user-facing add: Options Strategist / Options Risk Specialist (the
    options wedge). Macro/Income/Sentiment are P2 or merge; Tax is deferred
    (compliance-sensitive); Liquidity/Concentration merges into Risk Manager;
    Data-Quality and Compliance stay internal (deterministic + eval), not personas.
  - Debate roles: deferred; only ever as structured non-conviction sections, never
    separate personas. Trader: rejected as persona. "Portfolio Manager" label:
    keep now with mandatory guardrail copy; pre-approved fallbacks "Portfolio
    Lead" / "Portfolio Synthesis" if testing shows fiduciary confusion.
- Recommended doc updates (routed, not edited here): Codex A PRD / MVP_SCOPE /
  POSITIONING; `docs/shared/AI_TEAM.md` Educational Financial Language Rules
  (forbidden product phrases + persona-label policy); Codex B ARCHITECTURE_HANDOFF
  note or ADR 0009 for the persona/display-label read contract; Claude D review of
  the Portfolio-Manager label/copy. Claude E to refresh memo §6 role model.
- Acceptance criteria: analysis covers current 5, TradingAgents mapping,
  additional roles, debate roles, Trader, Portfolio-Manager label, and a role
  roadmap; no code/behavior change; no backend key change.
- Tests: none (analysis/docs only).
- Status: `done` (analysis; Codex A persona/positioning decisions encoded).

### P25A-T11 - Agent Console display-label slice

- Task id: `P25A-T11`
- Title: Agent Console clean persona display labels
- Owner: Claude A (frontend), with Codex B read-contract review and Claude D copy review
- Objective: Show clean persona titles (no "Agent") in the Agent Console, with
  mandatory guardrail copy for the Portfolio Manager persona. Backend keys
  unchanged.
- Approach: add a backend-owned `display_name` to the Agent Console read contract
  (Codex B reviews the field) OR map machine `role_name` → label in the frontend;
  Claude A renders labels + the Portfolio-Manager guardrail tooltip/subtitle.
- Boundaries: no behavior change; composer stays disabled; analysis-only; no
  backend role-key rename; no execution/advice/guarantee wording.
- Codex A product sign-off (2026-06-02):
  - Approved display labels: Fundamentals Analyst, News Analyst, Technical
    Analyst, Risk Manager, Portfolio Manager.
  - Approved required Portfolio Manager guardrail copy: "Synthesizes the team's
    analysis for your review - does not manage your portfolio or recommend
    trades."
  - Approved fallbacks if user testing or compliance review finds fiduciary
    confusion: Portfolio Lead, then Portfolio Synthesis / Review Synthesizer.
    Avoid Portfolio Strategist.
  - MVP/private-alpha role roadmap remains the five approved personas. P1
    candidate is Options Strategist / Options Risk Specialist; Trader and debate
    roles remain rejected as user-facing personas.
  - Product docs updated: `docs/codex-a-product/POSITIONING.md`,
    `docs/codex-a-product/PRD.md`, `docs/codex-a-product/MVP_SCOPE.md`, and
    `docs/shared/AI_TEAM.md`.
- Codex B contract decision (2026-06-02): backend-owned display labels (not
  frontend mapping). Accepted read-schema fields:
  `AgentTeamRoleOutputRead.display_name: str` and
  `AgentTeamStageRead.display_name: str | None`. No `specialty` field yet.
  Recorded as accepted ADR 0009.
- Backend display-label contract (Claude E, 2026-06-02): implemented.
  - Files changed: `backend/app/services/agent_team/roles.py` (registry
    `display_name`: "Risk Management Agent" → "Risk Manager"; "Portfolio Manager
    Agent" → "Portfolio Manager"; the three analyst labels were already clean);
    `backend/app/schemas/agent_team.py` (added `display_name` to
    `AgentTeamRoleOutputRead` and `AgentTeamStageRead`);
    `backend/app/services/agent_team/frontend_read.py` (populate `display_name`
    verbatim from the role registry; stage `display_name` null when `role_name`
    is null); new accepted
    `docs/codex-b-architecture/adr/0009-agent-persona-display-labels.md`;
    `backend/tests/api/test_agent_team_analysis_console.py` (display-label tests).
  - Machine `role_name` keys preserved exactly; per-persona evidence tiers
    unchanged; no behavior change; mock default; composer disabled; no
    routes/persistence/live calls.
  - Tests: display labels present + registry-matched on role_outputs and
    role-bound stages; stage `display_name` null when `role_name` null; no label
    contains "Agent"; no forbidden/advice wording or private fields introduced.
    Ran `tests/api/test_agent_team_analysis_console.py tests/services/agent_team/
    tests/services/agent_eval` → 211 passed, 2 deselected;
    `tests/services/agents/ tests/services/trade_review/` → 128 passed;
    `git diff --check` clean.
- Codex B review (2026-06-02): PASS. ADR 0009 accepted. Backend display-label
  contract is complete. The frontend rendering of `display_name` and the
  Portfolio Manager guardrail tooltip remains Claude A's slice.
- Status: `done`.

### P25A-T12 - Migrate Gemini adapter to the `google-genai` SDK (proposed)

- Task id: `P25A-T12`
- Title: Migrate the Gemini provider adapter off the deprecated `google.generativeai` SDK
- Owner: Claude E, with Codex B review and Codex D dependency awareness
- Trigger: the real Gemini live smoke (P25A-T9) emitted a `FutureWarning` that
  `google.generativeai` is end-of-life; Google recommends `google-genai`
  (`google.genai`).
- Objective: migrate `backend/app/services/agent_team/google_provider.py`'s lazy
  client from `google.generativeai` to the `google-genai` client
  (`from google import genai`), swap the `live-llm` extra in `pyproject.toml`
  (`google-generativeai` → `google-genai`) and refresh `uv.lock`, keeping the
  app-owned `LLMProvider` Protocol, lazy import, injected-client tests, and safe
  error mapping unchanged.
- Boundaries: mock stays default; no live call in default tests; no behavior
  change beyond the SDK swap; injected fake client keeps the default suite
  offline; no routes/persistence/frontend/composer/TradingAgents changes.
- Acceptance criteria: default suite passes offline with no keys; mocked adapter
  tests updated to the new client surface; an opt-in live Gemini smoke passes on
  the new SDK with no deprecation warning; `git diff --check` clean.
- Priority: low (works on the deprecated SDK today) but worth doing before the
  package is removed upstream.
- Status: `proposed` / `not_started`.

## Phase 26A - Market Context: Market Mood

Purpose: add a safe, internal-demo Market Context surface based on
CNN-derived Fear & Greed data. Market Mood is broad sentiment context only. It
must not become advice, market timing, a screener, a trade-review actionability
input, a deterministic risk-rule input, or an LLM/agent input by default.

Architecture source of truth:

- `docs/codex-b-architecture/PHASE_26A_MARKET_MOOD_CONTRACT.md`

Surface split:

- Dashboard card: compact overall score/rating only.
- Detail page: overall index, 7 component indicators, 1-year trend, component
  bars, explanations, and source/freshness caveats.

Core boundaries: backend fetch/cache only; no frontend-direct provider calls; no
CNN logo/branding; no `live`/`real_time` claims; source is internal-demo pending
source/rights review; no actionability/risk-rule/LLM-agent use; no
advice/recommendation/buy/sell/risk-on/risk-off/urgency/execution wording.

### P26A-T0 - Market Mood architecture contract

- Task id: `P26A-T0`
- Title: Market Mood architecture contract and boundaries
- Owner: Codex B
- Objective: define source caveats, backend contract, cache/fallback policy,
  frontend display boundaries, and source/rights review requirement.
- Files:
  - `docs/codex-b-architecture/PHASE_26A_MARKET_MOOD_CONTRACT.md`
  - `docs/shared/implementation_plan.md`
- Status: `done`.

### P26A-T1 - Market Mood backend contract, adapter, cache, and tests

- Task id: `P26A-T1`
- Title: Market Mood backend contract, adapter, cache, and tests
- Owner: Codex C, with Codex B architecture/safety review
- Objective: implement the provider-neutral Market Mood backend contract,
  CNN-derived internal-demo adapter boundary, normalized cache, last-good
  fallback, stale/unavailable states, and synthetic/offline tests.
- Files changed:
  - `backend/app/schemas/market_mood.py`
  - `backend/app/services/market_mood.py`
  - `backend/app/api/routes/market_context.py`
  - `backend/app/main.py`
  - `backend/tests/services/test_market_mood.py`
  - `backend/tests/api/test_market_context.py`
- Result:
  - `GET /market-context/market-mood` returns a safe display contract for the
    dashboard and detail page.
  - `POST /market-context/market-mood/refresh` is explicit/manual, sanitized, and
    unconfigured by default.
  - Cache persists normalized app-owned JSON only at
    `backend/cache/market_mood_snapshot.json`.
  - Invariant flags remain false: `is_trading_signal`,
    `is_actionability_input`, `is_risk_rule_input`.
  - No startup fetch, frontend work, provider live call, actionability/risk-rule
    integration, LLM/agent ingestion, CNN branding, or advice/execution wording.
- Verification:
  - `tests/services/test_market_mood.py tests/api/test_market_context.py` -> 13 passed.
  - `tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py` -> 52 passed.
  - `tests/services/test_symbol_lookup.py tests/services/test_symbol_directory.py tests/api/test_symbols.py` -> 45 passed.
  - `git diff --check` clean.
- Codex B review (2026-06-03): PASS. Claude A may consume this contract for
  P26A-T2. Deferred polish: add one cache-restore robustness test for
  structurally valid but semantically invalid normalized cache content.
- Status: `done`.

### P26A-T2 - Dashboard Market Mood compact card

- Task id: `P26A-T2`
- Title: Dashboard Market Mood compact card
- Owner: Claude A, with Codex B / Claude B frontend safety review
- Dependency: P26A-T1 reviewed and passed.
- Objective: add a compact dashboard Market Mood card that consumes only the
  reviewed backend contract and displays the overall score/rating as broad market
  context.
- Display requirements:
  - title: Market Mood;
  - overall score/rating, 0-100 band/gauge/bar, updated label, stale/unavailable
    state;
  - required copy visible: "Broad market sentiment context only. Not a trading
    signal.";
  - source caveat visible: "Source: CNN-derived Fear & Greed data. Not
    affiliated with CNN. Latest available snapshot. Internal demo only pending
    source/rights review.";
  - Portfolio Copilot visual language only; no CNN branding or cloned CNN design.
- Boundaries:
  - no frontend-direct provider call;
  - no refresh trigger unless separately reviewed;
  - no component charts on the dashboard card;
  - no actionability/risk-rule integration;
  - no LLM/agent ingestion;
  - no advice/recommendation/market-timing wording.
- Status: `not_started`.

### P26A-T3 - Market Mood detail page

- Task id: `P26A-T3`
- Title: Market Mood detail page with indicator explanations and interactive graphs
- Owner: Claude A, with Codex B / Claude B frontend safety review
- Dependency: P26A-T1 reviewed and passed; P26A-T2 may proceed independently if
  the shared API client exists.
- Objective: add a separate Market Mood / Market Context page that displays the
  full backend-provided Market Mood contract in an exploratory, source-labelled,
  non-advisory interface.
- Display requirements:
  - overall score/rating and 1-year trend graph;
  - all 7 component summary bars;
  - explanation text for each indicator, owned by frontend copy/design review or
    backend display contract if later required;
  - optional 1w/1m/1y comparison labels from the backend;
  - stale/unavailable/source-rights caveats always visible;
  - responsive and dark-mode verified.
- Boundaries:
  - no component-level historical charts unless backend contract later supplies
    safe component history;
  - no alerts/notifications;
  - no strategy interpretation;
  - no "risk-on/risk-off" wording;
  - no agent commentary or LLM ingestion;
  - no advice/execution/trade-timing language.
- Status: `not_started`.

### P26A-T4 - Market Mood source-rights and production readiness review

- Task id: `P26A-T4`
- Title: Market Mood source-rights and production readiness review
- Owner: Codex B with Codex A/founder review
- Dependency: internal-demo implementation exists.
- Objective: decide whether the CNN-derived source can remain in the product
  beyond internal demo, whether a replacement licensed source is needed, and what
  public/user-facing wording is allowed.
- Review focus:
  - source terms and redistribution/display rights;
  - stability risk of internal/private endpoint;
  - attribution and non-affiliation wording;
  - whether source should be disabled or replaced before public beta.
- Status: `not_started`.

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
