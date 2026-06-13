# Implementation Plan

Active coordination index for Portfolio Copilot. Keep this file short: current
work, next handoff, review gates, and status only. Historical task detail belongs
in the archives listed below.

## Source Of Truth

- Current product direction: `docs/shared/current_roadmap.md`
- Agent workflow rules: `docs/shared/agent_workflows.md`
- Report format: `docs/shared/AGENT_REPORT_FORMAT.md`
- Completed phase history: `docs/shared/completed_phases_log.md`
- Archived active-plan snapshots:
  - `docs/shared/implementation_plan_archive_2026-06-03.md`
  - `docs/shared/implementation_plan_archive_2026-06-12.md`

## Standing Rules

- Backend contracts own finance calculations, display labels, freshness,
  provenance, privacy boundaries, and actionability policy.
- Frontend renders reviewed backend fields and may add presentation-only
  formatting.
- LLM/Agent Team evidence may use only separately approved sanitized
  projections.
- Do not expose raw holdings, raw positions, quantities, cash balances, buying
  power, account values, account/provider/broker IDs, raw provider payloads,
  prompts, provider traces, LLM traces, secrets, or local DB contents in
  frontend or agent contracts.
- No automatic trading, broker actions, broker scraping, MFA bypass, advice
  wording, guaranteed-return wording, or safe/ready-to-trade wording.
- Use CodeGraph first when available; avoid broad read loops and large archived
  docs unless the task explicitly needs historical context.

## Owners

- Codex A: product / PM approval.
- Codex B: architecture, privacy, safety, contract review.
- Codex C: backend implementation, except agentic workflow.
- Claude A: frontend implementation.
- Claude B: frontend/privacy/safety review.
- Claude E: agentic AI system design and implementation.
- Codex F: frontend UI backup / visual implementation support.
- Codex D: DevOps, build, deployment, CI/CD.

## Current Status

### Phase 27B - Account Details Stability And Broker Snapshot Semantics

Status: implementation complete through P27B-T22; archived.

Reference docs:

- `docs/codex-b-architecture/PHASE_27A_ACCOUNT_DETAILS_SELECTED_ACCOUNT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`

Delivered:

- Latest-sync membership and current/expired/closed option semantics.
- Account Details v1 broker-readiness overview plus selected-account detail.
- Opaque account refs and selected-account sync bridge.
- Display-only cash/buying-power/collateral policy.
- Enriched selected-account labels, option unit fixes, optional tax-lot display
  contract, purchase-history hiding when lots are absent, and frontend visual
  polish.
- Agent Team evidence boundary remains lossy and excludes account refs, labels,
  cash values, holdings, option rows, tax lots, provider IDs, and raw payloads.
- Frontend follow-up polish: collapsed sidebar controls no longer clip, Account
  Details selected-account refresh preserves the current scroll/detail context,
  and Market Mood has a Data Sources sidebar shortcut.

Review state:

- Codex B contract/privacy reviews: PASS through P27B-T22.
- Claude B visual/safety smoke for Account Details: PASS after full-stack preview
  dev-token fix.
- Remaining caveat: DB-backed destructive tests are skipped unless a disposable
  safe test DB is explicitly enabled.

## Next Recommended Work

### Phase 26A Follow-Up - Market Mood Source-Update Detection

Status: complete through P26A-T12; ready to archive on the next docs pass.

Goal:

- Keep Market Mood honest when a page refresh triggers a backend refresh:
  `updated_at_label` remains provider/source update time, while backend refresh
  attempts and unchanged-source states are represented separately.

Reference doc:

- `docs/codex-b-architecture/PHASE_26A_MARKET_MOOD_CONTRACT.md`

Tasks:

- `P26A-T11` - Backend source-change detection and refresh-status metadata.
  - Owner: Codex C.
  - Reviewer: Codex B.
  - Scope: detect source changes from provider `updated_at_utc` or normalized
    snapshot equivalence; preserve last-good snapshot; optionally expose safe
    `last_checked_at_utc` / `last_checked_at_label` style metadata; no raw
    provider payloads, URLs, headers, cookies, provider IDs, exception bodies,
    prompts, traces, broker/account data, or secrets.
  - Acceptance: unchanged provider source does not imply a new source update;
    refresh failures preserve last-good; source update time and backend checked
    time are separate; tests use fake/injected provider responses only.
  - Verification 2026-06-12 by Codex C: implemented backend refresh result
    metadata with `status="refreshed" | "unchanged" | "failed"`,
    `source_changed`, `last_checked_at_utc`, and `last_checked_at_label`;
    `updated_at_utc` remains provider/source update time. Refresh compares
    provider `updated_at_utc` plus normalized snapshot equivalence, preserves
    and reuses last-good snapshots on unchanged checks, and records sanitized
    failed checks without replacing last-good data. Files changed:
    `backend/app/services/market_mood.py`,
    `backend/app/schemas/market_mood.py`,
    `backend/app/api/routes/market_context.py`,
    `backend/tests/services/test_market_mood.py`,
    `backend/tests/api/test_market_context.py`. Tests:
    `cd backend && ./.venv/bin/python -m pytest tests/services/test_market_mood.py tests/api/test_market_context.py -q`
    -> 30 passed. Codex B review 2026-06-12: PASS. Source update time and
    backend checked time remain separate, last-good snapshot preservation is
    intact, default tests are fake/offline, and no raw provider payloads or
    provider-private metadata are exposed.
- `P26A-T12` - Frontend Market Mood backend-state auto-update.
  - Owner: Codex F.
  - Dependency: P26A-T11 reviewed and passed.
  - Reviewer: Codex B for contract/safety; Claude B for visual review if UI copy
    or status display changes.
  - Scope: on Market Mood page mount/page refresh, use backend refresh/status and
    detail reads only; optionally poll backend state with tab-visibility pause;
    update page from backend detail only; preserve honest provider timestamp
    display; no frontend CNN/provider calls.
  - Acceptance: `updated_at_label` is never treated as page-refresh time;
    backend checked/status metadata, if shown, is compact and clearly separate;
    no `live`/`real-time`, advice, recommendation, buy/sell, risk-on/risk-off,
    order, execution, safe-to-trade, or ready-to-trade wording.
  - Verification 2026-06-12 by Codex B: PASS. Frontend calls only backend
    Market Mood endpoints, refreshes/reads backend state on mount, polls backend
    on a visibility-aware interval, keeps provider `updated_at_label` distinct
    from backend `Checked` metadata, and adds no frontend provider call,
    storage write, advice/execution wording, or CNN branding.

### Phase 27C - Trade Review And Agent Team Scope Integration

Status: P27C-T1 done (Codex B PASS); P27C-T2/T3/T4 not started.

Goal:

- Use the stabilized Account Details scope/account model to make Trade Review,
  saved reports, and Agent Team readouts state scope clearly and consistently.

Reference doc:

- `docs/codex-b-architecture/PHASE_27C_TRADE_REVIEW_AGENT_SCOPE_INTEGRATION_CONTRACT.md`

Recommended first task:

- `P27C-T1` - Trade Review review-account selector frontend wiring: done; Codex B PASS 2026-06-12.
  - Owner: Claude A. Reviewer: Codex B (contract/privacy/safety) PASS.
  - Files: `frontend/src/types/tradeReview.ts` (added `ReviewAccountSelectionMode`,
    `ReviewAccountSelectionRequest`, `review_account_selection` on the portfolio
    request, `ReportScopeMetadataRead`, `scope_metadata` on `TradeReviewWorkspaceRead`,
    reusing the existing `ReviewAccountRead`/`PortfolioScopeRead` mirrors via a
    type-only import), `frontend/src/components/trade-review/TradeReviewForm.tsx`
    (Account Details fetch + `Review account` selector separate from the relabeled
    `Broader portfolio context`), `frontend/src/components/trade-review/TradeReviewResults.tsx`
    (`ScopeMetadataPanel`), `frontend/src/api/tradeReviews.ts` + `frontend/src/api/client.ts`
    (forward the existing `X-User-Id` route header), `frontend/src/pages/TradeReviewPage.tsx`
    (pass `selectedUser?.id`).
  - Consumes the existing reviewed backend contract only; no new backend route,
    field, migration, provider call, or storage write. Submits only the opaque
    `account_reference`; renders backend display labels only (no `*_reference`,
    broker/provider IDs, balances, holdings, quantities, payloads, prompts, or
    traces); no frontend financial math; no advice/order/execution/safe-to-trade
    wording.
  - Verified: `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`,
    `git diff --check` clean. Full-stack smoke (`docker compose up -d postgres backend
    frontend`): `/health` 200; backend `/users` and proxy `/api/users` return the dev
    user; a portfolio-preview with a selected review account resolves `scope_metadata`
    to display labels (e.g. review account label + kind) through the Vite proxy with
    the `X-User-Id` header; `unselected` returns `review_account: null` and
    `account_level_feasibility_evaluated: false`.
  - Deferred (non-blocking): forward the user id on the Agent Team analysis-preview
    path for review-account parity (fold into P27C-T3); add an aria-live announcement
    for the account-list loading→ready/error transition.

Follow-up candidates:

- `P27C-T2` - Report scope metadata display and history filtering.
- `P27C-T3` - Agent Team scope banner and caveat rendering from sanitized
  evidence only.
- `P27C-T4` - Account group/scope management product decision.

## Paused Or Deferred

- Phase 21A realtime Agent Console: paused; composer remains disabled.
- Market-data provider selection: parked until production/display licensing
  planning.
- Market Mood production/public display: blocked on source/rights review.
- Economic Awareness frontend expansion: paused unless PM reactivates.
- Full tax-lot/history reconstruction from transactions: deferred; do not infer
  tax lots from activity/order data without a new reviewed contract.

## Handoff Format

Every implementation/review handoff should use one fenced `text` block, not a
`markdown` block, and should avoid nested triple backticks. Follow
`docs/shared/AGENT_REPORT_FORMAT.md`.
