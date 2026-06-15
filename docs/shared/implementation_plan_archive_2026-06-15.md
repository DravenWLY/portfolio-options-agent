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

Status: complete / archived for the scoped Phase 27C integration. P27C-T1,
P27C-T2, P27C-T3, P27C-T5, P27C-T6, and P27C-T7 are done. P27C-T4 account
group/scope management is deferred to a future product decision.

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

- `P27C-T2` - Reports scope metadata display and history-scope honesty: done;
  Codex B contract/privacy/safety re-review PASS and Claude B visual re-review
  PASS 2026-06-13.
  - Reports consume only saved `scope_metadata: ReportScopeMetadataRead | null`
    from each report thread. Null scope renders honest unavailable copy.
  - Reports do not infer saved scope from `account_id`, the current account
    selector, route state, cached Account Details, or mutable portfolio context;
    the old hidden selected-account report filtering and `account-scoped` /
    `user-scoped` copy were removed.
  - Verified: `npm run typecheck`, `npm run lint -- --max-warnings 0`,
    `npm run build`, `git diff --check`, and full-stack `/reports` route smoke
    with no console errors or horizontal overflow at 1024/1280.
- `P27C-T5` - Reports saved scope metadata backend contract: done; Codex B
  PASS 2026-06-13.
  - Backend report list/detail/create read contracts now include
    `scope_metadata: ReportScopeMetadataRead | null`; current legacy/unknown
    report rows return explicit `null` rather than reconstructing scope from
    `account_id`, route params, current Account Details, selector state, or
    mutable context.
  - No report storage migration was added in this slice; immutable saved-scope
    persistence remains a future generation-path follow-up before newly
    generated reports can return non-null scope.
- `P27C-T6` - Report detail saved-scope display: done; Codex B re-review PASS
  2026-06-13.
  - The opened report detail view consumes
    `GET /users/{uid}/reports/{thread_id}` and renders only
    `ReportThreadDetailRead.scope_metadata`; null detail scope shows
    "Scope metadata unavailable for this report."
  - Detail rendering is gated to the selected report id so stale detail responses
    cannot display another report's saved scope under the current header.
  - Browser smoke was intentionally not run to avoid inspecting private saved
    report content; verified with frontend typecheck/lint/build and
    `git diff --check`.
- `P27C-T3` - Agent Team scope banner and caveat rendering from sanitized
  evidence only: done; Codex B contract/privacy/safety PASS and Claude B visual
  re-review PASS 2026-06-12 (implemented under user task label P27C-T4).
  - Frontend adds a compact Agent Console `Review scope` banner consuming only
    the reviewed lossy `scope_summary` fields: scope modes, selected-context
    presence, included/excluded counts, review-account presence,
    account-level-feasibility evaluated flag, and sanitized scope caveat codes.
  - No account labels/refs, broker/provider IDs, balances, holdings, quantities,
    tax lots, raw payloads, prompts, traces, provider calls, storage writes,
    frontend financial math, or advice/order/execution/safe-to-trade wording.
  - Responsive fix: the banner stacks at the existing Agent Console breakpoint
    and passed 1024/1280 browser overflow smoke.
- `P27C-T7` - Scope model acceptance audit and archive blocker fix: done;
  Codex B narrow re-review PASS 2026-06-13.
  - Removed the remaining visible `context_reference` row from the Trade Review
    Portfolio Context disclosure. Trade Review results now preserve safe context
    display while avoiding visible `account_reference`, `scope_reference`,
    `context_reference`, broker/provider IDs, balances, holdings, quantities,
    payloads, prompts, or traces.
  - Verified by Codex F: frontend typecheck, lint, build, and `git diff --check`
    passed.
- `P27C-T4` - Account group/scope management product decision.

### Phase 28A - Saved Review Artifact Foundation

Status: foundation complete. Backend contract, persistence, frontend save
action, migration metadata fixes, and full-stack save-flow smoke are complete.
The saved artifact currently preserves a deterministic/source snapshot; Agent
Team report generation is intentionally deferred to Phase 29A.

Goal:

- Make each completed Trade Review / Agent Team analysis saveable as a durable
  historical review artifact with immutable generation-time scope, caveats,
  freshness, deterministic summary, and optional sanitized Agent Team output.

Reference doc:

- `docs/codex-b-architecture/PHASE_28A_SAVED_REVIEW_ARTIFACT_CONTRACT.md`

Completed backend tasks:

- `P28A-T1` - Backend saved review artifact contract.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: define the backend schema and endpoint for creating saved review
    artifacts from reviewed Trade Review / Agent Team outputs. The artifact must
    persist immutable `ReportScopeMetadataRead` and generation-time review
    summary data rather than reconstructing from current account state.
  - Acceptance: saved reports never infer scope from current account selector,
    current Account Details, mutable portfolio context, route state, or cached
    frontend state; no raw provider/account IDs, account numbers, raw payloads,
    raw holdings, raw positions, quantities, tax lots, raw balances, buying
    power, prompts, traces, transactions, orders, advice, or execution wording.
  - Verification 2026-06-13 by Codex C: added backend schema contract in
    `backend/app/schemas/reports.py` for `SavedReviewArtifactCreateRequest`,
    `SavedReviewArtifactRead`, deterministic summary, optional Agent Team
    summary, and saved report metadata that omits legacy raw `account_id`.
    Blocker fix: aligned saved-artifact prohibited wording with Trade Review
    policy (`you should`, `I recommend`, recommend buying/selling, guaranteed,
    safe/ready-to-trade) plus execution phrases, and hardened saved source/report
    references against broker/provider/account/private-data hint tokens while
    preserving valid `trrev_`, `workspace_`, `agentrun_`, and `svrev_`
    references. Persistence/route implementation is tracked in P28A-T2 below.
    Tests:
    `cd backend && ./.venv/bin/python -m pytest tests/unit/test_report_agent_schemas.py tests/api/test_reports.py -q`
    -> 20 passed, 4 skipped by safe DB guard;
    `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py tests/services/agent_team/test_evidence_projection.py -q`
    -> 113 passed, 14 skipped. Codex B PASS 2026-06-13; P28A-T1 done.

- `P28A-T2` - Backend persistence and projection for saved artifacts.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: add the minimal backend storage/projection slice so a reviewed
    Trade Review payload can be persisted as an immutable saved artifact.
  - Verification 2026-06-13 by Codex C: added nullable
    `report_threads.saved_artifact_json` storage and migration revision
    `0020_saved_review_artifacts`; added
    `POST /users/{uid}/reports/from-trade-review` using
    `SavedReviewArtifactCreateRequest`; report list/detail now project
    `scope_metadata` only from saved artifact JSON and legacy/unknown rows keep
    explicit `scope_metadata: null`. Codex B blocker fix: added server-owned
    `saved_review_sources` materialization/resolution so the save endpoint
    builds artifacts from a current-user reviewed source row, ignores
    client-supplied scope/summary fields during save, and returns 404 for
    nonexistent, wrong-user, unreviewed, or incomplete sources. Narrow
    re-review blocker fix: the resolver now validates stored source
    `scope_metadata_json`, `deterministic_summary_json`, and optional
    `agent_summary_json` against approved read schemas before any report thread
    is committed, so malformed stored source JSON fails closed. Persistence
    order blocker fix: the save path now validates the full
    `SavedReviewArtifactRead` candidate before `db.add()` / `db.commit()`,
    including `review_pipeline_label`, `limitations_json`, and
    `caveat_codes_json`; unsafe source metadata such as advice wording,
    `raw_payload`, or private provider/account hints returns 404 with no report
    thread committed. The saved artifact stores generation-time
    caveats/freshness/summary labels and does not reconstruct from Account
    Details, selector state, route state, or mutable portfolio context. Tests:
    `cd backend && ./.venv/bin/python -m pytest tests/unit/test_report_agent_schemas.py tests/api/test_reports.py -q`
    -> 27 passed, 12 skipped by safe DB guard;
    `cd backend && ./.venv/bin/python -m pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py tests/services/agent_team/test_evidence_projection.py -q`
    -> 113 passed, 14 skipped. Final Codex B PASS 2026-06-13; P28A-T2
    done.

Completed frontend/save-flow tasks:

- `P28A-T3` - Frontend "Save review snapshot" action.
  - Owner: Claude A or Codex F. Reviewers: Codex B for contract/privacy/safety;
    visual reviewer only if the UI surface is non-trivial.
  - Scope: add a compact save action on completed Trade Review results that
    calls `POST /users/{uid}/reports/from-trade-review` using the reviewed
    backend contract. The frontend must send only approved create-request fields
    and must not copy scope metadata, deterministic summaries, Agent Team output,
    Account Details data, or current selector state into the request.
  - Acceptance: saved review state is driven by the backend response; success
    links or guides to Reports without implying a trading recommendation; failure
    is quiet and retryable; no raw refs/IDs/private data are displayed beyond
    already-reviewed opaque source references when required by the contract.
  - BLOCKED (Claude A 2026-06-13; Codex B independent review verified): no valid
    `source_reference` is available to the frontend. `TradeReviewWorkspaceRead`
    exposes only `review_reference` (a `trv_`/intent value) which fails the
    `^(trrev|workspace|agentrun)_` saved-source regex, and
    `record_saved_review_source` has no production caller, so no resolvable
    `saved_review_sources` row exists — the save endpoint would 404 end-to-end.
    Per task instruction, no frontend reference was invented from
    `review_reference`, route state, account id, selector, or cache. Backend
    (Codex C) must first add an opaque `saved_review_source_reference` to
    `TradeReviewWorkspaceRead` (+ frontend type mirror), populated only for
    completed save-eligible reviews, and materialize the matching
    `saved_review_sources` row; then Codex B re-review, then unblock this task.
  - Backend unblock 2026-06-13 by Codex C: added
    `TradeReviewWorkspaceRead.saved_review_source_reference: str | None` with
    opaque `trrev_...` validation; synthetic/stateless previews keep `null`,
    while the authenticated portfolio-preview route materializes a
    server-owned `saved_review_sources` row from backend-built workspace output
    and returns its reference. The save endpoint can resolve that reference via
    `POST /users/{uid}/reports/from-trade-review`; client-supplied scope/summary
    remains ignored. Tests:
    `cd backend && ./.venv/bin/python -m pytest tests/unit/test_report_agent_schemas.py tests/api/test_reports.py tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py -q`
    -> 132 passed, 26 skipped by safe DB guard. Codex B PASS 2026-06-13;
    frontend save action is unblocked.
  - Frontend implemented 2026-06-13 by Claude A; Codex B contract/privacy/safety
    review PASS. Added a compact `SaveReviewSnapshot` action on completed Trade
    Review results, shown only when backend `saved_review_source_reference` is
    non-null and a user-id route context exists. The request sends only
    `source_kind`, `source_reference` (verbatim backend value, never displayed or
    invented), `title`, and `report_type`; it sends no scope_metadata,
    deterministic_summary, agent_summary, Account Details, selector state, cached
    state, or raw account/provider/broker/holdings data. Success is quiet/
    report-like with a link to Reports; failure is non-alarming and retryable; no
    advice/order/execution wording. Files: `frontend/src/types/tradeReview.ts`,
    `frontend/src/types/api.ts`, `frontend/src/api/reports.ts`,
    `frontend/src/components/trade-review/SaveReviewSnapshot.tsx` (new),
    `frontend/src/components/trade-review/TradeReviewResults.tsx`,
    `frontend/src/pages/TradeReviewPage.tsx`. Verified: `npm run typecheck`,
    `npm run lint -- --max-warnings 0`, `npm run build`, `git diff --check` clean.
    Data-backed browser smoke was initially blocked by migration metadata;
    P28A-T3A fixed alembic revision `0020_saved_review_artifacts`
    `down_revision` to `0019_option_position_tax_lots`, and P28A-T3B shortened
    the revision id to fit `alembic_version.version_num`. Full-stack save-flow
    smoke remains the P28A-T4 closeout gate.
- `P28A-T3A/T3B` - Alembic saved-artifact migration metadata fixes.
  - Owner: Codex C. Reviewer: Codex B if touched again.
  - Scope: migration metadata fixes only so backend startup can resolve and
    store revision `0020_saved_review_artifacts` after
    `0019_option_position_tax_lots`.
  - Status: done 2026-06-13; no schema/contract behavior change. Verification:
    `cd backend && ./.venv/bin/alembic heads` -> single head
    `0020_saved_review_artifacts`; `alembic current` reached DB connection and
    failed only because local Postgres was not running; focused report tests
    passed.
- `P28A-T3C` - Saved-review-source caveat-code sanitizer.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: fix full-stack save-flow materialization where backend-generated
    caveat codes contained saved-artifact-forbidden private tokens such as
    `buying_power`.
  - Status: done 2026-06-14. Added a saved-review-source sanitizer at the
    `trade_reviews.py` materialization boundary, mapping private liquidity and
    collateral caveats to report-safe codes such as
    `liquidity_model_unverified` or `account_feasibility_not_evaluated`.
    The global saved-artifact validator was not relaxed. Verification reported
    by Codex C: focused backend tests -> 137 passed, 26 skipped; full-stack
    smoke: backend `/health` 200, frontend proxy `/api/users` 200,
    portfolio-preview returned `trrev_...`, and
    `POST /api/users/{uid}/reports/from-trade-review` returned 201.
- `P28A-T4` - Review closeout across Codex B, visual reviewer, and Claude E if
  Agent Team output is saved.
  - Status: done for the deterministic/source snapshot foundation. No Agent Team
    output is saved yet, so Claude E saved-output review moves to Phase 29A.

## Phase 29A - Agent Team Report Architecture And Evidence Package

Status: active. P29A-T0 through P29A-T7 are complete. Next recommended work is
the public-evidence contract for currently skipped public analyst roles.

Goal:

- Turn the saved review source foundation into the product's main review
  experience: an Agent Team report generated from an immutable, validated
  evidence package.
- Keep deterministic services as the calculation/evidence foundation, not the
  final report product.
- Allow high-fidelity deterministic portfolio-impact analysis surfaces as
  supporting UX, such as before/after position-weight changes or deterministic
  risk-pattern alerts.

Reference doc:

- `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`

Architecture alignment:

- `P29A-T0` - Agent Team report architecture alignment.
  - Owner: Codex B. Product input: Codex A/founder.
  - Scope: lock evidence-package-first architecture, runtime-tool deferral,
    deterministic analysis surface boundaries, Agent Team report artifact
    shape, report statuses, and UI design workflow.
  - Acceptance: deterministic output remains a backend-owned evidence and audit
    layer; Agent Team synthesis becomes the primary narrative report when
    available; deterministic-only artifacts are drafts/source snapshots; no
    silent recomputation from current Account Details, account selector, market
    data, or route state; runtime private tools remain prohibited by default.
  - Status: accepted 2026-06-14. Founder direction confirmed that Portfolio
    Copilot should not become a deterministic report viewer. Deterministic
    services remain the evidence/calculation foundation; Agent Team synthesis is
    the primary saved-report experience; high-fidelity deterministic
    portfolio-impact views are allowed as supporting analysis surfaces; runtime
    private tools remain deferred/prohibited by default.

Next tasks:

- `P29A-T1` - Evidence package backend contract.
  - Owner recommendation: Codex C. Reviewer: Codex B.
  - Scope: define the agent-safe saved evidence package consumed by report
    generation, including scope, actionability, portfolio impact, risk,
    freshness, market context, and caveats.
  - Acceptance: evidence package is built from immutable saved review source
    data, not current Account Details/current account selector/current market
    data; includes backend-owned deterministic summaries and optional
    high-fidelity portfolio-impact sections when safe; excludes raw
    account/provider/broker IDs, account numbers, balances, buying power,
    holdings, positions, quantities, tax lots, raw payloads, prompts, traces,
    transactions, orders, advice, and execution wording.
  - Status: done 2026-06-14 by Codex C; Codex B narrow re-review PASS after
    blocker fixes.
  - Verification: added `SavedEvidencePackageRead` and supporting saved-evidence
    section/source/scope/freshness/actionability schemas in
    `backend/app/schemas/reports.py`, built only from `SavedReviewArtifactRead`;
    scope projection is intentionally lossy and excludes account labels,
    account refs, context refs, current selectors, and runtime tools; blocker
    fix preserved the immutable saved `source_kind` / `source_reference` through
    `SavedReviewArtifactRead` into the evidence source snapshot and expanded
    prohibited wording coverage for advice/recommendation phrases; added
    validator tests in `backend/tests/unit/test_report_agent_schemas.py`; ran
    `cd backend && ./.venv/bin/python -m pytest
    tests/unit/test_report_agent_schemas.py tests/api/test_reports.py
    tests/api/test_trade_review_workspace.py
    tests/services/trade_review/test_frontend_read.py
    tests/services/agent_team/test_evidence_projection.py -q` -> 148 passed,
    26 skipped. Residual note: saved-evidence wording validation is
    deterministic substring-based and acceptable for P29A-T1; P29A-T2/T3 should
    reuse or tighten it for generated Agent Team output.
- `P29A-T2` - Agent Team report output contract.
  - Owner recommendation: Claude E. Reviewer: Codex B.
  - Scope: define role outputs, synthesis sections, degraded/provider-unavailable
    states, and saveable sanitized report summaries.
  - Acceptance: report output references approved evidence sections only; role
    summaries and synthesis avoid advice/recommendation/order/execution/buy-sell
    wording; no raw private data, prompts, traces, provider payloads, or tool
    outputs enter saved reports; degraded/provider-unavailable states remain
    reportable without inventing analysis; generated-output validation reuses or
    tightens the P29A-T1 saved-evidence wording/private-data validator.
  - Status: contract accepted 2026-06-14 by Claude E; Codex B review PASS
    (review-only). Output contract, role section rules, saved-artifact mapping
    onto P28A `SavedAgentTeamSummaryRead`/`SavedAgentTeamRoleSummaryRead`,
    generated-output validator (reuses/tightens P29A-T1 saved-evidence +
    provider-output validators with an evidence-reference allowlist), failed-safe
    behavior, and report statuses
    (`source_snapshot`/`deterministic_draft`/`full_agent_report`/
    `agent_unavailable`/`validation_failed`) defined in
    `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`.
    Design/contract only; no backend/frontend implementation. Deferred to T3:
    shared safety-vocab module and persistence of report_status/final_synthesis.
- `P29A-T3` - Agent Team report generation backend path.
  - Owner recommendation: Codex C. Reviewers: Codex B and Claude E.
  - Scope: generate and persist Agent Team report output from a saved evidence
    package only.
  - Status: done 2026-06-14 by Codex C; Codex B review PASS after blocker fix.
  - Verification: added on-demand backend endpoint
    `POST /users/{uid}/reports/{thread_id}/agent-team-report`, deterministic
    saved-evidence-only generation service, P29A-T2 report read schemas,
    generated-output safety validator with evidence-reference role boundaries,
    and persistence of `report_status`, final synthesis, evidence schema
    version, evidence references, and role summaries in
    `saved_artifact_json.agent_summary`. Public analyst roles are skipped until
    reviewed public evidence exists; blocked actionability gates all roles to a
    deterministic draft; provider-unavailable and validation-failed summaries
    fail closed without persisting offending text. Existing deterministic-only
    saved artifacts and legacy reports remain readable. Blocker fix: extended
    `validate_agent_team_report_output()` to validate persisted
    `SavedAgentTeamSummaryRead`-shaped payloads (`role_summaries` and top-level
    `evidence_references`) in addition to read-model `role_sections` /
    `final_synthesis`, so unavailable evidence sections and role-boundary
    violations fail before persistence and fall back to `validation_failed`.
    Tests:
    `cd backend && ./.venv/bin/python -m pytest
    tests/unit/test_report_agent_schemas.py tests/api/test_reports.py
    tests/api/test_trade_review_workspace.py tests/services/agent_team/
    tests/services/agent_eval -q` -> 324 passed, 28 skipped, 2 deselected.
- `P29A-T4` - Reports Library / Report Detail redesign.
  - Owner recommendation: Claude A or Codex F. Reviewers: Claude B and Codex B.
  - Scope: redesign Reports around saved Agent Team analysis, with deterministic
    evidence and scope/caveats as supporting sections.
  - Status: done 2026-06-14 by Claude A; Codex B contract/privacy/safety PASS
    and Claude B visual review PASS.
  - Verification: Reports is now a saved-analysis library — a report-identity
    rail with an honest Agent-Team-analysis indicator (derived from the saved
    `agent_summary.report_status`, never current selector/Account Details/route
    state), and a reading pane that leads with the Agent Team final synthesis +
    per-role analyst sections, with deterministic scope/evidence/caveats moved to
    a supporting "Supporting evidence & provenance" block (scope summary,
    keys-only evidence references, audit disclosure). Honest states for
    `source_snapshot` (compact Generate Agent Team Report action, gated to
    snapshots that carry saved scope), `deterministic_draft`, `agent_unavailable`,
    and `validation_failed` without implying a defect or trading readiness.
    Generate uses only `POST /users/{uid}/reports/{thread_id}/agent-team-report`
    and refetches list + detail; a stale guard holds a skeleton until the fetched
    detail id matches the selected report. Added frontend type mirrors for
    `SavedAgentTeamSummaryRead`/`SavedAgentTeamRoleSummaryRead` and the
    `agent_summary` field on `ReportThreadRead`. New files under
    `frontend/src/components/reports/` (reportStatus, ReportProse,
    ReportLibraryList, AgentRoleSection, GenerateAgentTeamReport, ReportProvenance,
    ReportDetail); rewrote `ReportsPage.tsx`; added `.mp-reports-grid` responsive
    rule. No new deps, no markdown-injection, no localStorage, no frontend
    financial math, no provider/LLM calls. Verified:
    `cd frontend && npm run typecheck` clean; `npm run lint -- --max-warnings 0`
    clean; `npm run build` succeeds; `git diff --check` clean. Full-stack
    connected-data browser smoke on `/reports`: list loads with mixed states,
    selecting reports swaps the detail (stale guard holds), Generate flips a
    `source_snapshot` to `full_agent_report` and refetches list + detail, no
    console errors (only pre-existing React Router future-flag warnings), no
    horizontal overflow at 1024/1280/1440 in light and dark.
- `P29A-T4A` - Reports visual closeout polish.
  - Owner recommendation: Claude A. Reviewer: Claude B (narrow visual re-review).
  - Scope: two style-level follow-ups after the P29A-T4 PASS. (1) State-banner
    icon contrast in mute states (`source_snapshot` / `agent_unavailable`): the
    icon was the faint `--mp-rule` color; now uses readable `--mp-ink-2` (matches
    the banner body text), ~9:1 contrast on `--mp-card-2` in both themes, meaning
    unchanged. (2) Removed the border shorthand/longhand React dev-console warning
    in `ReportLibraryList` (`card`/`cardSelected` and `iconChip`) and the same
    pattern in `ReportDetail`'s banner, by switching the base styles to longhand
    `borderWidth`/`borderStyle`/`borderColor` so the per-state `borderColor`
    overrides no longer conflict. No backend/contract/scope/value changes.
  - Status: done 2026-06-14 by Claude A; Claude B narrow visual re-review PASS.
    Codex B confirmed the CSS-only changes did not require contract/privacy/safety
    re-review.
  - Verification: `cd frontend && npm run typecheck` clean; `npm run lint --
    --max-warnings 0` clean; `npm run build` succeeds; `git diff --check` clean.
    Connected-data smoke on `/reports`: banner icon computes to `--mp-ink-2` in
    both themes (light `#374151` on `#F3F5F8`, dark `#C5C8D2` on `#1F2430`); no
    style shorthand/longhand warning in the dev console after rendering the rail,
    selecting a card, and toggling themes (only pre-existing React Router
    warnings); no horizontal overflow at 1024/1280/1440 in light and dark; no
    visual regression in list/detail layout.
- `P29A-T5` - Report generation UX policy and trigger model.
  - Owner recommendation: Codex B with product input from Codex A / founder.
    Design/implementation follow-on: Claude E for contract wording if needed,
    then Claude A or Codex F for UX.
  - Scope: decide whether Agent Team report generation from a saved snapshot is
    manual, automatic, or hybrid; define honest user-visible states and when the
    product should encourage or defer generation.
  - Acceptance: no silent recomputation from current account state; saved
    snapshots remain reproducible; generation timing is honest in the UI; no
    advice/recommendation/order/execution framing; current `source_snapshot`,
    `deterministic_draft`, `full_agent_report`, `agent_unavailable`, and
    `validation_failed` states remain coherent.
  - Status: policy accepted 2026-06-15 by Claude E; Codex B review PASS
    (review-only). Product sign-off on manual-vs-auto remains with Codex A /
    founder. Recommendation: guided-manual (explicit user trigger), no
    auto-generation; transient `generating` state is UI-only, not a persisted
    status; add nullable additive `report_generated_at` (distinct from source
    `generated_at` and render `report_built_at`); explicit replace-only
    regeneration, versioned history deferred; Trade Review = save/capture and
    Reports = generate/revisit. Policy in
    `docs/claude-e-agentic/PHASE_29A_T5_REPORT_GENERATION_UX_POLICY.md`.
    Follow-on: P29A-T6 (Codex C, schema/persistence/regeneration semantics,
    folded into the single `SavedAgentTeamSummaryRead` extension) and P29A-T7
    (Claude A or Codex F, honest three-timestamp display, transient generating
    state, retry, coverage disclosure, Trade Review post-save suggestion).
- `P29A-T6` - Report generation timestamps and regeneration semantics.
  - Owner recommendation: Codex C. Reviewers: Codex B and Claude E.
  - Scope: implement the accepted guided-manual timing policy for saved Agent
    Team reports without adding auto-generation, queues, polling, or frontend
    behavior.
  - Status: done 2026-06-15 by Codex C; Codex B / Claude E consistency
    review PASS.
  - Verification: added nullable `report_generated_at` to
    `SavedAgentTeamSummaryRead` and `AgentTeamReportRead` so saved-source
    `generated_at`, Agent Team report-generation time, and read-projection
    `report_built_at` remain distinct. `POST
    /users/{uid}/reports/{thread_id}/agent-team-report` remains the explicit
    generation/regeneration path; it preserves immutable saved source/scope/
    deterministic evidence and replaces only `saved_artifact_json.agent_summary`.
    Generated states (`full_agent_report`, `deterministic_draft`,
    `agent_unavailable`, `validation_failed`) receive `report_generated_at`;
    source-only snapshots and legacy summaries read with `report_generated_at`
    null. Added deterministic `_now_utc()` service seam for tests, no persisted
    pending/generating state, no coverage descriptor, no provider/frontend/
    TradingAgents/runtime-tool changes. Tests run:
    `cd backend && ./.venv/bin/python -m pytest
    tests/unit/test_report_agent_schemas.py tests/api/test_reports.py -q` -> 40
    passed, 14 skipped locally (DB destructive-test guard).
    Broader requested suite:
    `cd backend && ./.venv/bin/python -m pytest
    tests/unit/test_report_agent_schemas.py tests/api/test_reports.py
    tests/api/test_trade_review_workspace.py tests/services/agent_team/
    tests/services/agent_eval -q` -> 327 passed, 28 skipped, 2 deselected
    locally (DB destructive-test guard). `git diff --check` clean. Review-only
    sub-agent PASS confirmed no blockers, docs adequate, and P29A-T5 policy
    consistency satisfied; sub-agent was closed after review.
- `P29A-T7` - Reports generation UX and honest timestamp presentation.
  - Owner recommendation: Claude A or Codex F. Reviewers: Claude B and Codex B.
  - Scope: frontend UX on the accepted P29A-T5 policy + P29A-T6 contract —
    honest three-timestamp display, transient (UI-only) generating state,
    per-state treatment, post-save suggestion, coverage disclosure.
  - Status: done 2026-06-15 by Claude A (frontend only); Claude B visual/UX
    review PASS and Codex B contract/privacy/safety closeout PASS. No backend or
    contract change beyond straightforward consumption of approved fields.
  - Verification: (1) Honest timestamps — the report header now shows the source
    "Snapshot saved" time and, when a report exists, a distinct "Report
    generated" time (`agent_summary.report_generated_at`); the audit disclosure
    adds a "Report generated" row and keeps "Saved record updated" as secondary.
    `report_built_at` is intentionally not surfaced — it is a technical read/build
    time and is not returned by the consumed `GET /reports[/{id}]` payloads, so
    fabricating it would be misleading. Source time is never shown as the report
    time. (2) Transient generating state — generation is single-flight per
    thread, owned by `ReportsPage` (`generatingThreadId`), shown over the prior
    persisted status (no skeleton flash; the matched body stays during refetch),
    never persisted; on success it refetches list + detail and clears, on failure
    it clears and shows a scoped, sanitized, retryable error while the saved
    report stays stable. (3) State treatment — `source_snapshot` framed as a
    complete kept analysis with an optional Generate action; `full_agent_report`
    leads with synthesis; `agent_unavailable` / `validation_failed` get a compact
    explicit "Try again" re-run (no silent regeneration). (4) Post-save
    suggestion — Trade Review's saved-snapshot confirmation now suggests
    generating an Agent Team report in Reports (suggest-only, non-blocking).
    (5) Coverage disclosure — a compact note ("Public market analysts are not yet
    enabled…") derived from existing `role_summaries`, no new fields. Files:
    `frontend/src/types/api.ts` (+`report_generated_at`), `pages/ReportsPage.tsx`,
    `components/reports/ReportDetail.tsx`, `GenerateAgentTeamReport.tsx`
    (presentational), `ReportProvenance.tsx`, `reportStatus.ts` (coverage
    helpers), `components/trade-review/SaveReviewSnapshot.tsx`. Microcopy avoids
    advice/order/execution and the forbidden `prompt` token. Verified:
    `cd frontend && npm run typecheck` clean; `npm run lint -- --max-warnings 0`
    clean; `npm run build` succeeds; `git diff --check` clean. Connected-data
    smoke on `/reports`: source snapshot shows only "Snapshot saved" + Generate
    card; an explicit generate flips it to `full_agent_report` and refetches list
    + detail (both timestamps then shown, distinct: e.g. saved Jun 13 vs report
    generated Jun 15) with the coverage note; no console errors (only pre-existing
    React Router warnings); 0px horizontal overflow at 1024/1280/1440 in light and
    dark. Claude B review caveat: source_snapshot / transient generating / retry
    were code-reviewed in the final visual pass rather than re-run live because
    the shared dev seed had already generated its only source snapshot and the
    stack had been torn down; accepted as non-blocking because the implementer's
    connected-data smoke covered the generate path. Deferred polish: add stable
    source_snapshot / agent_unavailable / validation_failed demo fixtures for
    future live re-verification.

## Phase 29B - Reviewed Public Evidence For Public Analyst Roles

Status: active. P29B-T0 architecture contract is accepted. Next recommended
work is parallel Codex C backend public-evidence design and Claude E public-role
agentic design.

Goal:

- Enable currently skipped public analyst roles (`fundamentals_analyst`,
  `news_analyst`, `technical_analyst`) to contribute to saved Agent Team reports
  from reviewed public evidence without widening private brokerage/account data
  exposure.
- Keep reports reproducible from generation-time evidence.
- Preserve evidence-package-first architecture and defer runtime agent tools by
  default.

Reference doc:

- `docs/codex-b-architecture/PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md`

Architecture alignment:

- `P29B-T0` - Public agent evidence architecture contract.
  - Owner: Codex B. Product input: Codex A/founder.
  - Status: accepted 2026-06-15. Codex C and Claude E have broad design freedom
    inside explicit rails: no private brokerage/account data, no raw provider
    payloads, no prompts/traces/secrets, no unreviewed source bodies, no runtime
    private tools, no silent recomputation from current providers, and no
    advice/order/execution/guaranteed-return/safe-to-trade wording.
  - Design-tool sequencing: do not introduce Claude Design or Stitch until
    backend public-evidence sample payloads and Claude E public-role output
    states are stable and reviewed.

Next tasks:

- `P29B-T1` - Backend public evidence contract and projection design.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: design the additive backend public evidence schema/projection that
    can extend saved evidence packages for public analyst roles. Codex C may
    choose schema names, section splits, adapter boundaries, persistence
    strategy, fake-provider shape, and validator internals, provided saved
    reports remain reproducible and the Phase 29B hard rails are preserved.
  - Acceptance: public evidence sections are additive/backward-compatible and
    include availability, freshness/provenance, rights status, limitations, and
    stable section keys; validators reject private keys, raw payloads,
    unreviewed article bodies, unsafe wording, prompts, traces, and secrets;
    tests use synthetic public evidence and mocked/fake providers only.
  - Verification: design doc or implementation report must state whether any
    real provider/source is used. Default is fake/mock only until source/rights
    approval exists.
  - Status: done 2026-06-15 by Codex C; Codex B review PASS.
  - Implementation summary: added additive saved public-evidence schemas in
    `backend/app/schemas/reports.py`:
    `SavedPublicEvidencePackageRead`, `SavedPublicEvidenceSectionRead`, and
    `SavedPublicEvidenceFactRead`, with stable section keys
    (`public_company_profile`, `public_fundamentals_snapshot`,
    `public_news_snapshot`, `public_events_calendar`,
    `public_technical_context`, `public_market_context`). Each section carries
    availability, freshness category/label, source label, rights status,
    limitations, optional facts, and safe caveat codes. `SavedEvidencePackageRead`
    now includes additive `public_evidence`, defaulting all sections to
    `not_reviewed` for current saved artifacts. Added
    `backend/app/services/reports/public_evidence.py` as the offline provider
    boundary; the default provider returns not-reviewed sections only and makes
    no external calls.
  - Safety/validation: added `validate_public_evidence_payload()` to reject
    private keys, raw source fields, raw provider payload hints, URLs, article
    bodies, prompts, traces, secrets, and unsafe wording. Extended
    `validate_agent_team_report_output()` evidence keys/role allowlists for
    public sections and made availability collection recursive so nested public
    sections must be `available` or `limited` before public roles can cite them.
    No frontend, route, persistence-table, provider, LLM, TradingAgents, or
    runtime-tool behavior was added; no real provider/source is used.
  - Verification: `cd backend && ./.venv/bin/python -m pytest
    tests/unit/test_report_agent_schemas.py -q` -> 46 passed.
    `cd backend && ./.venv/bin/python -m pytest
    tests/unit/test_report_agent_schemas.py tests/api/test_reports.py
    tests/api/test_trade_review_workspace.py tests/services/agent_team/
    tests/services/agent_eval -q` -> 333 passed, 28 skipped, 2 deselected
    locally (DB destructive-test guard). `git diff --check` clean. Codex B
    review PASS; docs adequate; Claude E can start P29B-T2 from these section
    keys and citation rules. Non-blocking handoff note: P29B-T2/T3 must preserve
    calls to `validate_agent_team_report_output(..., evidence_package=evidence)`
    so nested public-section availability is enforced.
- `P29B-T2` - Public role agentic design.
  - Owner: Claude E. Reviewer: Codex B.
  - Scope: design the public-role evidence projections, role behavior, output
    rules, degraded states, and validation/evaluation plan for fundamentals,
    news, and technical analysts. Claude E may choose prompt/projection shape,
    role degradation semantics, evaluation cases, role output structure, and
    whether additive report-output fields are needed.
  - Acceptance: public roles cite only approved available/limited public
    evidence sections; missing/unreviewed evidence degrades honestly; generated
    output remains analysis-only and avoids advice/order/execution,
    guaranteed-return, safe/ready-to-trade, and buy/sell instruction wording;
    no prompts, traces, raw provider payloads, private data, or tool outputs are
    saved or exposed.
  - Status: design accepted 2026-06-15 by Claude E; Codex B review-only PASS.
    Per-role evidence projections, citation allowlists (matching shipped
    `ROLE_ALLOWED_EVIDENCE_KEYS`), honest fail-closed degradation matrix
    (not_reviewed / not_available / not_applicable / stale-limited /
    provider_unavailable / validation_failed over the existing
    `AgentTeamReportRoleStatus`), PM-synthesis rules, and a synthetic
    positive/negative eval plan are defined in
    `docs/claude-e-agentic/PHASE_29B_T2_PUBLIC_ROLE_AGENTIC_DESIGN.md`. No
    required new report-output fields (one optional nullable
    `public_evidence_coverage` and two additive validator tightenings noted for
    T3). Design-only; no code. T3 must preserve
    `validate_agent_team_report_output(..., evidence_package=evidence)` (the only
    site that enforces nested public-section availability) and persist
    generation-time public sections so reopened reports reproduce without
    current-provider re-fetch.
- `P29B-T3A` - Backend public evidence persistence and projection seam.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: implement the backend-owned generation-time `public_evidence`
    persistence/readback seam and role-scoped public-evidence projection
    contract. This comes first because Claude E needs a stable backend evidence
    shape and reproducibility path before wiring public-role behavior.
  - Acceptance: generation-time `public_evidence` can be persisted in the saved
    artifact/readback path; `SavedEvidencePackageRead.from_saved_review_artifact`
    reads saved public sections when present and defaults to `not_reviewed` only
    when absent; role-scoped public evidence projections are backend-built from
    the same `SavedEvidencePackageRead` instance used for validation and
    persistence; no real provider/source, frontend, LLM, TradingAgents, runtime
    tool, or external call is added; default tests are offline, deterministic,
    and synthetic.
  - Status: ask Codex C first.
- `P29B-T3B` - Public role generation wiring and validation behavior.
  - Owner: Claude E. Reviewer: Codex B; Codex C cross-review if backend seams are
    touched.
  - Dependency: P29B-T3A reviewed and PASSed.
  - Scope: wire the public-role behavior from P29B-T2 onto the backend
    projection seam: role-scoped prompt/public-context inputs, skipped/
    unavailable/validation-failed role handling, PM synthesis use of validated
    public summaries, and the synthetic positive/negative eval cases.
  - Acceptance: public roles complete only from approved available/limited
    synthetic public sections; default `not_reviewed` sections continue to skip
    honestly; role-boundary and availability violations fail closed; the
    package-aware `validate_agent_team_report_output(...,
    evidence_package=evidence)` call is preserved before persistence; technical
    invented-level and source-leak/advice/private-data negative cases fail
    closed.
  - Status: ask Claude E after P29B-T3A PASS.
- `P29B-T3C` - Integrated closeout and docs checkpoint.
  - Owner: original implementer of the final T3B fix, with Codex B review.
  - Scope: close P29B-T3 after T3A/T3B PASS, then update only the active plan,
    changelog, and any required architecture note. Do not leave long
    verification transcripts in the active plan.
  - Acceptance: P29B-T3 status is concise; detailed history is in changelog or
    completed-phase/archive docs; next frontend/design step is explicit.
- `P29B-T4` - Frontend rich report optimization.
  - Owner: Claude A or Codex F. Reviewers: Claude B and Codex B.
  - Dependency: P29B-T3 reviewed and accepted, with stable sample payloads.
  - Scope: optimize Reports UI for richer public + portfolio-aware role output.
    This is where Claude Design or Stitch may be introduced under the timing
    rules in the Phase 29B contract.
  - Acceptance: frontend consumes reviewed fields only; no invented public
    evidence, role states, calculations, or citations; public-role coverage and
    provenance are understandable without overwhelming the report; no
    advice/execution/trading-readiness language.

## Recommended Coordination Checkpoint

Before starting P29B-T3A, do a narrow stabilization pass:

- clean up `docs/shared/implementation_plan.md` so it returns to a short active
  index rather than a long phase ledger;
- move durable P28A/P29A/P29B completion detail to
  `docs/shared/CHANGELOG.md`, `docs/shared/completed_phases_log.md`, or a dated
  archive snapshot;
- verify the dirty worktree contains only intentional recent phase changes;
- then commit and push the accepted P28A/P29A/P29B foundation before the next
  implementation slice touches report generation again.

Rationale: P29B-T3A will modify saved-artifact/readback and report-generation
seams that already carry many recent uncommitted changes. A checkpoint now
reduces review risk and prevents future agents from rereading completed history.

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
