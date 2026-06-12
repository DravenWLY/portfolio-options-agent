# Phase 27B Account Details Stability Contract

Status: active architecture reference
Owner: Codex B
Related plan: `docs/shared/implementation_plan.md` Phase 27B

## Purpose

Phase 27A proved that Account Details can be private, display-label-only, and
multi-account aware. Phase 27B changes the product posture: Account Details v1
must be an honest broker-data readiness page, not a holdings mirror.

The reason is current-position truth. A broker sync can return a latest account
snapshot while older normalized local rows remain in the database. Until the app
can prove which rows belong to the latest successful sync snapshot, equity and
option rows must not be presented as authoritative current holdings.

## Core Rule

A position is current only when it belongs to the latest successful sync
snapshot/batch for that account, or when it is explicitly current in a reviewed
manual/CSV snapshot.

Rows missing from the latest successful provider snapshot are not current. An
expired option must never appear in a current positions section.

## Account Details V1 Display Policy

Allowed in normal v1:

- backend-owned broker/source label;
- backend-owned account display label;
- backend-owned account kind label when available;
- source type: SnapTrade, manual, CSV;
- connection status;
- sync status;
- last successful sync label;
- freshness/as-of labels;
- reauthorization/error caveats;
- broad portfolio shape counts;
- backend-formatted cash labels;
- cash state labels;
- currency;
- cash freshness/as-of labels.

Required caveat copy, where relevant:

- `Cash is broker-reported. Buying power, free cash, and option collateral treatment are not fully modeled yet.`
- `Position details are temporarily limited while latest-sync membership is verified.`
- `This account snapshot may include stale local rows. Current-position review will remain caveated until sync membership is validated.`

Hidden or deferred from normal v1:

- buying-power detail;
- collateral detail;
- full holdings grid;
- tax lots;
- transactions;
- order history;
- raw balances;
- raw holdings/positions/quantities/lots;
- broker account IDs;
- provider IDs;
- raw provider payloads;
- performance benchmarking;
- P/L charts;
- account transfer logic.

Equity rows:

- Do not present as authoritative current holdings until latest-sync membership
  is fixed.
- Prefer hiding row-level equity details in normal v1.
- If shown during development/debugging, label them as:
  `Broker snapshot rows - may include stale positions until latest-sync validation is complete.`

Option rows:

- Hide from normal current-position display until expired/closed/missing
  handling is fixed.
- Expired options must never appear in a current positions section.
- Later expired/closed options may appear only in a separate historical section
  after transaction/history semantics exist.

## Latest-Sync Membership Semantics

The backend must define a sync membership boundary before position rows can be
used as current account truth.

Required states:

- `current`: belongs to latest successful sync snapshot/batch, or reviewed
  current manual/CSV snapshot.
- `stale_local`: exists in local storage but is not proven to belong to latest
  successful sync.
- `absent_from_latest_sync`: previously known position that did not appear in
  latest successful provider snapshot.
- `expired`: option contract expiration is before the app's current date.
- `closed`: provider/manual/CSV source explicitly marks the position closed, or
  backend reconciliation marks it non-current after latest sync.
- `unknown`: backend cannot safely classify the row.

Implementation may use a `sync_run_id`, `snapshot_id`, or equivalent membership
marker. The key requirement is that the selected-account read path can determine
whether a row is part of the latest successful account snapshot.

## Deterministic Review Data-Use Policy

Until latest-sync membership is enforced:

- broker/account metadata may be used only for provenance and freshness;
- cash may support cautious cash-state labels only;
- equity rows must not be treated as authoritative current holdings;
- option rows must not be used for current assignment, exercise, covered-call,
  cash-secured-put, or option exposure logic;
- position-dependent real-broker reviews should downgrade to
  `analysis_only`, `manual_confirmation_required`, or `blocked`, depending on
  flow and missing-data severity.

Covered calls and cash-secured puts:

- covered-call coverage cannot rely on real broker option/stock rows until
  latest-sync membership is enforced;
- cash-secured-put collateral cannot rely on buying power/collateral until a
  separate cash/collateral policy is reviewed.

Broker snapshot freshness and market quote freshness remain separate concepts.

## P27B-T9 Buying Power And Collateral Policy

Status: accepted architecture decision for private alpha

### Decision

Portfolio Copilot may display broker-reported cash, available cash, and buying
power labels privately on Account Details, but deterministic trade-review
feasibility must not treat those labels as approved collateral, free cash, or
order capacity.

Buying power is not cash. Broker-specific buying power may include margin,
unsettled proceeds, option approval, broker house rules, account restrictions,
or instrument-specific treatment that Portfolio Copilot does not yet model.
Therefore buying power is display-only until a separate broker/account-type
collateral model is approved and tested.

### Display-Only Fields

The selected-account detail read may show backend-owned display labels for:

- broker-reported cash;
- available cash;
- buying power;
- currency;
- balance source;
- cash state;
- sync/freshness labels.

These labels remain private, authenticated, and account-specific. They must not
be exposed to Agent Team prompts by default and must not be used by frontend
code for calculations.

### Deterministic Review Use

Until a later collateral model is approved:

- `buying_power_label` is display-only;
- `available_cash_label` is display-only for feasibility;
- broker-reported cash may support conservative cash-state wording only;
- reserved collateral is not considered modelled unless produced by an
  app-owned deterministic rule with reviewed inputs;
- account-level feasibility remains not evaluated for real-broker
  position-dependent option flows;
- CSP collateral checks must remain `analysis_only`,
  `manual_confirmation_required`, or `blocked` rather than claiming sufficient
  cash/collateral;
- covered-call coverage remains unverified unless current same-account share
  coverage, deliverable, and option contract semantics are explicitly modelled.

### Account-Type Rules

Account kind labels may be displayed, but they are not enough to infer
permissions.

- Cash accounts: do not assume all cash is settled or available for options.
- Margin accounts: do not treat margin buying power as CSP collateral.
- IRA/Roth/retirement accounts: do not infer option permissions or collateral
  treatment from the label alone.
- Unknown account kind: always display-only for feasibility.

### CSP Policy

Cash-secured-put collateral may be estimated generically as
`strike * multiplier * contracts` for explanation, but the app must state that
the estimate is not broker-specific and does not validate account capacity.

The app may not mark a CSP as cash-secured, feasible, ready, safe, or
supported by broker buying power until all of the following are reviewed:

- selected review account is resolved and current;
- account type and option permissions are modelled;
- cash/free-cash/settlement semantics are modelled;
- existing open short-put collateral reservation is modelled;
- source freshness and latest-sync membership are acceptable;
- deterministic tests cover missing/partial/stale data.

### Covered-Call Policy

Covered-call coverage may not rely on broad portfolio context or shares held in
another account. It must be same-review-account only.

Coverage remains unverified until all of the following are reviewed:

- selected review account is resolved and current;
- current stock/ETF rows are latest-sync members;
- share quantity and option deliverable/multiplier semantics are modelled;
- existing open short calls are considered;
- expired/closed/missing option rows are excluded from current exposure.

### Agent Team Evidence

Agent Team evidence may receive only high-level policy outcomes and caveat
codes, such as:

- `cash_display_only`;
- `buying_power_display_only`;
- `cash_collateral_policy_not_reviewed`;
- `account_level_feasibility_not_evaluated`;
- `covered_call_coverage_unverified`;
- `csp_collateral_unverified`.

Agent Team evidence must not receive account refs, account labels, display cash
values, buying power values, raw balances, position rows, option rows, tax lots,
provider IDs, provider payloads, or account-specific thresholds by default.

### Required Backend Behavior

Real-broker Trade Review should preserve or add caveats when the review depends
on account-level cash/collateral/coverage:

- do not set `account_level_feasibility_evaluated=true` from display-only
  cash/buying-power labels;
- keep CSP collateral model generic or unreviewed;
- keep covered-call coverage unverified unless same-account coverage is
  explicitly modelled;
- preserve broker snapshot freshness and market quote freshness separately;
- never emit `safe to trade`, `ready to trade`, order, execution,
  recommendation, or guaranteed-return wording.

Rollback:

- If implementation becomes uncertain, force real-broker CSP and covered-call
  reviews to `analysis_only` with `cash_collateral_policy_not_reviewed` or
  `covered_call_coverage_unverified` caveats.

## Agent Team Evidence Policy

Allowed agent-safe evidence for now:

- broker freshness status;
- market quote freshness status;
- source/data mode;
- account scope mode;
- whether account-level feasibility was evaluated;
- broad portfolio shape counts or buckets;
- caveat codes;
- stale/missing-membership caveat;
- actionability status;
- deterministic summary categories.

Blocked from LLM/agent evidence:

- account refs;
- account display labels unless explicitly approved later;
- raw or display cash values;
- buying power values;
- raw/display holdings;
- position quantities;
- option contract rows;
- broker/provider IDs;
- raw provider payloads;
- stale local position rows;
- account-specific thresholds;
- transaction/order data.

Deterministic backend services may compute safe summaries first. LLM agents may
receive only high-level, caveated summaries, never raw rows or account
identifiers.

## Work Packages

### P27B-T0 - Account Details Data Policy And Contract Freeze

Owner: Codex B

Dependencies: Codex A product decision complete.

Areas expected to change:

- `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`
- `docs/shared/implementation_plan.md`

Steps:

- Record Account Details v1 as broker-data readiness, not holdings mirror.
- Freeze allowed/hidden fields.
- Define latest-sync membership rule.
- Define deterministic review data-use gates.
- Define Agent Team evidence boundary.

Acceptance:

- Codex C can implement backend membership work without guessing UI policy.
- P27A selected-position rows are clearly not product-authoritative until P27B
  membership is complete.

Review gates:

- Codex B architecture signoff.
- Codex A PM sanity check if product wording changes.

Rollback:

- Docs-only; revert this file and plan entry.

Status recommendation: done.

### P27B-T1 - Latest Sync Membership Foundation

Owner: Codex C

Dependencies: P27B-T0.

Areas expected to change:

- broker sync models and migrations, if needed;
- broker sync normalization services;
- stock/option/cash normalized models or equivalent snapshot membership tables;
- broker sync tests.

Steps:

- Add `sync_run_id`, `snapshot_id`, or equivalent membership identity to
  normalized cash/equity/option rows.
- Associate rows produced by a broker sync with that sync.
- Define latest successful sync lookup per broker account.
- Mark or classify rows missing from latest successful sync as non-current.
- Preserve local history without exposing it as current.

Acceptance:

- A repeated sync where a previously present stock disappears no longer returns
  that stock as current.
- A repeated sync where a previously present option disappears no longer returns
  that option as current.
- Existing account details summary labels do not double-count stale historical
  rows.

Tests/review:

- disappearing-stock test;
- disappearing-option test;
- repeated-sync test;
- missing-from-latest classification test;
- forbidden-field tests.

Rollback:

- Keep Account Details v1 summary-only and hide position rows if migration or
  membership logic is uncertain.

Status recommendation: done; Codex B PASS.

### P27B-T2 - Option Current/Expired/Closed Semantics

Owner: Codex C

Dependencies: P27B-T1.

Areas expected to change:

- option normalization;
- `OptionPosition.status` handling;
- selected Account Details detail rows;
- option-position tests.

Steps:

- Stop setting every normalized option position to `open`.
- Exclude expired options from current positions.
- Classify absent-from-latest options as non-current.
- Keep future historical/closed display out of normal Account Details v1.

Acceptance:

- Expired options, including previously cached rows, cannot appear in the
  current positions section.
- Missing/closed options do not affect current option exposure labels unless the
  backend explicitly marks them current.

Tests/review:

- expired option test;
- missing option after latest sync test;
- current non-expired option test;
- unsupported OCC symbol safety test.

Rollback:

- Hide all option rows and option-dependent current-position summaries.

Status recommendation: done; Codex B PASS.

### P27B-T3 - Account Details V1 Backend Read Contract

Owner: Codex C

Dependencies: P27B-T0; can start before T1 if position rows remain suppressed.

Areas expected to change:

- `backend/app/schemas/trade_review_workspace.py`
- `backend/app/services/trade_review/frontend_read.py`
- `backend/app/api/routes/users.py` if route behavior changes
- account details tests.

Steps:

- Refine Account Details to a broker-readiness read contract.
- Keep safe account/source/sync/freshness/cash labels.
- Suppress row-level equity/option details unless latest-sync membership is
  verified.
- Replace raw caveat codes in normal UI-facing fields with backend-owned
  readable labels or compact status sections.
- Keep raw caveat codes available for deterministic services only if needed.

Acceptance:

- Account Details v1 cannot be mistaken for authoritative holdings.
- Cash is labelled as broker-reported and collateral/buying-power caveats are
  visible.
- No raw IDs, raw balances, raw positions, quantities, lots, provider payloads,
  orders, or transaction data are exposed.

Tests/review:

- v1 summary-only response tests;
- hidden/suppressed position-row tests;
- readable caveat/status label tests;
- forbidden-field tests.

Rollback:

- Return current Account Details summary fields and hide selected detail rows.

Status recommendation: ready.

### P27B-T4 - Deterministic Trade Review Gating

Owner: Codex C

Dependencies: P27B-T0; full current-position usage waits for P27B-T1/T2.

Areas expected to change:

- trade review actionability services;
- portfolio context read/projection;
- deterministic review tests.

Steps:

- Add membership-stability caveats to position-dependent real-broker reviews.
- Downgrade or block covered-call/CSP feasibility when current holdings,
  option positions, or collateral are not verified.
- Preserve broker freshness vs market quote freshness separation.

Acceptance:

- Covered-call coverage does not rely on stale local share rows.
- CSP collateral does not rely on unreviewed buying power/collateral fields.
- Account-level feasibility is clearly not evaluated or is downgraded when
  prerequisites are missing.

Tests/review:

- covered-call without validated shares;
- CSP without reviewed collateral policy;
- stale membership downgrade;
- broker/market freshness separation.

Rollback:

- Force `analysis_only` for real-broker position-dependent flows.

Status recommendation: policy can be implemented after T0; richer logic waits
for T1/T2.

### P27B-T5 - Agent Team Evidence Boundary Update

Owner: Claude E

Dependencies: P27B-T0 and P27B-T4 policy.

Areas expected to change:

- `backend/app/services/agent_team/evidence_projection.py`
- agent eval tests;
- Claude E agentic architecture docs.

Steps:

- Update evidence policy to include only freshness, scope, broad buckets,
  caveats, and deterministic actionability categories.
- Add or tighten forbidden-field tests for account labels, refs, cash values,
  holdings, quantities, and option contracts.

Acceptance:

- Agent prompts receive no account labels, refs, display cash values, holdings,
  quantities, option rows, provider IDs, or stale local rows by default.

Tests/review:

- Claude E implementation review.
- Codex B privacy review.
- Claude B privacy/safety review if UI copy changes.

Rollback:

- Remove broker-derived evidence from Agent Team entirely.

Status recommendation: ready after T0.

### P27B-T6 - Account Details Frontend V1 Redesign

Owner: Codex F or Claude A

Dependencies: P27B-T3 Codex B PASS.

Areas expected to change:

- `frontend/src/pages/AccountDetailsPage.tsx`
- account details types/API if the read contract changes;
- possible shared UI primitives.

Steps:

- Redesign `/account-details` as a broker-data readiness page.
- Show account rail, selected account status, sync/freshness, cash summary, and
  compact data-status/caveat panel.
- Hide holdings/options rows in normal v1 unless backend contract marks them
  current-safe.
- Remove repeated freshness/as-of clutter and unexplained caveat code display.

Acceptance:

- The page does not display all accounts at once.
- The page does not look like a holdings mirror.
- There are no unexplained raw caveat codes.
- No broker actions, order controls, execution UI, advice, or recommendation
  wording.

Tests/review:

- typecheck, lint, build, `git diff --check`;
- browser smoke at 1024/1280/1440 light/dark;
- Codex B contract/privacy review;
- Claude B privacy/safety review;
- Codex F UI/product UX review.

Rollback:

- Keep master/detail shell and hide selected position sections.

Status recommendation: frontend-only after T3.

### P27B-T7 - Private Alpha Current Positions Addback

Owner: Codex C plus Codex F

Dependencies: P27B-T1, P27B-T2, P27B-T3, P27B-T6.

Areas expected to change:

- selected Account Details backend detail contract;
- frontend selected-account tables.

Steps:

- Add current equity/option sections back only after membership is stable.
- Keep expired/closed options out of current positions.
- Label any historical/closed section separately and only after a history
  contract exists.

Acceptance:

- Position rows are latest-sync members only.
- Expired options never appear current.
- No stale local row is rendered as current.

Tests/review:

- disappearing/expired rows never shown current;
- frontend table does not compute values.

Rollback:

- Summary/readiness-only Account Details.

Status recommendation: later.

### P27B-T8 - Buying Power And Collateral Policy

Owner: Codex B with Codex C

Dependencies: P27B-T0 and provider data inventory.

Areas expected to change:

- architecture docs;
- cash normalization;
- deterministic review collateral services.

Steps:

- Decide how buying power, free cash, and reserved collateral differ by broker
  and account type.
- Decide whether CSP collateral can use any provider buying-power field.
- Define display labels and review gates.

Acceptance:

- CSP collateral is not inferred from generic buying power.
- Account Details copy is clear that cash is broker-reported and collateral is
  not fully modeled until approved.

Tests/review:

- cash account vs margin vs IRA policy tests;
- deterministic review downgrade tests.

Rollback:

- Hide buying power/collateral detail.

Status recommendation: blocked by policy.

## Review Gates

- Codex B: architecture and backend privacy review for P27B-T0/T1/T3/T4.
- Claude E: Agent Team evidence review for P27B-T5.
- Claude B: frontend privacy/safety review for P27B-T6.
- Codex F: Account Details UI/product UX review for P27B-T6.
- Codex A: PM acceptance after P27B-T6 before current holdings are added back.

## Open Decisions

- Should account display labels be user-editable later? Defer.
- Should account group/scope management be built now? Defer until Account
  Details is stable.
- Should Account Details show any position rows in private alpha after
  membership fix? Decide after P27B-T1/T2.
- What exact policy governs buying power, free cash, and reserved collateral?
  Resolved for private alpha by P27B-T9: display-only until a later
  broker/account-type collateral model is approved.
- Should expired options ever appear outside a future history/transactions page?
  Not in v1.
