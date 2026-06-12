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

Review state:

- Codex B contract/privacy reviews: PASS through P27B-T22.
- Claude B visual/safety smoke for Account Details: PASS after full-stack preview
  dev-token fix.
- Remaining caveat: DB-backed destructive tests are skipped unless a disposable
  safe test DB is explicitly enabled.

## Next Recommended Work

### Phase 27C - Trade Review And Agent Team Scope Integration

Status: architecture ready; implementation not started.

Goal:

- Use the stabilized Account Details scope/account model to make Trade Review,
  saved reports, and Agent Team readouts state scope clearly and consistently.

Reference doc:

- `docs/codex-b-architecture/PHASE_27C_TRADE_REVIEW_AGENT_SCOPE_INTEGRATION_CONTRACT.md`

Recommended first task:

- `P27C-T1` - Trade Review review-account selector frontend wiring.
  - Owner: Claude A or Codex F.
  - Reviewer: Codex B for contract/safety; Claude B for UI if visual changes are
    substantial.
  - Architecture: follow
    `docs/codex-b-architecture/PHASE_27C_TRADE_REVIEW_AGENT_SCOPE_INTEGRATION_CONTRACT.md`.
  - Scope: consume existing backend scope metadata and selected review account
    contract; no new backend fields unless Codex B opens a separate backend task.
  - Acceptance: Trade Review clearly separates `Review account` from broader
    `Portfolio context scope`; no frontend financial computation; no raw account
    IDs/provider IDs; no advice/execution wording.

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
