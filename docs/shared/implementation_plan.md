# Implementation Plan

Active coordination index for Portfolio Copilot. Keep this file short: current
work, next handoff, review gates, and status only. Historical task detail belongs
in the archives and logs listed below.

## Source Of Truth

- Current product direction: `docs/shared/current_roadmap.md`
- Agent workflow rules: `docs/shared/agent_workflows.md`
- Report format: `docs/shared/AGENT_REPORT_FORMAT.md`
- Completed phase history: `docs/shared/completed_phases_log.md`
- Human-readable recent changes: `docs/shared/CHANGELOG.md`
- Archived active-plan snapshots:
  - `docs/shared/implementation_plan_archive_2026-06-03.md`
  - `docs/shared/implementation_plan_archive_2026-06-12.md`
  - `docs/shared/implementation_plan_archive_2026-06-15.md`
  - `docs/shared/implementation_plan_archive_2026-06-19.md`

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

### Completed Foundation

- Phase 27B Account Details stability is complete enough for UI use.
- Phase 27C Trade Review / Agent Team / Reports scope integration is complete
  for the scoped work; account group/scope management remains deferred.
- Phase 28A saved review artifact foundation is complete.
- Phase 29A Agent Team report experience is complete through P29A-T7:
  evidence-package-first report generation, saved report output contract,
  backend generation/persistence, Reports redesign, guided-manual generation
  policy, honest report timestamps, and frontend generation UX.
- Phase 29B reviewed public evidence, Reports, and Skyframe work is complete
  through P29B-T7 and reviewed PASS.
- Phase 29C EDGAR `public_company_profile` vertical slice is complete through
  saved-report provenance display and reviewed PASS.
- Phase 30A Golden Path Review Desk Prototype is accepted as the first coherent
  internal prototype loop and committed at `35f1d01`.
- Phase 30B Golden Path Prototype Hardening And Demo Readiness is accepted as
  the internal MVP validation loop and committed at `df47a1b`.

Reference docs:

- `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_28A_SAVED_REVIEW_ARTIFACT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`
- `docs/codex-b-architecture/PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29C_PUBLIC_EVIDENCE_SOURCE_GOVERNANCE.md`
- `docs/codex-b-architecture/PHASE_30A_GOLDEN_PATH_REVIEW_DESK_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_30B_GOLDEN_PATH_HARDENING_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_31A_FOUNDER_DEMO_POLISH_CONTRACT.md`
- `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
- `docs/claude-e-agentic/PHASE_29A_T5_REPORT_GENERATION_UX_POLICY.md`
- `docs/claude-e-agentic/PHASE_29B_T2_PUBLIC_ROLE_AGENTIC_DESIGN.md`

Detailed verification history is archived in:

- `docs/shared/implementation_plan_archive_2026-06-15.md`
- `docs/shared/implementation_plan_archive_2026-06-19.md`
- `docs/shared/CHANGELOG.md`
- `docs/shared/completed_phases_log.md`

## Recently Completed

### Phase 29B - Reviewed Public Evidence And Skyframe

- `P29B-T0` - Public evidence architecture contract: accepted.
- `P29B-T1` - Backend public evidence contract/projection foundation: done;
  Codex B review PASS.
- `P29B-T2` - Public-role agentic design: done; Codex B review PASS.
- `P29B-T3` - Generation-time persistence/readback and public-role generation
  wiring: done; T3A/T3B reviews PASS.
- `P29B-T4` - Reports product/design closeout.
  - Status: done. Direction A (Synthesis Column) is founder-accepted and Claude B
    reviewed PASS. Reports is the Skyframe reference surface and uses reviewed
    read-contract fields only; proposed Track-B fields remain deferred.
- `P29B-T5` - Reports Skyframe token/surface reference.
  - Status: done. Reports uses the accepted light-sky atmosphere with medium-high
    structural contrast; no contract, report-semantic, or privacy boundary changed.
- `P29B-T6` - Shared Skyframe primitive, token migration, and rollout guard.
  - Status: done. `SkyframeSurface`, the per-surface checklist, and the warning-only
    raw-hex/legacy-token guard are implemented and reviewed PASS.
- `P29B-T7` - Route rollout and private-safe connected verification.
  - Status: done. Reports, Trade Review, Dashboard, Settings, Market Data, Risk,
    and Market Mood use the accepted Skyframe shell. Visual/safety reviews passed.
    A dev/test-only, production-fail-closed synthetic fixture overlay covers saved
    reports, Dashboard states, and the fixed synthetic account selector without
    real-data fallthrough; Codex B contract/privacy reviews passed. Account Details
    and Agent Console remain explicitly deferred as higher-scrutiny surfaces.
- Phase 29B closeout: complete through P29B-T7. Reviewed public-evidence contracts,
  role-scoped agent inputs, generation-time persistence/readback, public-role
  degradation/validation, Reports presentation, and Skyframe reference rollout are
  accepted. Production public-evidence sourcing, rights, provider policy, and
  freshness operations move to the next architecture phase.
- Detailed P29B-T4 through T7 implementation and verification history is archived in
  `docs/shared/implementation_plan_archive_2026-06-19.md`.
- `MAINT-BE-1` - Seven stale/nondeterministic backend tests reconciled; full
  backend suite clean (`1045 passed`, `122 skipped`, `3 deselected`).

## Next Handoff

### Phase 31A - Founder Demo Polish And Product Narrative

- `P31A-T0` - Founder demo polish contract and task sequence.
  - Owner: Codex B. Reviewer: Codex A/founder as needed.
  - Architecture reference:
    `docs/codex-b-architecture/PHASE_31A_FOUNDER_DEMO_POLISH_CONTRACT.md`.
  - Status: done 2026-06-23 by Codex B. P31A is PASS to open as a narrow polish/
    narrative phase. The goal is to make the working P30A/P30B internal
    validation loop feel like a believable founder demo without expanding
    product scope. No new providers, public evidence sources, Dashboard
    expansion, Account Details redesign, Agent Console composer, auth/pricing/
    signup implementation, runtime tools, frontend financial calculations,
    broker/order behavior, or private-data exposure are in scope.

- `P31A-T1` - Product narrative docs alignment.
  - Owner: Codex A. Reviewer: Codex B.
  - Scope: update PRD, MVP scope, positioning, and roadmap language where
    relevant so Portfolio Copilot is consistently described as a read-only
    specialist review desk for busy self-directed investors. Preserve the core
    question: "What would I be ignoring if I acted manually now?" Do not expand
    product scope or imply advice, execution, automation, or AI stock-picking.
  - Acceptance criteria: product docs distinguish internal validation prototype
    from public MVP; P30A/P30B golden path is the demo baseline; placeholder
    areas are named honestly; deferred surfaces remain deferred.
  - Status: done 2026-06-23 by Codex A. Updated PRD, MVP scope, and positioning
    docs to consistently frame Portfolio Copilot as a read-only specialist
    review desk for busy self-directed investors centered on "What would I be
    ignoring if I acted manually now?" Preserved manual decision-support, no
    advice/order/execution, no AI-stock-picker, and no scope-expansion
    boundaries. The docs now distinguish the P30A/P30B/P31A state as an
    internal founder-demo validation loop, not a public MVP or commercial beta.

- `P31A-T2` - Golden path copy and technical-artifact audit.
  - Owner: Claude A. Reviewers: Codex B and Claude B.
  - Scope: inventory Trade Review, Save Evidence Snapshot, Reports Library,
    Report Detail, Agent Team briefing states, and accessible adjacent surfaces
    for rough copy, raw scope-note codes, synthetic/demo labels, technical
    handles, disjointed save/generate/report continuity, and unsupported-surface
    distractions. Produce a narrow patch plan before broad visual changes.
  - Acceptance criteria: audit identifies which fixes are presentation-only,
    which need Codex B contract review, and which should be deferred. Raw
    scope-note code friendly labels should be treated as frontend mapping over
    existing reviewed codes unless a backend field is requested.
  - First implementation owner: Claude A.
  - Status: done 2026-06-23 by Claude A; Codex B and Claude B review PASS.
    Audited the golden path (Trade Review, Save Evidence Snapshot, Reports
    Library/Detail, Agent Team briefing states) and accessible adjacent surfaces
    for raw scope-note/caveat/warning codes, technical handles, and synthetic/
    demo labeling, and produced a narrow presentation-only patch plan. Friendly
    scope-note labels are scoped as frontend mapping over existing reviewed
    codes; visible `/portfolio-context` `ctx_` handles were routed to P31A-T4 as
    adjacent-surface hygiene.

- `P31A-T3` - Golden path frontend polish.
  - Owner: Claude A, with Codex F as backup. Reviewers: Claude B and Codex B.
  - Status: done 2026-06-23 by Claude A; Claude B visual/safety review PASS and
    Codex B contract/privacy/safety review PASS. Applied presentation-only golden-
    path polish: a `scopeNoteLabel` friendly-label map over existing backend-owned
    scope-note/caveat/warning codes (raw code preserved for audit via `title`),
    applied in Report scope summary, Report provenance, the saved Agent role
    section, the Agent Team scope banner, and Trade Review results scope notes,
    with unmapped codes falling back to `humanizeCode`. The Trade Review demo-
    context selector now shows friendly labels while keeping the backend-owned
    `context_reference` as the option value. No new read fields, evidence,
    freshness, actionability, or status semantics; no backend/API/schema/storage
    change.

- `P31A-T4` - Adjacent surface hygiene.
  - Owner: Codex F or Claude A. Reviewers: Claude B; Codex B if copy,
    privacy, report-state, or read-contract semantics change.
  - Status: done 2026-06-23 by Claude A; Claude B visual/product-safety review
    PASS 2026-06-23 and Codex B contract/privacy review PASS 2026-06-23 (touched
    visible opaque handles). Presentation-only change on `/portfolio-context`: the list
    "Reference" column is now a friendly "Context" label
    (`contextReferenceLabel`) and the detail summary no longer shows the raw
    handle as its panel tag. The backend-owned `context_reference` is unchanged
    as the row key, selection value, detail request value, and route state; the
    raw handle stays reachable for audit via the list row `title` hover and a
    clearly-labeled detail "Reference (audit)" row. No backend/API/schema/
    storage/contract change. Connected synthetic-demo preview confirmed friendly
    labels with zero raw `ctx_` in primary visible copy, page-level horizontal
    overflow 0 at 1024/1280/1440 in light and dark, and a clean console.

- `P31A-T5` - Agent briefing wording check.
  - Owner: Claude E if needed. Reviewer: Codex B.
  - Status: conditional. Only open if frontend polish reveals confusing Agent
    Team wording that must be fixed in deterministic-template output. No new
    sources, roles, fields, runtime tools, or provider calls.

- `P31A-T6` - Founder demo polish smoke.
  - Owner: Claude A or Codex F. Reviewers: Claude B and Codex B.
  - Status: done 2026-06-23 by Claude A. Founder-demo polish smoke PASS across
    stock/ETF and cash-secured-put selected-account golden paths plus
    `/portfolio-context` adjacent hygiene; friendly labels render as primary copy,
    raw technical codes/ctx handles remain audit-only, explicit generation
    unchanged, saved report historical evidence unchanged, no unsafe wording/
    private-data exposure, no new overflow beyond tracked known issue,
    verification commands pass. Ran against the stable P30B synthetic seed
    (`seed_golden_path_demo.py --apply --reset-saved-outputs`) on a disposable
    `gp-smoke` DB (fresh isolated volume, destroyed with `down -v`) with no
    Skyframe fixture headers, exercising real routes/storage for one synthetic
    demo user only. Verified: Trade Review friendly scope-note labels as primary
    copy with raw codes only in `title`; demo-context dropdown leads with friendly
    labels (raw `ctx_demo_*` only as secondary `·` reference, per reviewed
    P31A-T3); save snapshot distinct from explicit Agent Team generation; Reports
    required explicit Generate with no auto-generation; saved report detail led
    with the specialist briefing, kept honest separate saved/generated timestamps,
    skipped public roles honestly, and read scope/evidence from the saved snapshot
    only; `/portfolio-context` showed zero raw `ctx_` in primary copy (handle in
    `title`/audit row only); no advice/order/execution wording (only the negated
    "Not an order recommendation" disclaimer); no `trrev_`/`svrev_`/private refs,
    balances, holdings, provider IDs, or payloads rendered; page-level horizontal
    overflow 0 at 1024/1280/1440 in light and dark on Trade Review, Reports detail,
    and `/portfolio-context`; console clean except known React Router v7 future-
    flag warnings. Verification commands all PASS: frontend typecheck, lint
    `--max-warnings 0`, build, check:skyframe-tokens, and `git diff --check`. No
    visual/copy behavior changed from the reviewed P31A-T3/T4 expectations, so no
    new Claude B/Codex B review was required. Deferred polish: pre-existing
    `/portfolio-context` right-column ("View") clip at <=1024 (already tracked,
    not worsened); raw `saved_review_artifact` source-type label still shown on
    Reports cards/detail (out of P31A-T3/T4 scope).

- `P31A-T7` - Founder acceptance and closeout.
  - Owner: Codex B and Codex A/founder.
  - Status: ready_for_founder_acceptance 2026-06-23. P31A-T1/T2/T3/T4/T6 are
    complete and reviewed/accepted as applicable. P31A may now proceed to
    Codex A/founder PASS/REVISE/BLOCK closeout.

### Phase 32A - Account Details Nickname Management And Redesign

- `P32A-T5` - Account Details nickname management UI (display-name editor).
  - Owner: Claude A. Reviewer: Claude B (visual/UX/accessibility/safety-copy);
    Codex B for contract/privacy.
  - Scope: collapsed "Edit display name" affordance plus compact inline
    Save/Clear/Cancel editor on the selected-account header. Edits PATCH
    `/users/{uid}/account-details/{account_reference}/nickname` with only the
    opaque `account_reference` + `{ nickname }`; the backend-returned candidate
    is the source of truth for the new label.
  - Status: review PASS 2026-06-24 by Claude B (visual/UX/accessibility/safety-
    copy); Codex B contract/privacy review PASS. Reads as Account Details
    identity management, not trade/order entry. Enter saves, Escape cancels,
    autofocus and the global focus-visible ring intact, errors use role=alert,
    input has aria-label. Hint "This changes only your Portfolio Copilot label."
    is safe and on-product; no advice/order/execution/guaranteed-return wording
    introduced. Claude A verification PASS: frontend typecheck, lint
    `--max-warnings 0`, build (only pre-existing >500 kB chunk advisory),
    check:skyframe-tokens, and `git diff --check`. Browser smoke not run
    (data-backed Account Details surface needs the local API token / real
    boundary); not closed in closeout for the same boundary reason.
  - Closeout 2026-06-24 by Claude A: all three review deferred-polish items
    implemented and re-verified (typecheck, lint `--max-warnings 0`, build,
    check:skyframe-tokens, `git diff --check` PASS) — focus returns to the "Edit
    display name" trigger when the editor closes (save/clear/cancel/Escape), the
    hint is associated to the input via `aria-describedby`, and the selected-
    account title has a long-label overflow guard (`overflow-wrap: anywhere`,
    `min-width: 0`). Presentation/a11y-only; no contract, request shape, or field
    usage change, so no Codex B re-review required.

- `P32A-T6A` - Account Details redesign (two-pane workspace, sticky tabbed top
  bar, pencil nickname affordance, restored brokerage-style position tables).
  - Owner: Claude A. Reviewer: Claude B (visual/UX/accessibility/safety-copy);
    Codex B high-level contract/privacy PASS.
  - Scope: two-pane account rail + selected-account detail; sticky top bar with
    local Dashboard/Analytics/Reports/Settings tabs (Dashboard live, the other
    three placeholders only); large Review scope block removed per founder
    feedback; nickname trigger reduced to a pencil-only icon with "Edit account
    name" tooltip; position tables restored to richer brokerage-style columns
    (gain/loss, gain/loss %, avg cost, cost basis) that render only when backend
    labels exist. Existing Account Details + nickname endpoints unchanged.
  - Status: review PASS 2026-06-25 by Claude B. Reads as a read-only trust/detail
    workspace, not order entry; no unsafe copy and no raw account/provider IDs.
    Implementer verification PASS: frontend typecheck, lint `--max-warnings 0`,
    build (existing Vite chunk advisory only), check:skyframe-tokens, and
    `git diff --check`. Browser smoke not run (data-backed surface needs the
    local API token / real boundary).
  - Follow-ups (non-blocking, for the next polish slice): complete or simplify
    the tab ARIA pattern (`role="tab"` without `aria-controls`/`tabpanel`/roving
    `tabindex`); move chrome accents off the green `--mp-live` status token to
    `--mp-accent` (teal/cyan) per Skyframe, since green also signals gain in the
    same pane; fix the PageHeader sub-copy that still references the removed
    Review scope block. Deferred polish: nickname pencil rest contrast (WCAG
    1.4.11), decorative profile avatar that looks interactive, backend-owned
    gain/loss tone. Placeholder tabs: keep for internal, disable as "Soon" before
    a founder demo. Scope visibility: compact per-account role chips already
    present, so no scope block needs restoring.

- `P32A-T6B` - Account Details demo-readiness polish (presentation/interaction
  only; same contract).
  - Owner: Claude A. Reviewer: Claude B (visual/UX/accessibility/safety-copy).
    No Codex B re-review: no contract, request shape, endpoint, read-field, or
    nickname PATCH change.
  - Status: review PASS 2026-06-25 by Claude B. Implements the three T6A Important
    follow-ups: header sub-copy no longer references the removed Review scope
    block; all nav/selection chrome (active nav, tab hover/underline, selected
    rail stripe/border/bg + hover, refresh button + hover, profile avatar,
    primary stat tile, nickname-trigger hover) moved off the green `--mp-live`
    status token to `--mp-accent` (green reserved for live freshness + positive
    gain); Analytics/Reports/Settings are honestly disabled "Soon" buttons with
    Dashboard as `aria-current`, replacing the incomplete tablist/tab ARIA.
    Nickname editor a11y intact (focus-return, aria-describedby, role=alert,
    aria-label, Enter/Escape, autofocus, focus-visible) — only its hover color
    changed. No unsafe copy, no raw IDs. Verification PASS: typecheck, lint
    `--max-warnings 0`, build (existing chunk advisory only), check:skyframe-
    tokens, `git diff --check`. Browser smoke not run (data-backed surface needs
    local API token / real boundary). Deferred polish (carried from T6A): nickname
    pencil rest contrast (WCAG 1.4.11), decorative profile avatar, backend-owned
    gain/loss tone.

- `P32A-T6C` - Account Details connected browser smoke.
  - Owner: Claude A. Reviewer: Claude B only if a later token-authorized smoke
    finds visual/UX issues requiring fixes.
  - Status: deferred/token-gated 2026-06-25 by Codex B. Connected browser smoke
    is token-gated by local API access and the real-data boundary; static
    verification and reviews passed, and no `.env`, secrets, local DB contents,
    broker payloads, screenshots with real data, or generated reports were
    inspected. A founder-authorized throwaway-token synthetic run may verify the
    Account Details page later, but it does not block closing the reviewed
    Account Details / nickname-management slice.

- `P32A-T7` - Selector/nickname integration closeout after backend landing.
  - Owner: Claude A. Reviewer: none required (verification/docs-closeout only;
    no code change).
  - Status: done 2026-06-25 by Claude A. Frontend selector/nickname integration
    confirmed coherent with the landed backend at commit `9c80de2`
    (PATCH `/users/{uid}/account-details/{account_reference}/nickname`, GET
    `/users/{uid}/review-account-candidates`, BrokerAccount.user_nickname
    migration `0021`). Verified field-for-field that the committed frontend
    (`d982dcb`) mirrors the backend `ReviewAccountCandidateRead` /
    `ReviewAccountCandidateListRead`; Trade Review consumes the candidates GET
    and submits only `review_account_selection.account_reference` (or mode
    `unselected`); the Account Details editor calls only the nickname PATCH with
    `{ nickname }`/null and treats the backend `display_label` as source of
    truth. No raw IDs/balances/holdings/positions/payloads rendered, no frontend
    financial computation, no advice/order/execution wording. Static
    verification PASS: typecheck, lint `--max-warnings 0`, build (existing chunk
    advisory only), check:skyframe-tokens, `git diff --check`. Connected browser
    smoke prepared, not executed; token-gated by local API access / real-data
    boundary. P32A Account Details / nickname-management slice closed by Codex B;
    any future token-authorized connected smoke is deferred follow-up only.

- `P32A-T8` - Real-source golden-path acceptance and remaining blocker map.
  - Owner: Codex B. Reviewer: Codex A/founder as needed for product acceptance.
  - Architecture reference:
    `docs/codex-b-architecture/PHASE_32A_REAL_SOURCE_GOLDEN_PATH_GAP_AUDIT.md`.
  - Status: done 2026-06-25 by Codex B. Confirms the landed backend (`9c80de2`)
    and frontend (`d982dcb`) make Account Details nickname management and the
    searchable review-account selector contract-ready, while the broader
    real-source golden path is not yet demo-closeout ready. Remaining blockers:
    token-authorized browser verification, disposable DB Alembic verification for
    migration `0021`, and a reviewed deterministic feasibility boundary for
    cash/collateral/current-position truth. Next task: P32A-T9 for Codex C to run
    disposable DB migration/test verification without real data.

### Phase 33A - Tool-Mediated Agent Team Prototype

- `P33A-T0` - Tool-mediated Agent Team prototype contract.
  - Owner: Codex B. Reviewers: Codex A/founder for product posture; Claude E for
    agentic design alignment.
  - Architecture reference:
    `docs/codex-b-architecture/PHASE_33A_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md`.
  - Status: done 2026-06-27 by Codex B. Opens Phase 33A as a tool-mediated,
    app-owned Agent Team prototype. Agents may request reviewed evidence through
    structured tool requests; the backend validates and executes tools, returns
    privacy-safe `ToolResult` envelopes, and freezes used results for
    reproducibility. LangGraph is deferred until durable multi-turn threads,
    resumable state, human interrupts, or complex dynamic loops become
    load-bearing. Initial tools are limited to existing saved evidence:
    `trade_intent_summary`, `portfolio_scope_context`,
    `deterministic_review_findings`, `broker_snapshot_freshness`,
    `market_quote_freshness`, `public_company_profile`, and
    `evidence_gap_inspector`. Deferred tools (`market_mood_context`,
    `economic_awareness_context`, `prior_report_context`, `public_news_events`)
    each require separate Codex B/source-rights review.

- `P33A-T1` - Tool registry, request shape, and ToolResult envelopes.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-28 by Codex C; Codex B-style review PASS after raw URL
    rejection blocker was fixed and re-reviewed. Implemented backend-only
    mock/offline `ToolRequest`, extended `ToolResult` envelopes,
    `default_tool_registry()`, `execute_tool_request(...)`, and the initial
    saved-evidence tools: `trade_intent_summary`, `portfolio_scope_context`,
    `deterministic_review_findings`, `broker_snapshot_freshness`,
    `market_quote_freshness`, `public_company_profile`, and
    `evidence_gap_inspector`. Verification PASS: `test_tools.py` 55 passed;
    agent_team/agent_eval 235 passed, 2 deselected; backend unit suite 193
    passed; `git diff --check` clean. No live providers, new sources, frontend
    changes, persistence, MCP, TradingAgents runtime, or LangGraph.

- `P33A-T2` - Planner, Evidence Auditor, and role behavior design.
  - Owner: Claude E. Reviewer: Codex B.
  - Design reference:
    `docs/claude-e-agentic/PHASE_33A_T2_PLANNER_AUDITOR_ROLE_DESIGN.md`.
  - Status: done 2026-06-28 by Claude E; Codex B review PASS. Adopted
    `USABLE_EVIDENCE_BY_ROLE = receivable tool evidence refs intersect citable
    report refs` as the binding planner/auditor map, with
    `ROLE_ALLOWED_EVIDENCE_KEYS` as the report-output ceiling. Planner and
    Evidence Auditor remain meta/run-state-only and out of `AGENT_TEAM_ROLES`;
    `options_structure_analyst` remains deferred; public roles are
    gap-reporting roles over T1's near-empty public tool set only through
    skipped/unavailable/warning states or citable availability refs, not
    unsupported prose; the auditor filters `evidence_gap_inspector` refs to each
    role's citable set and uses
    `liquidity_collateral_caveats` as the canonical ref. Structured plan,
    findings, auditor record, and citation graph stay run-state-only in T3 and
    reduce to existing markdown/evidence_refs/warning_codes; freeze remains T4.
    One bounded re-pass is allowed only for contradiction or fixable unsupported
    claims; leak/advice/invented-number failures drop fail-closed while the rest
    of the report survives.

- `P33A-T3` - First tool-mediated saved-report run.
  - Owner: Codex C + Claude E. Reviewer: Codex B.
  - Status: done 2026-06-29 by Codex C; Codex B narrow re-review PASS after
    citable-ref filtering blockers were fixed. Implemented deterministic
    planner -> backend-executed tools -> role findings -> Evidence Auditor ->
    Portfolio Manager synthesis over existing saved evidence only, using
    `provider_mode="tool_mediated_mock"` and the existing saved summary read
    model. Verification PASS: tool-mediated report tests 24 passed; combined
    tool/tool-mediated tests 74 passed; backend suite 1139 passed, 138
    DB-gated skips, 3 deselected; `git diff --check` clean. No live providers,
    frontend, new sources, web/MCP, TradingAgents runtime, LangGraph, or LLM
    provider calls.

- `P33A-T4` - Reproducibility freeze contract.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-29 by Codex C; Codex B narrow re-review PASS after
    nested URL-like keys inside frozen `summary_payload` were blocked
    schema-side. Added an optional `tool_run_artifact` freeze on
    `SavedAgentTeamSummaryRead` with the sanitized plan, tool-result envelopes,
    audited findings, auditor record, open questions, warning codes, and
    synthesis evidence refs. Legacy summaries without a freeze remain valid;
    blocked deterministic drafts do not attach the artifact. The freeze rejects
    raw/private IDs, buying power, raw payloads, URL keys/values, prompts,
    traces, unsafe wording, and generated metrics. Verification PASS: focused
    report/tool/agent suites 353 passed, 18 skipped, 2 deselected; full backend
    suite before the narrow blocker fix 1146 passed, 138 skipped, 3 deselected;
    `git diff --check` clean.

- `P33A-T5` - Tool-mediated Agent Team evaluation harness.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-29 by Codex C; Codex B review PASS. Implemented the
    offline deterministic eval harness for tool-mediated Agent Team reports with
    no schema/read-contract changes and no persisted/read-model eval output. The
    harness evaluates both `SavedAgentTeamSummaryRead` and frozen
    `tool_run_artifact` payloads; checks citation closure, usable evidence by
    role, unavailable/gap ref handling, PM synthesis refs, red-team hard-block
    drops, artifact reproducibility, deterministic-draft no-artifact behavior,
    byte-stable regeneration, and legacy-summary deferral. D1 discovery remains
    delta-measured/non-regression-gated rather than strict-improvement-gated.
    Verification PASS: tool-mediated eval tests 22 passed; agent_eval +
    agent_team 285 passed, 2 deselected; `git diff --check` clean.

- `P33A-T6A` - Report UI contract/design handoff for tool-mediated artifacts (planning).
  - Owner: Claude A. Reviewer: Codex B (read-contract/privacy).
  - Status: done 2026-06-29 by Claude A; Codex B read-contract/privacy decision
    APPROVED-TO-IMPLEMENT for a collapsed supporting-provenance "Tool-mediated
    evidence & audit" band when tool_run_artifact is present. Approved safe-subset
    frontend mirror only; summary_payload / raw scope / source_key / data_mode /
    latency / cost / contract_version / planner internals / auditor internals stay
    unmirrored or hidden. Mock output may render with a persistent
    "Demo evidence · mock tools" badge. Open questions, audited role findings,
    frozen timestamp, warning/caveat/finding-type humanization, and
    source-label-mapped citation/provenance chips approved. Frontend-derived
    auditor counts not approved; a backend-owned auditor_summary_label (later
    Codex C task, Codex B review) is required before any compact auditor summary
    is shown.

- `P33A-T6B` - Tool-mediated evidence & audit band (frontend implementation).
  - Owner: Claude A (Codex F backup). Reviewers: Claude B (visual/UX/safety-copy);
    Codex B re-review only if the UI needs additional fields, renders hidden
    fields, or adds auditor summary/counts.
  - Status: done 2026-06-29 by Claude A; Claude B visual/UX/accessibility/safety-
    copy review PASS. Additive collapsed supporting-provenance band rendered after
    ReportProvenance, gated on `summary.tool_run_artifact`. Reads as frozen,
    secondary, historical evidence (not live research); persistent "Demo evidence
    · mock tools" badge + per-source "Mock" tags while mock. Open questions and
    audited findings inline; Sources checked + audit metadata in a keyboard-
    operable `mp-disclosure` with a visible focus ring. Gaps (not_available
    sources, unavailable/empty finding sets) are muted, icon+text (not color-
    only), and never show citation chips. Codes humanized (raw only in `title`);
    citations map via `evidenceKeyLabel`. Renders the P33A-T6A safe-subset mirror
    only — no summary_payload / scope / source_key / data_mode / latency / cost /
    contract_version / planner or auditor internals, no derived auditor counts; no
    forbidden field rendered, so no Codex B re-review required. No advice/order/
    execution wording; tokens only. Verification PASS: typecheck, lint
    `--max-warnings 0`, build (existing chunk advisory only), check:skyframe-
    tokens, `git diff --check`. Browser smoke not run (data-backed Reports need
    `LOCAL_DEV_ACCESS_TOKEN` and the real-data boundary); this is deferred and
    does not block closeout. Deferred polish: neutral icon for not_available gaps;
    optionally surface finding/source caveat codes; optionally strengthen the demo
    badge for the founder demo.

- `P33A-Closeout` - Phase closeout.
  - Owner: Codex B. Reviewer: Codex A/founder for product validation.
  - Status: closed 2026-06-29 by Codex B. Phase 33A completed the mock/offline
    tool-mediated Agent Team prototype: reviewed tool registry and ToolResult
    envelopes, planner/role/auditor behavior, first saved-report run,
    reproducibility freeze, offline eval harness, and a safe-subset Reports UI
    for the frozen tool-run artifact. The result is an internal prototype over
    existing saved evidence and mock tools only. Real tool/source expansion,
    live LLM/provider use, Agent Console active runs, LangGraph, MCP, and
    browser smoke remain outside Phase 33A.

### Phase 35 - Real-Account Trade-Impact Working Prototype (ACTIVE)

- Architecture reference:
  `docs/codex-b-architecture/PHASE_35_REAL_ACCOUNT_TRADE_IMPACT_PROTOTYPE_CONTRACT.md`.
- Opened 2026-07-08 by Claude G after the founder rejected the P34A-T18
  structured report as not working. Founder's working-report definition:
  trade-centered, account-aware (real Fidelity account by nickname
  `Fidelity Individual`, buy-NVDA test trade), zero internal tokens in user
  prose, well-formatted markdown with titles/paragraphs/tables. Founder
  decisions D1-D6 recorded in the contract, including: derived percentages
  AND dollar values allowed in internal-prototype reports (identifiers/raw
  payloads still banned; real-derived-value artifacts stay local and
  gitignored); Claude G may view reports + derived values, never raw
  payloads; **all frontend work (incl. P34A-T14) is gated on founder
  acceptance of the backend prototype**; v1 exposure is sector-level (FMP
  constituent endpoints are 402 on the current tier - v2 look-through is
  founder decision P35-T7).
- `P35-T1` - Trade-impact methodology memo. Owner: Claude H. Reviewer:
  Claude G. Status: done 2026-07-08; review PASS as amended (blocker B1: SMH
  mislabeled "broad-market" in three narrative examples; wording fixed in
  place per the review spec). Decisions recorded: D-R1 (§2.4 categorical
  caveat = backend-rendered fixed text, never LLM-authored) and D-R2 (§5
  narrative = deterministic backend-rendered prose, outside the live-gate
  $/% ban; LLM-authored narrative is a separate v4 decision). Memo at
  `docs/claude-h-knowledge/P35_T1_TRADE_IMPACT_METHODOLOGY.md`; Codex C
  (P35-T3) and Claude E (P35-T4) build on it.
- `P35-T2` - Human-readable rendering + display-token ban. Owner: Codex C.
  Reviewer: Claude G. Status: done 2026-07-08; review PASS. Backend-owned
  display-label service with enumerated-vocabulary asserts and safe
  unknown-token fallback; all deterministic and frozen prose label-rendered;
  fail-closed `display_token_blocked` validator on user-visible prose via
  the existing fallback path; additive `display_label` in prompt fact rows;
  exporter founder-readable. Verification: 532 focused / 1344 full passed;
  diff-check clean. Deferred polish folded into T3: freshness "manual"
  label should read "manually entered"; FreshnessStatus completeness assert
  (eod_only/delayed/error/unavailable labels); shorter inline unknown-token
  phrase.
- `P35-T3` - Deterministic exposure engine v1 (sector-level, before/after,
  dollars + percentages, thresholds, narrative statements). Owner: Codex C.
  Reviewer: Claude G. Status: done 2026-07-08; review PASS after blocker
  P35-T3-F1 (narrative hardcoded SMH/VTI fund names, emitting false holdings
  statements for any non-golden portfolio; fixed to derive held ETF/fund
  symbols from reviewed positions). Golden worked example byte-identical;
  non-golden SOXX/IWM/MSFT+AMD regression proves no false SMH/VTI mentions.
  Pure Python; injected/default-off FMP company-profile classification
  (POA_MARKET_CONTEXT_MODE, 30-req budget, sanitized errors); ETF theme map
  + broad-market exclusion + coverage metric; funding regimes; reference-point
  thresholds; §7 ban patterns preserving descriptive "would add". Verification:
  engine 8, focused 496, full offline 1371 passed; diff-check clean. NOT yet
  wired into saved-report persistence — that is P35-T3a (privacy-reviewed
  positions->snapshot adapter + evidence freeze).
- `P35-T3a` - Exposure adapter + call seam. Owner: Codex C. Reviewer:
  Claude G (privacy). Status: done 2026-07-08; review PASS. PortfolioReviewContext
  + stock/ETF buy intent -> exposure-engine inputs -> display-only
  SavedEvidenceSectionRead sections; options bucketed as one asset-class line;
  missing market values -> caveats; buy-only guard; price basis genericized;
  fail-closed. Preview call seam computes but does not yet store (stopped
  before the freeze field per instruction). Privacy confirmed empirically:
  no account/user UUID, quantities, or source leak into the sections; only
  D2-approved derived dollars/percentages. Verification: focused 658, full
  offline 1376 passed; diff-check clean.
- `P35-T3b` - Freeze derived exposure sections into the saved artifact +
  readback wiring. Owner: Codex C. Reviewer: Claude G (privacy). Status: done
  2026-07-08; review PASS. Additive constrained derived_exposure_sections on
  SavedDeterministicReviewSummaryRead (only before_after_portfolio_impact /
  concentration_risk_drift, max one each, validated); route captures adapter
  output via a type-filtered callback and freezes it; from_saved_review_artifact
  uses frozen sections with fail-closed per-section re-validation (forbidden
  keys / secrets / internal tokens -> stub) and no recompute-on-readback
  (proven by a monkeypatch-to-raise test). Backward compatible (empty default
  -> legacy stubs). Verification: schema 110, focused 554, full offline 1382
  passed; diff-check clean. **The real-account backend path is now complete
  end-to-end: preview -> adapter -> engine -> frozen display sections ->
  readback.**
- `P35-T4` - Report contract v4: trade-centered markdown document. Owner:
  Claude E (design), Codex C (P35-T5 impl). Reviewer: Claude G. Status:
  design PASS as amended 2026-07-08. Decisions D1-D6 recorded: deterministic
  document composer (PM synthesis repurposed); live roles may not reference
  engine-derived portfolio values in any form (new portfolio-claim gate,
  digit+word) - D2 AMENDED to add comparative-magnitude vocabulary
  (double/triple/halve/most/majority/bulk/dominant/concentrat*) so the
  word-form channel is fully closed; numeric allowed-set unchanged;
  fundamentals/news live notes dropped; §7 ban list over all prose with the
  instruction-vs-description matcher; §2.4 overlap = T1-preferred backend
  fixed text (D-R1). Load-bearing gate facts verified in code (live gates
  run only on live_report_markdown; NUMBER_RE digit-only; token regex spares
  tickers). Important riders for the T5 prompt: engine must expose
  section-keyed narrative statements (not positional slicing); the §2
  risk-note example's "should" must not be encoded as acceptable.
- `P35-T5` - Report contract v4 implementation (document composer + gate
  extensions). Owner: Codex C. Reviewer: Claude G. Status: done 2026-07-09
  (PASS after P35-T5-F1 nickname fix). Structurally-frozen narrative groups,
  portfolio-claim + display-token gates, live-note v4 contract, honest-
  unavailable rendering; account nickname threaded fail-closed into
  scope_state. Verification: 652 passed, diff-check clean.
- `P35-T6` - Real-account gated run and founder acceptance read. Owner:
  Claude G with per-run founder authorization. Status: RUN 1 DONE 2026-07-09
  (mock mode, founder-authorized) - pipeline works end-to-end, NOT accepted.
  Blockers found: (A) `_resolve_portfolio_context` only serves synthetic demo
  contexts, so real synced positions never reach the exposure engine
  (criterion 2 fails); (B) assumed-external funding regime mixes two funding
  models (engine `portfolio_after = before + shortfall` vs `cash_after`
  unchanged) so After % column summed to 152.6% and two portfolio totals were
  quoted. Polish: doubled freshness labels, "1 are exchange-traded funds"
  grammar, bare not-reviewed list lines. Founder directives from the readout:
  per-role prompts are too thin (shared template + one sentence, 2 roles
  only); report verification runs must use live Gemini going forward (3.5
  Flash candidate); insufficient-cash detection should surface as a
  proceed-anyway warning (frontend banner later).
- `P35-T7a` - Funding-regime fix + shortfall warning + report polish. Owner:
  Codex C. Reviewer: Claude G. Status: done 2026-07-10 (PASS) - assumed-external
  funding unified on the full-purchase denominator with per-sentence basis
  naming + external-regime reconciliation test; funding_shortfall_detected
  caveat and honest shortfall warning; freshness-label, plural-grammar, and
  list-formatting polish.
- `P35-T7b` - Real-account portfolio context provider (selected review
  account, symbol+market-value-only seam). Owner: Codex C. Reviewer:
  Claude G. Status: done 2026-07-10 (PASS after T7b-F1) - lossy privacy seam,
  nickname-only single-account scope, sync-derived freshness; requested-but-
  failed resolution yields honest-unavailable exposure + account_snapshot_
  unavailable caveat with no membership claim (all three failure triggers
  tested offline). Verified 683 passed. Frontend PortfolioContextSource
  mirror ("account_snapshot") remains a queued frontend task.
- `P35-T7c` - Per-agent prompt contract p35-role-note-v2. Owner: Claude E
  (design) / Codex C (impl). Reviewer: Claude G. Status: done 2026-07-10
  (design PASS: D1-D5 ruled; impl PASS: verbatim shared core + four role
  blocks, exact-string static system-prompt registry validated at import,
  fail-closed unmapped-role raise, dormant fundamentals/news blocks,
  finish_reason truncation guard with nothing frozen; D3 wrong-direction-echo
  residual documented as eval tripwire). Do not amend the verbatim prompts.
- `P35-T7b-F2` - Selected-account freshness vocabulary fix. Owner: Codex C.
  Reviewer: Claude G. Status: done 2026-07-10 (PASS) - the T7b resolver path
  now validates sync freshness against the canonical broker_import
  DATA_FRESHNESS_STATUSES via preserve_canonical_sync_freshness (only that
  call site); cached/delayed flow to actionability as non-blocking
  manual_confirmation_required / analysis_only; unknown-with-successful-sync
  rescue and junk fail-closed kept; Account Details display path deliberately
  unchanged (its ReadinessSnapshotStatus read schema has no cached/delayed -
  extending it + frontend mirror queued with the PortfolioContextSource task).
- `P35-T6` RUN 2/3 - Real account + live Gemini runs. Status: RUN 2 2026-07-10
  blocked before any Gemini call (sync freshness vocabulary mismatch ->
  blocked_unknown_freshness; fixed by P35-T7b-F2). RUN 3 DONE 2026-07-10
  (founder-authorized): first full live end-to-end pass - real selected
  account snapshot reached the engine, funding-shortfall warning surfaced on
  real cash, semiconductor SMH+NVDA overlap surfaced, two live Gemini role
  notes generated and gated (gemini-3.5-flash attempted, rejected by API,
  fell back to gemini-2.5-flash), full_agent_report returned. NOT accepted
  yet - report defect list for P35-T9: (1) false "already above the 30.0%
  industry reference point before this trade" clause appended unconditionally
  in the engine's semiconductor-overlap statement (exposure_engine.py ~:852);
  (2) raw fact key atr14_usd rendered in the market-context table
  (FACT_DISPLAY_LABELS missing entry; unmapped keys should fail closed);
  (3) composer doubling "reviews stock buy review" (runner ~:1351);
  (4) lowercase sentence start after a period in the coverage sentence;
  (5) repetitive top-three fund note wording; (6) live note echoed a composed
  display label ("Market quote freshness: manual") because the envelope feeds
  the labeled string instead of the bare category; (7) near-duplicate
  freshness/as-of rows in the market-context table. Data finding for
  founder/Claude H: cash balance and the SPAXX money-market position appear
  as equal-value separate rows both counted in the portfolio total (likely
  the same swept dollars counted twice), which also understates available
  cash in the shortfall warning - needs a domain ruling on core-position
  dedup before the next run.
- `P35-T9` - Report defect fixes from T6 run 3 (list above), plus two agent-
  section items found on founder readout: (8) render each live role note with
  visible owner attribution and honest dropped/dormant text; (9) resolve the
  output-side token-scan collision - the auditor's private-leak scan includes
  bare "cash"/"holdings"/"positions", which the risk role's own prompt block
  guarantees it will say, so its live note is always generated then dropped
  (run-3 artifact confirms live_report_markdown empty + private_leak_blocked).
  Owner: Codex C. Reviewer: Claude G (token-scan ruling by Claude G).
  Status: done 2026-07-10 (PASS) - all ten items fixed and tested offline:
  fail-closed display labels, value-consistent threshold clauses,
  wording/table polish, bare envelope freshness categories, per-persona
  note attribution with honest absence lines, note-prose-only
  topic-vocabulary exemption with key-value disclosure guard, and
  SPAXX-class core positions treated as cash (founder ruling 2026-07-10;
  Fidelity documents uninvested cash is held in the core position) with
  three-branch mirror dedup, caveat, and reconciled totals. 596 passed /
  2 DB-gated skips.
- `P35-T6` RUN 4 - DONE 2026-07-10 (founder-authorized). First fully clean
  live run: every run-3 defect verified fixed in the generated report; both
  live role notes survived the gates and rendered with visible Technical
  Analyst / Risk Manager attribution; SPAXX deduped into cash with the
  honest core-cash note and reconciled totals; no raw keys, no false
  threshold claims; two live Gemini calls (gemini-3.5-flash still rejected
  by the API, fell back to gemini-2.5-flash). Only remaining warning:
  public_evidence_partial_coverage (expected - dormant news/fundamentals).
  Report delivered to founder for the four-criteria acceptance judgment.
  Deferred polish noted: summary headline bolded the core-cash note instead
  of the new-position statement; live notes quote copied numbers in single
  quotes. FOUNDER VERDICT 2026-07-10: NOT ACCEPTED. The acceptance bar for
  a working version requires ALL agent roles working - live gated notes,
  not dormant roles and not deterministic-only sections. No further live
  acceptance runs until Phase 36 activation completes; the next live run is
  P36-T5 with four live role notes.
- `P35-R1` - Research brief: output-side safety gating and auditor false
  positives in multi-agent LLM pipelines. Owner: Codex G (onboarded
  2026-07-10; charter at docs/codex-g-research/RESEARCH_ONBOARDING_PROMPT.md).
  Reviewer: Claude G. Status: done 2026-07-10 (review PASS). Brief at
  docs/codex-g-research/RESEARCH_OUTPUT_SAFETY_GATING_2026-07-10.md.
  Ruling: ranks 1-3 adopted as the durable post-T9 direction - typed
  privacy-match taxonomy with three outcomes (data-bearing hard block /
  vocabulary-only not leak evidence / ambiguous fail-closed drop) plus a
  synthetic minimal-pair + canary eval matrix scored at complete-report
  level; the P35-T9 bare-word exemption is the tactical first increment and
  is superseded by, not layered under, the typed taxonomy. Bounded re-pass
  deferred until the eval matrix measures base gate error rates. No learned
  component may ever be the sole layer between a note and display. The
  brief's incompatible list is binding for future gate design docs.
- `P35-T8` - Constituent look-through source decision. Owner: founder.

### Phase 36 - Working Version: All Five Agents Live

Working-version definition (founder, 2026-07-10, revised same day): all
five agent-team roles working as live gated agents - not deterministic-only
and not dormant. That is four analyst live notes PLUS a real live Portfolio
Manager role. Founder explicitly reopened the P34A PM boundary: the PM
becomes a gated live synthesis over the other roles' outputs and the
deterministic findings. Safety adaptation on record: PM live output is a
typed no-advice synthesis (evidence weighting, verification priorities,
trust assessment) - no ratings, no targets, no sizing, no horizons; every
number envelope-copied; deterministic composer keeps document authorship
and is the fail-closed fallback for the synthesis section. Deterministic
financial math and the no-advice rule are unchanged.

Reference model (founder-directed): ../TradingAgents role implementations,
studied read-only. Adoption analysis:
docs/shared/PHASE_36_TRADINGAGENTS_REFERENCE_ADOPTION_NOTES.md
(adopt/adapt/reject verdicts per role + source-rights delta table).

Founder autonomy directive (2026-07-10, governs all Phase 36 design):
TradingAgents is the golden standard for agent capability and autonomy.
Product agents get maximum permission, freedom, and resources inside hard
safety boundaries (read-only, privacy, source licensing, deterministic
math in code as invocable tools, no advice framing); in-depth analysis and
truthfulness verification are the agents' responsibility, with the auditor
as backstop. Prior micro-constraints (2-4 sentence notes, copy-only
numbers, blanket interpretation bans) are reclassified as adjustable
posture - see the REVISION section of the adoption notes doc. Team members
exercise their own judgment within this frame.

- `P36-T1` - TradingAgents reference study + adoption notes. Owner:
  Claude G. Status: done 2026-07-10 (doc above).
- `P36-T2` - Five-role domain design: per-role analysis charter, per-role
  evidence fact-groups and tool allowlists, per-role prompts (v3 prompt
  contract superseding p35-role-note-v2), and the PM live-synthesis
  design. Owner: Claude H (founder-assigned). Reviewers: Claude E
  (prompt/gate compatibility) + Claude G (architecture/safety), then
  founder. Status: design delivered 2026-07-10 (revised under the
  autonomy directive; docs/claude-h-domain/PHASE_36_FIVE_ROLE_DOMAIN_DESIGN.md).
  Claude G rulings 2026-07-10: Q-R1/A-1 CONFIRMED - D-R1
  identifier-privacy boundary stands (reviewed symbol + envelope-/
  calc-sourced portfolio values allowed in LLM surfaces, nickname only,
  identifiers/payloads never) with two conditions: (1) the replacement
  gates (F-5 provenance + F-6 identifier scan) must land in the SAME
  implementation slice that opens any magnitude-bearing surface - no
  interleaving; (2) internal-prototype posture only - any external or
  multi-user deployment reopens the decision (record in P36-T3).
  Q-R4 CONFIRMED - D-R5 budgets adopted as Tier 1 config (typical ~10
  LLM calls / ~20 tool requests, hard caps 19/40, wall-clock + token
  ceilings); PM keeps full calc-catalog access (narrowing it would
  recreate starvation; bounded by its 2/6 budget, allowlist validation,
  frozen-package-only reads, whole-block fail-closed), with pending-lane
  tools failing closed identically for the PM. Q-R7 CONFIRMED - C7-C9
  derived public-price statistics stay inside the existing FMP EOD
  approval (same class as the SMA/RSI/MACD/ATR indicators computed since
  P34A; own tested code over already-frozen licensed data; method/window/
  as-of labels required); P36-T3 records a confirmation line, no new
  source review. Claude E review done 2026-07-10: PASS
  (docs/claude-e-agentic/PHASE_36_GATE_PROMPT_COMPATIBILITY_REVIEW.md);
  decisions: Q-R5 sequential analyst loops for the working version
  (parallelism re-proposable only after P36-T6 measured quota headroom +
  chain-provider concurrency-safety review); Q-R6 one shared
  advice-boundary banned-class set (role dimension via per-role eval
  probes); gap flags F-12 (legacy scanner reconciliation, keep/retire
  disposition table) and F-13 (version-keyed freeze/readback - v2-frozen
  reports re-validate under v2 gates, v3 under v3, never mixed) added as
  binding gate work. Claude G arbitration 2026-07-10: FND-1 resolved as
  (a) - C15/C14 emit backend-computed humanized recency value labels
  ("93 days (one quarter) old"); uniform across lanes (absorbs Claude E
  deferred-polish 2); Claude H updates the charter excerpt in closeout.
  FND-2 CONFIRMED - bullish/bearish banned outright on all five surfaces
  even attributed (irreducibly forward-direction-encoding; descriptive
  saved-history terms like "downtrend" pass); deterministic word-class
  ban is also the only mechanically checkable form. FND-3 CONFIRMED -
  direction-inversion residual stays verification-over-prohibition with
  materiality now quantified: any inversion in a founder-facing
  acceptance-run report, or >=2% slip in the D3 eval family, triggers
  the pre-agreed promotion of a direction-adjacency check into F-5.
  Slice boundary (section 14) and F-12/F-13 ownership confirmed binding
  on Codex C slice planning. Next: founder read of design + review, then
  P36-T3 (Codex B).
- `P36-T3` - Activation contract + source-rights delta: FMP fundamentals
  lane (founder-approved, free tier), FRED data-series lane
  (founder-approved, free tier), PM live boundary amendment to the P34A
  contract, EDGAR operational constraints, free-tier budget/caching
  rules, plus the five P36-BIZ acceptance additions (standalone
  deterministic read contract; overall-verdict vocabulary in F-4;
  verdict-incapable PM fields as contract acceptance; backend-only
  future policy store; options mechanics fail closed to
  unable-to-verify). C4/C5 classified beachhead-critical for slice
  ordering; P36-T6 gains a covered-call acceptance scenario with honest
  not-fully-modelled states. Owner: Codex B. Status: contract drafted
  2026-07-11 at
  `docs/codex-b-architecture/PHASE_36_FIVE_AGENT_ACTIVATION_CONTRACT.md`.
  Claude G architecture review 2026-07-11: PASS with one binding
  clarification. Binding: §2's PM amendment supersedes a paraphrased
  "Phase 34A statement that the PM is never a live synthesis agent" that
  does not exist in that form - the deterministic-only-PM decision lives
  in PHASE_34A_T2 (Codex B Q2: "PM stays deterministic in M1") and
  PHASE_35_T7C §3e ("Portfolio Manager: stays deterministic - no PM live
  prose"; final_synthesis_authored_by: deterministic_template), and
  P34A-T0:221 already permits LLM "synthesis"; §2 must cite and explicitly
  retire those two decisions for v3 so the live PM leaves no dangling
  deterministic-PM contradiction (T7C §3e otherwise stays on the books and
  collides with P36-T5B). Verified faithful otherwise: all P34A/T6 hard
  boundaries intact; PM typed/verdict-incapable/whole-block fail-closed
  with deterministic composer authorship; FMP+FRED normalized-fields-only
  + freeze-once-per-package + free-tier honest-unavailable; EDGAR
  metadata-only + User-Agent/1rps; F-5/F-6/F-12 same-slice and F-13 with
  first v3 freeze (T4A); C4/C5 in the first calc slice (T4A); five-role
  T6 across stock-buy + covered-call with honest unable-to-verify; all
  five P36-BIZ acceptance additions present; Q-R7 confirmation line
  present; commercial news blocked; P37 policy backend-only; no Tier 1
  weakening. Deferred polish (3): (1) state whether the profile lane
  shares the FMP daily budget and whether the WITHOUT variant survives FMP
  exhaustion (Codex C smoke); (2) no per-day LLM budget constant exists
  (only per-run 19) - honest 429 fallback covers the working version, note
  it as a conscious choice; (3) confirm T4A lands atomically and any
  sub-split never opens a value-bearing surface before the F-5/F-6/F-12
  gate set. Codex B landed the §2 citation fix 2026-07-12: P36 explicitly
  retires the actual deterministic-PM decisions in P34A-T2 Q2 and P35-T7C
  §3e for v3 only, while v2 remains deterministic under F-13. The contract
  also resolves all three deferred operational notes: profile-only WITHOUT
  survives FMP exhaustion without an FMP call; no daily LLM cap is a conscious
  Phase 36 choice; and T4A is atomic at the value-bearing boundary. Next:
  issue the P36-T4A prompt to Codex C.
- `P36-T4A` - V3 calculation and safety foundation: C1-C5 (including
  beachhead-critical C4/C5), F-5 numeric provenance, F-6 identifier privacy,
  F-12 scanner reconciliation, F-13 version-keyed freeze/readback, and the
  deterministic standalone summary/check read contract. Owner: Codex C.
  Status: done 2026-07-12 (review PASS). C1-C5 use frozen saved evidence
  only; C4/C5 return unable-to-verify when broker coverage, collateral, or
  pending-order semantics are absent. F-5/F-6/F-12/F-13 ship atomically.
  Narrow F-5 re-review PASS: explicit identifier forms and five-plus-digit
  ambiguous spans defer to F-6; unmatched sub-five-digit numerals remain
  blocked by F-5. Atomic at the value-bearing boundary.
- `P36-T4B` - Free-tier source snapshot boundaries. Owner: Codex C.
  Status: done 2026-07-12 (review PASS). Added default-off, replay/injected
  FMP reported-statement and six-series FRED normalized snapshot lanes with
  approved-fact allowlists, labeled period/as-of metadata, daily budgets,
  named unavailable behavior, and package-frozen no-refetch readback.
  EDGAR now enforces the configured descriptive User-Agent, daily budget, and
  one-request-per-second operational limits. The FMP snapshot is intentionally
  excluded from role projection until T4C enables deterministic floors.
- `P36-T4C` - Deterministic Company + Events/Macro floors from frozen
  FMP/FRED/EDGAR; add C6-C15 wrappers where frozen inputs exist, incl.
  FND-1 backend-computed humanized recency value labels. Owner: Codex C.
  Status: in progress (Codex C started after T4B PASS). Claude G review +
  guardrails 2026-07-12 - progression verified in code (T4A gate
  foundation + C1-C5 real and faithful; C6-C15 + their display labels do
  not exist yet, so the gate-before-value-bearing-surface precondition
  holds). Guardrails that must be explicit before completion: (1)
  deterministic-only - tests assert zero provider run and no
  p36-role-analysis-v1 prompt emission during floor render (registering
  C6-C15 is not invoking them; live invocation is T5A); (2) every rendered
  C6-C15 fact_key is added to the approved display-label map
  (display_labels.py) - _render_values (deterministic_standalone.py:143)
  falls back to a generic reviewed label for unapproved keys, so no raw
  storage key becomes user-visible prose; (3) correct evidence_tier on each
  wrapper (C6-C10 and C11-C15 public, C1-C5 stay agent_safe), C11-C13 fail
  closed to source_rights_not_approved without a frozen lane, C7-C9 keep
  the existing FMP EOD approval with method/window/as-of labels, and C15
  filters its inventory to the requesting role's visible sections (built +
  tested in T4C though live invocation is T5A). Acceptance: honest-
  unavailable per lane incl. the profile-only WITHOUT variant when the FMP
  snapshot is absent (never blank, never fabricated); a forced-fallback
  test shows the standalone summary/check complete with all live blocks
  omitted; C6-C15 freeze additively under p36_tool_run_freeze_v1 and
  readback re-validates under the v3 set with zero source calls.
  Status: done - Claude G review PASS 2026-07-12. All three guardrails and
  the acceptance bar verified in code + tests: tiering structurally
  enforced (envelopes.py:435 blocks agent_safe->public allowlisting;
  :545 validates calc tier), C1-C5 agent_safe / C6-C10 + C11-C15 public;
  display-label allowlist complete with safe fallback; deterministic-only
  proven by test (provider_runs == (), no p36-role-analysis-v1/pm-synthesis
  strings, _live_provider_request monkeypatched to raise); C14 signs
  future events ("N days after the saved snapshot"); C15 role-filtered to
  public-only for every role (no before_after_*/scope_state refs); v2/v3
  freeze separation + no-rerun readback tested. FINDING (non-blocking for
  T4C, BINDING before T5A): 7 of 15 calc tools ship dark because the
  frozen evidence they need was never owned by a slice - C6-C10 (all
  Technical) are hardwired to frozen_eod_history_not_available (no frozen
  EOD OHLCV window; eod_history.py is groundwork only), and C12
  (period-change) + C13 (macro-series-change) have no available-path (FMP
  freezes one period, FRED one observation per series). T4C correctly
  renders these honest-unavailable, but at T5A the Technical analyst is
  substantially hollowed and the Fundamentals period-change / News macro-
  change (the founder-approved FRED lane's whole point) are dark. Resolve
  via T4D before analyst activation.
- `P36-T4D` - Comparison-window freezes (unblocks the dark calcs). Extend
  the frozen evidence so C6-C10, C12, C13 can compute: freeze an EOD OHLCV
  window (wire C6-C10 to read it), and extend the FMP statement freeze to
  >=2 fiscal periods (C12) and the FRED series freeze to >=2 observations
  per series (C13). All within already-approved lanes - EOD is inside the
  existing FMP EOD approval (Q-R7); multi-period FMP and multi-observation
  FRED are the same lanes with more rows per response, so no new
  source-rights review and no extra request budget (one request returns
  the window). Owner: Codex C. Reviewers: Codex B (light confirm: freeze
  shape within lane + budget) then Claude G. Status: done - Claude G
  hard-gate review PASS 2026-07-12. All 8 gate items verified in code +
  tests: (1) EOD OHLCV in the existing fmp_eod_history lane, default-off
  (mode="off"), injected client, per-run budget (max 2), package-build
  history cache never used at readback, raw payload normalized-away/errors
  sanitized; (2) FMP freezes top-2 fiscal periods from ONE response per
  statement (FMP_STATEMENT_FREEZE_PERIOD_COUNT=2; 3 calls, no retry loop);
  (3) FRED freezes top-2 observations per the 6 approved series from ONE
  request each (no new lane/substitution/fallback); (4) C6-C10/C12/C13
  read frozen sections only, compose+readback zero provider calls (test
  asserts frozen-before-composition + readback); (5) short/missing windows
  -> honest unable_to_verify with named caveats, no invented values;
  (6) _clean_text strips http/paths/>48c, unit/frequency/currency
  allowlisted, value labels are public OHLCV/statement/observation numerics
  only, no identifiers/payloads/URLs; (7) no live-role prompt/loop/PM
  emission added (grep clean; deterministic_standalone freezes
  provider_runs=()); (8) available-path tests cover C6-C10, C12
  (statement_percent_change), C13 (macro_absolute_change/direction). All
  new calc value-label fact_keys are in display_labels.py.
  Deferred polish (2): eod_ohlcv_bar has no display label (harmless today -
  public_market_context is consumed by calcs, never prose-rendered, and the
  read-contract summary is token-clean with the 260-bar section present;
  add a label or a render-skip assertion as defense-in-depth);
  _statement_records/_fred_observations can raise NameError on a
  non-Mapping/non-Sequence payload from a malformed live client - init
  rows=() so it degrades to a clean unavailable section (live-only, fails
  closed by crashing, no leak).
- `P36-T5A` - V3 analyst activation. APPROVED TO START 2026-07-12 (Claude
  G). Split into a proving slice then a fan-out, since this is the first
  live-LLM-prose surface and the repo rule is smallest-reviewable-first:
  - `P36-T5A-1` - Bounded live-analyst loop + full v3 gate stack proven on
    ONE analyst: the Risk Manager (always runs; carries portfolio
    magnitudes via C1-C5, so it exercises F-5 provenance + F-6 identifier
    privacy hardest - the highest-stakes surface to prove fail-closed
    first). Activate p36-role-analysis-v1 for risk; bounded mediated
    plan-then-write loop (max 3 iter, iter-3 force-final, two-refusal early
    stop); apply F-4 (five advice classes) + F-7 + F-8 + F-9 + F-10 + F-11
    to the live section (F-5/F-6/F-12/F-13 already landed in T4A, now
    applied to the new prose surface); whole-section fail-closed to the
    T4A-T4D deterministic floor; per-role slice of the 19/40 Tier 1 caps;
    truncation guard; sequential execution (no concurrency;
    ChainedLLMProvider stays single-threaded). Role-block wording finalized
    WITH Claude E (design section 10); attribution-marker constant shared
    prompt<->gate. Evals (synthetic, complete-report scoring): provenance
    seeded-error, advice-boundary minimal pairs, What-was-verified
    boilerplate canaries, budget/loop families. Owner: Codex C. Reviewers:
    Claude E (agentic/loop/prompt) + Claude G (architecture/safety).
    Status: prompt issued 2026-07-12. Claude G attribution-constant ruling
    2026-07-12 (item 7 of Claude E's arbitration relay): the one-shared-
    constant coupling (P36_ATTRIBUTION_MARKERS imported by both prompt
    assembly and the F-4.6 gate + tests) is CONFIRMED and orthogonal to
    FND-2 (no conflict). BUT the pinned 7-member set is narrower than
    Claude E's own section 6.2.6 illustrative list and than "lenient by
    design" warrants, and misses two charter-instructed attribution forms:
    "per the <tool> calculation" (design section 5 Risk excerpt "Per the
    exposure calculation, ...") is NOT substring-matched by "per the
    calculation"; and "the saved <noun> show" (design section 6 "the saved
    statements show ... margin compression"; "the saved series/prices") is
    NOT matched by "the saved evidence". Because F-4.6 is fail-closed
    (missing marker on a trigger sentence drops the whole section) and the
    attribution check never excuses banned content (classes 1-5 + F-5 bind
    independently), the correct bias is broad/lenient. BINDING before
    T5A-1 wires F-4.6 (owner Claude E): widen "per the calculation" ->
    "calculation" and "the saved evidence" -> "the saved" (or restore the
    broader "per the" / "the saved" forms). One-line change in the single
    shared constant; Claude G verifies in the T5A-1 review.
    Claude G prompt-contract-collision ruling 2026-07-12 (T5A-1 blocker):
    verbatim CORE-B names the advice vocabulary it forbids ("no buy, sell,
    hold ... price targets, time horizons"), tripping the prohibited-phrase
    scan in register_static_system_prompts() and validate_llm_provider_
    payload(). RULING = Option A, a narrow exact-static-system-prompt
    exemption: exempt the prohibited-phrase scan ONLY for a segment that is
    (a) an exact full-string match to a reviewed entry in the static prompt
    registry AND (b) in the system-message role; retain forbidden-key,
    private-token, and secret-like scans on that segment; leave ALL output
    scans and ALL dynamic (user/assistant/envelope) segment scans unchanged
    - the payload validator must scan SEGMENT-WISE and exempt only the exact
    static system segment; no role-based bypass, no substring/prefix/
    whitespace-normalized match. Rationale: the prohibited-phrase scan is an
    output/dynamic-content control over-applied to reviewed static
    instruction text; A fixes the false positive while F-4 (output
    advice-boundary) and the output prohibited-phrase scan remain the
    primary, unchanged enforcement. B rejected (paraphrasing CORE-B weakens
    steering + is perpetually fragile). The exempt allowlist IS the reviewed
    v3 static-prompt registry; adding an entry requires Claude E + Claude G
    prompt review, never an ops knob. Owner: Claude E implements + 6-case
    test matrix (exact CORE-B registers; same vocab in OUTPUT still blocks;
    same vocab in a DYNAMIC segment still blocks; near-match/substring/
    prefix static prompt NOT exempt; forbidden-key/secret-like scans still
    fire on the static prompt; a non-registry system message with the vocab
    NOT exempt). Codex B records the narrow amendment to the static-registry
    contract. Generalizes to all reviewed v3 static system prompts (Risk
    now; analysts at T5A-2; PM at T5B). Claude E adopted 2026-07-12 as the
    single recorded spec (PHASE_36_T5A1_RISK_ROLE_BLOCK.md section 4);
    exemption + 6 tests specified, NOT yet implemented (Codex C's slice) -
    Claude E confirms all green at the T5A-1 review, not before.
    Refinements: (i) the exempt unit is each FULL ASSEMBLED (role,
    prompt_version) system prompt, not the shared CORE-B fragment - so each
    role's assembled prompt is its own reviewed exempt entry, and the same
    path covers p36-pm-synthesis-v1 unchanged; (ii) Claude G DECLINES the
    optional registration-time CORE-B-strip as a 7th test - the human
    prompt-review gate on the exempt allowlist is the correct guarantee that
    an exempt string is a genuine prohibition instruction, a mechanical
    negation/strip heuristic would risk re-introducing the very false
    collision we are removing, and output + dynamic scans + F-4 remain
    primary regardless of instruction phrasing; keep exactly one mechanism.
    Revisit only if the exempt allowlist ever grows beyond a small
    hand-reviewed set or becomes programmatically generated. Final
    ratification at the T5A-1 review.
    Status: done - Claude G review PASS 2026-07-12. All five areas pass
    (prompt/gate mechanics, bounded-loop safety, numeric/identifier
    provenance, deterministic fallback, frozen-readback). Verified in code +
    tests: attribution constant widened per the item-7 ruling ("per the
    calculation"->"calculation", "the saved evidence"->"the saved"); Option
    A exemption is narrow and correct - register_static_system_prompts()
    runs the secret + private-token scans even AT registration, only a
    structured ReviewedStaticSystemPrompt earns the phrase exemption,
    exact full-string + system-role only, and ignored_plain_tokens is a
    4-token allowlist (cash/holdings/positions/threshold) that still blocks
    every compound/private/secret token (find_forbidden_string_values
    iterates the full list minus the 4). Subagent-caught overbroad
    private-token bypass CONFIRMED fixed. My six-case exemption matrix is
    green (test_p36_static_registry_* + test_p36_reviewed_static_system_
    prompt_registers). Loop: max 3 provider calls (min with global 19),
    C1-C5/C15 allowlist, opaque calc IDs / no free numeric args, tool/token/
    90s wall-clock caps, two-refusal early stop, iter-3 force-final,
    whole-section _live_provider_fallback on every failure path; F-4
    suitability-vs-descriptive minimal pair + whole-section provenance/
    privacy/structure/grounding drop tests green; freeze/readback re-run
    nothing. WATCH-ITEM (non-blocking, for P37): "threshold" is the one
    ignored plain token with a user-policy dimension - today it is generic
    deterministic reference-point vocabulary and forbidden-KEY
    (account_specific_threshold) + dynamic scans still catch user thresholds,
    but re-examine before P37 so no user threshold value can ride a static
    prompt; consider rewording to drop it from the ignored set.
    Claude E cross-review 2026-07-12 also PASS (five dimensions, code-read);
    surfaced F1, a real spec-vs-impl divergence my review under-inspected:
    F-6's ambiguous-identifier branch (_identifier_privacy_flag /
    _ambiguous_identifier_context, v3_value_gates.py:340-359) drops ANY
    >=5-digit number near identifier vocab INCLUDING F-5-provenance-matched
    values, but Claude E's review section 5 intended only NON-matched runs
    to drop. Fail-closed/safe, but over-drops legitimate Risk sections that
    state a >=5-digit cash/exposure figure near a word like "account" - it
    will bite the founder's six-figure account at T6. Claude G ruling: fix
    as a discrete change (T5A-1b) that lands + is reviewed BEFORE the T5A-2
    fan-out (not pre-T6 = Claude E's lean b, not folded into T5A-2 = c),
    because it is a divergence in the SHARED reusable gate the proving slice
    exists to validate, it most affects T5A-1's own Risk surface, and
    fixing-before-fan-out propagates a correct gate + regression probe to
    all four analysts instead of re-baselining their evals later. T5A-1
    itself remains PASS (safety-correct); this is the one condition on it.
  - `P36-T5A-1b` - F1 fix: thread the F-5 allowed-set into the F-6
    ambiguous branch and skip provenance-matched tokens; the explicit/
    masked/UUID/provider/compound/secret hard-blocks (v3_value_gates.py:
    349-356) stay UNCHANGED (a provenance match never excuses an explicit
    identifier form, so no identifier hole opens) + regression eval
    (matched >=5-digit-near-vocab kept; unmatched dropped; "account number:
    N" hard-blocked regardless of provenance). Also fold Claude E's F2
    (heading word pollutes the attribution check) and F3 (execution-phrase
    graceful-drop vs whole-report fallback consistency). Owner: Codex C.
    Reviewers: Claude E + Claude G. Status: DONE - Claude G architecture/
    safety re-review PASS 2026-07-13 (verified in code + ran the affected
    gate tests, not on reported counts): F-6 residual now defers to F-5 via
    `and not _numeric_allowed(...)` at v3_value_gates.py:360 (matched
    survives, unmatched fails closed); the explicit hard-blocks at 349-356
    remain unconditional and ordered BEFORE the residual, so a provenance-
    matched value inside an explicit "account number: N" form still hard-
    blocks (test_p36_f6_ambiguous_identifier_residual_defers_to_f5_provenance
    case 3 - provenance cannot launder an identifier); F2 heading exclusion
    at 372-374 (test uses a heading containing a real interpretation
    trigger); F3 execution phrases handled once at provider-output
    validation with whole-section fallback, F-4 carries no execution-phrase
    list and the test asserts live_advice_boundary_dropped is ABSENT. No
    prompt/role/source/loop/schema/frontend/live-provider change. NOTE:
    could not isolate the diff via git (whole Phase 36 arc still uncommitted;
    v3_value_gates.py is untracked) - scope confirmed by function inspection.
  - `P36-T5A-2` - Fan-out to the three public analysts (Technical C6-C10,
    Fundamentals C11-C12, News C13-C14) on the proven machinery; adds the
    C13 series-misattribution eval probe (C13 returns all six series'
    values in one result under generic fact_keys
    macro_current_value/macro_series_label, so F-5 numeric match alone does
    not bind a cited value to the right series - the eval must catch a role
    citing CPI's number against the yield-curve label). Owner: Codex C.
    Status: CLEARED TO START 2026-07-13 (T5A-1b PASS unfroze it). Then:
    each new role's assembled prompt becomes its own
    ReviewedStaticSystemPrompt exempt entry requiring a Claude E + Claude G
    prompt review; the C13 series-misattribution eval is required; and
    strengthen F-11 grounding for the public analysts (Claude E's F4 -
    grounding matters more for news/fundamentals than for Risk). Reviewers:
    Claude E + Claude G. T6 stays frozen.
  - `P36-T5A-2-PROMPTS` - Claude E deliverable
    PHASE_36_T5A2_PUBLIC_ROLE_BLOCKS.md (three verbatim role blocks + SHAPE,
    p36-role-analysis-v1). Claude G prompt review 2026-07-13: PASS. Verified
    in code: p36-role-analysis-v1 in _P36_VALUE_BEARING_PROMPT_VERSIONS
    (contracts.py); every attribution phrase the blocks teach resolves to a
    P36_ATTRIBUTION_MARKERS substring (no block teaches a phrase F-4.6 drops);
    blocks steer hard off each role's characteristic advice class + enforce
    honest-unavailable/no-carryover. F-8 variant/symbol-heading contract
    (§4.2) and C13 series-binding-as-F-11 (§4.3) CONFIRMED as intended gate
    mechanics, with two conditions: (a) the C13 series-label alias set is a
    reviewed constant (Claude E + Claude G governed), not free text; (b)
    same-sentence label+numeral adjacency is the accepted fail-closed boundary
    and gets an eval case documenting a correctly-attributed-but-split-across-
    sentences drop. Deferred-polish watch-item: monitor drop-rate at the 400-
    word F-8 ceiling (zero headroom above SHAPE target).
  - `RULING-T5A2-1` (yield document-scan collision, §5.1) - APPROVED: Option
    1 (narrow reviewed-label scrub). Verified premise in code:
    report_output_safety.py:207 bans bare `yield|annualized|
    return on collateral`; _reject_report_phrases (231/238-245) runs over the
    assembled document with NO value-bearing exemption (that exemption only
    gates validate_llm_provider_output at 226), so a "yield" in an approved
    FRED label drops the WHOLE report; source_snapshots.py:284-285 confirms
    two approved labels ("Ten-year Treasury yield", "Yield-curve spread")
    carry the token; the scrub mirrors the existing
    REPORT_ALLOWED_NEGATED_DISCLOSURES loop (240-241). Binding conditions:
    (1) scrub set = the EXACT reviewed FRED display strings sourced from the
    FredMacroSeriesDefinition constant (single source of truth - not the
    doc's paraphrase), append-only, Claude E + Claude G governed like the
    static-prompt registry; (2) scan-only (never mutates persisted/projected
    report text); (3) residual bare-`yield` still drops ("dividend yield",
    "high-yield") - proven by test; (4) tests: WITH-variant naming both yield
    labels passes, non-label yield drops, scrub rescues no other prohibited
    pattern adjacent to a label. PRINCIPLE (generalizes the CORE-B/Option-A
    ruling): carve out ONLY contract-forced verbatim tokens the model must
    emit to name a series correctly; model-CHOSEN avoidable words
    ("annualized", "dividend yield") stay banned + steering/eval-caught.
    ADDITIVE CONDITION (Claude G): before EACH pending lane activates (FMP
    fundamentals AND FRED macro), audit that lane's FULL forced display-label
    set against the FULL P35_PROHIBITED_REPORT_PATTERNS - not just the two
    yield labels - so an analogous FMP-label collision (e.g. an "annualized"
    growth label or a "return on ..." ratio label) is caught pre-activation,
    not rediscovered live. Sequencing: this ruling gates the FRED WITH-variant
    activation, NOT T5A-2 (News ships WITHOUT-variant first).
  - `P36-T5A-2` IMPLEMENTATION - Claude G architecture/safety review
    2026-07-13: PASS. Verified in code + ran the affected gate/eval subset
    offline (not on reported counts). Technical fully live (C6-C10+C15);
    Fundamentals/News WITHOUT-variant live; C11/C12 fail closed
    (source_rights_not_approved / required_statement_facts_not_available),
    C13 fails closed (macro_series_history_not_available). Both my prior
    conditions landed: (a) FRED_MACRO_SERIES_DISPLAY_ALIASES is derived from
    the FRED_MACRO_SERIES constant ("no free-text alias can authorize a macro
    number"); (b) the split-across-sentences drop is an explicit eval
    (test_p36_c13_requires_same_sentence_governed_series_label...). C13
    _macro_series_grounding_flag: swap -> GROUNDING_FLAG, correct pairing ->
    None. F-8 binds the title to the frozen symbol; word floors 125/90/90 per
    §4.2d. F-12 phrase-ban fix VERIFIED SOUND: REPORT_PROSE_KEYS =
    {claim_text, final_synthesis_markdown, live_report_markdown,
    section_markdown, summary_markdown} is a superset of USER_VISIBLE_PROSE_
    KEYS (empty gap), so every model-generated prose field stays scanned;
    only frozen structured metadata is excluded; test proves generated prose
    still fails while a frozen method_label passes; content_markdown is a
    separate thread-message subsystem, not in this payload.
    FINDING-1 (recommended, tiny, non-blocking): the F-12 change inverts the
    phrase scan from denylist-by-default (repr of whole payload) to allowlist
    (REPORT_PROSE_KEYS). Currently complete, but fail-OPEN for any FUTURE
    prose key not added to the set. Add a guard test asserting
    REPORT_PROSE_KEYS covers USER_VISIBLE_PROSE_KEYS so a later omission
    can't silently drop a field from the ban. Owner: Codex C, next touch.
    FINDING-2 + FINDING-3 -> FRED-activation checklist (dormant WITH-variant
    only, NOT T5A-2 blockers): (2) _macro_series_grounding_flag scans the
    closing evidence table, but rows aren't sentence-delimited so the whole
    table is one segment where all labels are present, diluting the
    same-sentence binding for table cells (F-5 still constrains values);
    split table rows per-segment or add a mislabeled-row eval when the FRED
    lane activates. (3) confirm the bound fact_key set {macro_current_value,
    macro_prior_value, macro_absolute_change} covers ALL value-bearing macro
    fact_keys C13 emits (e.g. any percent-change field), else a misattributed
    change value is unbound (still F-5-constrained). Claude E (gate owner)
    adjudicates 2 + 3 at FRED activation, with RULING-T5A2-1 + the label audit.
  - `P36-T5A-2` DUAL-PASS ACCEPTED 2026-07-13 - Claude E (gate/eval) PASS +
    Claude G (architecture/safety) PASS. Verification complementarity: Claude
    E code-read only and relied on the reported 776/1496 counts; Claude G
    re-executed the affected gate/eval subset (10 passed offline) - so the
    affected tests are confirmed green AND the logic confirmed by two readers.
    CONSOLIDATED PRE-ACTIVATION CHECKLIST (merges both reviewers; all gate the
    FMP/FRED activations under RULING-T5A2-1, none block T5A-2):
    * [pre-FMP] Claude E F1 (Claude G confirmed in code, v3_value_gates.py:
      513-516): Fundamentals 2nd heading keys on calc_financial_ratios (C11)
      availability ALONE, so once FMP is live a statements-reviewed /
      C11-unavailable / C12-available section renders "Reported record" but the
      gate expects "What was reviewed" -> false drop. Fix: key on the statement
      SNAPSHOT presence (the semantic source: "reported record" = statements
      were in evidence), not on any single calc's availability. Dormant now
      (both C11/C12 fail closed pre-FMP).
    * [pre-FRED] Claude E F2 + Claude G FINDING-3 (same function
      _macro_series_labels_by_value): label->value pairing is POSITIONAL
      (assumes the C13 envelope orders the label row before its value rows per
      series) AND binds only {macro_current_value, macro_prior_value,
      macro_absolute_change}. Pin the envelope row-grouping contract (or bind
      per explicit series structure) and confirm the bound fact_key set covers
      ALL value-bearing macro fact_keys before FRED. Decimal-keyed shared value
      (two series same number -> either label satisfies) = minor, agreed.
    * [pre-FRED] Claude G FINDING-2 vs Claude E F3 are COMPLEMENTARY, both on
      the C13 binding, both dormant: FINDING-2 = UNDER-enforcement (the
      non-sentence-delimited closing table collapses to one segment, all labels
      present, so a mislabeled table cell passes); F3 = OVER-enforcement (a
      coincidental numeral equal to a macro value is forced to carry a label ->
      minor fail-closed over-drop, = the drop-rate watch-item). Adjudicate both
      when splitting table rows per-segment at FRED activation.
    * [T5A-2-adjacent, NOT a WITH-variant item] Claude G FINDING-1 (unique to
      the architecture lane): the F-12 phrase scan is now an allowlist
      (REPORT_PROSE_KEYS), fail-OPEN for any future prose key. Add the one-line
      guard test asserting it covers USER_VISIBLE_PROSE_KEYS. Owner: Codex C,
      next touch (does not wait for FMP/FRED).
- `P36-T5B` IMPLEMENTATION (commit aa146a2, LOCAL/unpushed) - Claude G
  architecture/safety review 2026-07-13: **PASS**. Verified in code + ran the
  PM/scope subset offline (60 passed), not on reported counts. BOTH open
  conditions landed: (1) design condition - _pm_advice_boundary_flag implements
  a REAL subject-noun boundary (_PM_TRADE_SUBJECT_FRAME_RE: trade|position|
  setup|entry|idea|purchase|sale|order + evaluative verb) plus directional
  leans, entry verdicts, tension-resolution, freeform trade-directives; evals
  parametrize exactly the soft verdicts I demanded ("the trade holds up well",
  "the setup looks solid", "the evidence points the right way") and assert
  ADVICE_BOUNDARY_FLAG in BOTH freeform fields; end-to-end pipeline test proves
  a soft verdict -> deterministic_template + pm_synthesis None (no partial
  render). (2) RULING-T5B-2 - P36_F6_VOCABULARY_ONLY_TOKENS is consumed ONLY by
  contracts.py; F-6 (_identifier_privacy_flag/_ambiguous_identifier_context/
  _IDENTIFIER_CONTEXT_RE/_ACCOUNT_NUMBER_RE) is UNTOUCHED = behavior-preserving;
  exemption gated on content_kind="p36_pm_accepted_sections" and REJECTED
  elsewhere ("restricted to the PM synthesis request"); exact-7 membership
  guard test present; non-vocabulary scans retained in the PM payload.
  VERIFY-NOT-RECOMPUTE structurally enforced: pm_calculation_matches_surfaced_
  values admits a PM calc only if EVERY value it returns was already surfaced,
  and the runner filters PM calc results through it BEFORE validation - a
  divergent re-run is never admitted, so the PM cannot originate a figure.
  Founder focus list all verified: static registration; sequential PM-LAST
  (call order asserted, 4-role and 5-role); no public access to C1-C5 (C1-C5 =
  agent_safe + role_allowlist=portfolio_roles, untouched); PM payload privacy;
  frozen artifact/readback NO-RERUN (provider call count unchanged across
  readback; missing PM run -> ValueError); additive schema; deterministic
  fallback (both gate-drop and unavailable lines). Doc-parity RESOLVED (commit
  includes both T5A2 + T5B design memos).
  FINDING-1 (non-blocking, doc-truth): registry grants the PM C6-C10 (technical
  calcs) in addition to C1-C5, but design §5 documented only C1-C5. SAFE - every
  PM calc passes the match-filter, so the wider surface cannot originate figures
  - but code and reviewed design disagree. Record the PM's actual calc surface
  in §5 (or narrow the grant if C6-C10 verification was unintended).
  FINDING-2 (carried from T5A-2): the REPORT_PROSE_KEYS allowlist guard test is
  still missing. PM prose IS covered (final_synthesis_markdown is in the set, so
  the P35 document scan reaches it), but the set stays fail-open for a FUTURE
  prose key. Still a one-liner; more valuable each slice.
  Next: Claude E gate/eval lane, then push the checkpoint (aa146a2 is local),
  then T6 - the five-live-role acceptance run, FROZEN pending founder per-run
  authorization.
  **F-B1 (Claude E, acceptance pass) - Claude G CONCURS: BLOCKED, not
  deferred.** Verified by probe: "the filing is not material" / "the release is
  already priced in" / "the tone was hawkish" / "the rate cut is dovish" all
  PASS the PM gate but DROP on news_analyst - _F4_NEWS_INTERPRETATION_RE binds
  only when role_name=="news_analyst" and _pm_advice_boundary_flag never passes
  it. The same vocabulary is banned on the surface that REPORTS the record and
  permitted on the surface that SYNTHESIZES it; News cannot emit these, so the
  PM would have to ORIGINATE them. Nothing else catches it (not an F-4.6
  interpretation trigger; no F-11 citation/number; absent from the P35 doc
  scan). Blocking, not deferring, because T6 is the founder's real-account run
  and shipping a known verdict-vocabulary gap into the run he personally judges
  is backwards; the patch is small. Scope gap in Claude E's design §4 ("five
  shared classes"), faithfully implemented - not a Codex deviation; Claude G's
  design review missed it too.
  **STRUCTURAL FIX (Claude G, generalizes the patch):** the PM advice gate must
  inherit the UNION of every role's advice vocabulary - shared five classes PLUS
  every role-specific pattern - not just the shared five. The PM synthesizes
  over all five roles, so any verdict vocabulary banned on ANY analyst must be
  banned on the PM. Wire it as a union so future role-specific patterns
  auto-inherit; the news-class pattern is the instance, the union is the
  invariant. This is the 2nd PM advice-surface gap (after the subject-noun
  condition) - the invariant closes the class.
  **"material" over-block discriminator (Claude G, answering Claude E ask 2):**
  anchor the news-verdict ban to the SUBJECT, exactly as the trade-verdict ban
  is anchored (§4a principle, reused). priced-in/dovish/hawkish/rate-cut/
  rate-hike have NO legitimate evidence-weighting sense -> unconditional (agree
  with Claude E). material/materiality/immaterial is the ONLY one with a
  legitimate on-charter sense and it is a core one: the PM's actual job includes
  saying which evidence matters. So: BAN when the subject is a public-record
  noun (filing/release/event/announcement/disclosure/headline/report-as-record)
  -> "the filing is not material" = a news verdict, off-charter. PERMIT when the
  subject is an evidence noun (evidence/section/input/finding) -> "the company
  section is not material to this reading" = evidence-weighting, ON-charter
  (literally field 1). Leave attributive/nominal uses alone ("source material",
  "the material inputs"). Do NOT ban bare \bmaterial\b. Rationale: an
  over-blocking pattern would systematically drop the PM's legitimate
  evidence-weighting sentences to the deterministic floor and push the model to
  vaguer phrasing to evade the gate - a gate that fires on the role's core job
  is not fail-closed, it is mis-aimed.
  Eval must lock BOTH directions: news-verdict FAIL canaries AND
  evidence-weighting "material" PASS canaries. Close-out: Codex C patches ->
  Claude E re-verifies -> Claude G re-runs the probe (incl. the 3 legit-use
  cases) and signs off -> T5B accepted. T6 frozen.

  **F-B1 PATCH RE-REVIEW (Claude G, 2026-07-14, working tree on aa146a2):
  BLOCKED.** What LANDED CORRECTLY: (a) the union invariant is exactly right -
  `_F4_ROLE_SPECIFIC_PATTERNS` registry + `include_all_role_specific=True` on
  the PM; behaviorally verified both news patterns now DROP on the PM, and
  future role-specific patterns auto-inherit. (b) F-B1 itself is closed on the
  PM: all 4 FAIL canaries DROP (were `pass` at aa146a2), all 3 legit "material"
  uses still `pass`. (c) The test diff is purely additive - 11 new tests, the
  exact 1551->1562 delta, no existing canary edited or deleted.
  **G-FB1-1 (BLOCKING - live-surface regression, out of scope for F-B1).** The
  patch deleted bare `material(?:ity)?` from `_F4_NEWS_INTERPRETATION_RE` and
  replaced it with a subject-anchored frame for ALL roles, not just the PM. A/B
  probe (aa146a2 vs working tree) shows 13 behavior drifts, **all on
  news_analyst, all in the loosening direction, zero on any other role**. News
  is LIVE and accepted since 9cc4899, and is one of the five roles in the T6
  real-account run. Newly permitted on News: "The impact is material." / "The
  news is material." / "The 8-K is material." / "The guidance update is
  material." / "It is material." / "The 8-K was filed on 2026-02-02. This is
  material." - every one of these DROPPED at aa146a2. The green 1562 run does
  NOT cover this: there has never been a News-side bare-`material` canary
  (grep: the 11 new PM tests are the only `material` assertions in the whole
  agent-team tree), which is exactly why deleting the token broke nothing.
  ROOT CAUSE IS CLAUDE G's RELAY, not a Codex deviation: my ruling text said
  "Do NOT ban bare \bmaterial\b" without scoping it to the PM. Codex C
  implemented it faithfully and globally. My error, my correction.
  **G-FB1-2 (BLOCKING - the new pattern is defeated by trivial phrasings, on
  BOTH surfaces).** `_F4_PUBLIC_RECORD_MATERIALITY_RE` requires a copula
  immediately followed by the adjective and an enumerated record noun as the
  subject. It therefore misses: pronoun/anaphoric subjects ("This is material."
  after naming the 8-K), record nouns outside the enumeration (news, 8-K,
  guidance update, earnings print, impact), and **adverb insertion - "The filing
  is highly material." / "is clearly material." passes even though the subject
  IS an enumerated noun.** Denylisting a subject class is an arms race against
  an open set of nouns; it cannot be won by enumeration.
  **CLAUDE E's PARALLEL REVIEW (PASS) - one finding is INVERTED.** Claude E's
  closing note reads: "the materiality pattern now ALSO fires on the
  news_analyst surface ... a TIGHTENING consistent with the news charter - an
  improvement, not a regression." This is backwards. Claude E saw
  `_F4_PUBLIC_RECORD_MATERIALITY_RE` being ADDED to the news_analyst tuple and
  missed that bare `material(?:ity)?` was DELETED from
  `_F4_NEWS_INTERPRETATION_RE` in the same hunk:
    aa146a2 : \b(?:priced in|dovish|hawkish|rate cut|rate hike|material(?:ity)?)\b
    patch   : \b(?:priced in|dovish|hawkish|rate cut|rate hike)\b
  The new record-noun frame is a strict SUBSET of the bare ban it replaced.
  Measured over a 20-string corpus on news_analyst: 13 LOOSENINGS, **0
  TIGHTENINGS**. Their finding 4 ("no F-4 regression - CONFIRMED") rests on a
  green suite that structurally CANNOT see this, because no News-side
  bare-`material` canary has ever existed. Lesson for both reviewers: a pattern
  ADDED to a role's tuple does not imply that role got stricter - only an A/B
  against the base commit shows the direction. Claude G's PASS-with-conditions
  reviews now require an A/B diff whenever a gate pattern is edited rather than
  purely appended.
  **REQUIRED FIX v2 (Claude G, supersedes the first draft; incorporates a real
  catch from Claude E).** Claude E's 12-case trace surfaced two legitimate uses -
  "a material portion" and "differ materially" - that my FIRST proposed fix
  (bare ban + sentence-scoped evidence carve-out) would have OVER-BLOCKED. The
  refined rule keeps the fail-closed allowlist shape (same as F-2's imperative
  whitelist and F-5's allowed-numbers) and adds a grammatical discriminator:
  * Ban PREDICATIVE and NOMINAL materiality only:
    `\b(?:is|was|are|were|remains?|stays?|seems?|appears?|looks?|becomes?|became)\s+(?:<intensifier>\s+)*(?:im)?material\b`
    plus `\bmateriality\b`, where <intensifier> covers not/very/quite/highly/
    clearly/rather/... and any `\w+ly`. The intensifier repetition is what closes
    the "is HIGHLY material" / "is CLEARLY material" adverb hole.
  * ATTRIBUTIVE material (`material` modifying a noun: "source material", "the
    material inputs", "a material portion") is NOT matched at all -> Claude E's
    legitimate uses survive. "materially" never matches `material\b` -> "differ
    materially" survives.
  * PM ONLY: a predicative/nominal hit DROPS unless that same SENTENCE also
    contains a closed-set evidence noun (section/sections/evidence/input/inputs/
    finding/findings/snapshot/snapshots/reading). The evidence vocabulary is
    enumerable because WE define it - it is the PM's own contract vocabulary;
    "things in the world that could be material" is an open set and cannot be
    enumerated, which is why the record-noun denylist loses.
  Probe: **21/21** - all 15 verdict/evasion strings DROP (incl. pronoun subjects,
  unlisted record nouns, adverb insertion, `immaterial`, `materiality of`), all 6
  legitimate uses pass (the founder's 3 + Claude E's `material portion`, `differ
  materially`, `findings are not material`).
  WIRING (closes G-FB1-1 and G-FB1-2 together):
  * `news_analyst` -> bare ban restored, NO carve-out. News never weighs
    evidence, so any materiality talk is a significance verdict. Byte-identical
    to aa146a2; verdict coverage 15/15. G-FB1-1 closed by construction.
  * `portfolio_manager_agent` -> predicative/nominal ban + evidence carve-out
    (its field-1 job IS evidence weighting). G-FB1-2 closed with no over-block.
  * Because News and PM need DIFFERENT materiality rules, materiality must NOT be
    a flat pattern in the inherited union. KEEP the union for patterns
    (`_F4_ROLE_SPECIFIC_PATTERNS["news_analyst"] = (_F4_NEWS_INTERPRETATION_RE,)`
    - priced-in/dovish/hawkish/rate-cut/rate-hike, unconditionally inherited by
    the PM) and add an explicit `_F4_ROLE_ONLY_PATTERNS` registry for the ONE
    justified non-inheritance (News's bare materiality ban). Default = inherit;
    non-inheritance must be EXPLICIT, named, and justified by a charter
    difference. It must NEVER be achieved by silently weakening the stricter
    role - that is the inversion this patch made.
  ACCEPTED RESIDUAL (name it, do not chase it): co-locating an evidence noun with
  a record verdict in one sentence ("The events section shows the filing is
  material.") still passes. It now requires deliberate construction, and F-4.6
  attribution + the `_PM_TRADE_SUBJECT_FRAME_RE` family remain as separate nets.
  NON-BLOCKING OBSERVATION (pre-existing at aa146a2, not a regression; Claude E
  owns the charter): technical_analyst, fundamentals_analyst, and
  risk_management_agent all `pass` "The filing is not material." and "The release
  is already priced in." today. F-B1's logic ("banned on any analyst => banned on
  the PM") does not imply "banned on one analyst => banned on all" - different
  charters - but whether Fundamentals should be able to rate a filing's
  significance is worth one deliberate ruling, not an accident.

  **F-B2 SAFETY REVIEW (Claude G, 2026-07-14, working tree on aa146a2, after
  Claude E re-verification): PASS with ONE eval-only condition. RULING-T5B-3
  issued (below).** Fix v2 landed faithfully: `_F4_ROLE_SPECIFIC_PATTERNS`
  (union, PM-inherited) + `_F4_ROLE_ONLY_PATTERNS` (explicit, commented
  non-inheritance for News's bare materiality ban) + `_pm_materiality_flag`
  (predicative/nominal ban, sentence-scoped evidence carve-out, split on
  `(?<=[.!?])\s+|\n+`). Verified by probe, all offline/synthetic:
  * News A/B vs aa146a2 over a 22-string corpus: **0 loosenings**; tightenings
    are EXACTLY the immaterial family (data/filing/charge/immateriality).
    G-FB1-1 closed. Other three roles + role_name=None: zero drift.
  * PM verdict/evasion suite 15/15 DROP (pronoun subjects, unlisted record
    nouns, adverb insertion, `immaterial`, `materiality of`, plus the four
    F-B1 originals).
  * All EIGHT approved evidence-weighting phrases pass on the direct flag.
  * NEWLINE ISOLATION verified: unpunctuated evidence tail + verdict line,
    colon tail + verdict line, punctuated evidence + nominal line -> all DROP;
    soft-wrapped legit phrase ("...is not\nmaterial to this reading.") still
    passes (no over-block).
  * CROSS-FIELD MERGES through the FULL validator on structure-valid payloads,
    BOTH directions: evidence-noun unpunctuated tail -> verdict head (H1, H2)
    and verdict-only unpunctuated tail -> evidence-noun head (H3c, H4) all
    return advice_boundary_blocked; clean baseline None. `_pm_field_text`
    joins all four fields (incl. verification_priorities) with "\n", so the
    `\n+` split is load-bearing on exactly these seams - confirmed in code.
  * Focused suites: test_p36_calculation_foundation.py + test_llm_provider.py
    = 172 passed, no live calls.
  **RULING-T5B-3 - News immateriality tightening: RATIFIED, STAYS.** "The data
  is immaterial." now DROPS on news_analyst; at aa146a2 it passed because
  `\bmaterial(?:ity)?\b` cannot match inside "immaterial" (no word boundary).
  Grounds: (1) "immaterial" is the fused negative of an already-banned verdict -
  aa146a2 dropped "The filing is not material." while passing "The filing is
  immaterial.", a one-word-rewrite evasion of an accepted ban; that asymmetry
  was an unreviewed hole, not a considered permission, and reverting would
  knowingly re-open it. (2) No legitimate News use exists: News never weighs
  evidence, and quoting a company's "described as immaterial" launders a
  significance verdict - the "material" equivalent already dropped at aa146a2.
  (3) Failure direction: over-tightening costs a News section falling to its
  deterministic floor (fail-closed, product cost only); reverting risks a
  significance verdict reaching the founder's real-account report across a
  legal no-advice boundary. (4) Lattice consistency: the PM predicate ban
  covers `(?:im)?material`; reverting News would permit on the reporting
  surface what the synthesis surface bans - F-B1's inconsistency, mirrored.
  Process note: this boundary change arrived exactly right - surfaced in the
  relay, pinned by an honestly-named test
  (test_p36_news_immateriality_tightening_is_pending_claude_g_ratification)
  rather than slipped in silently. Scope note: News is therefore aa146a2 PLUS
  the immaterial family; my earlier "byte-identical to aa146a2" phrasing is
  superseded - the (?:im)? was in the regex I specified, so the divergence is
  mine, and it is now ratified rather than accidental.
  **CONDITION (eval-only, required before the T5B checkpoint commit):**
  approved phrases #7 and #8 ("The section shows the filing is material." /
  "The evidence confirms the 8-K is material.") are instances of the NAMED
  CO-LOCATION RESIDUAL, not approved evidence-weighting. Keeping them pinned is
  right (regression detection); keeping them inside
  test_p36_pm_allows_material_language_when_it_weights_evidence is wrong - a
  PASS canary is a specification, and a future fix that closes the residual
  would be pressured to preserve the leak. Move both into a separate
  explicitly-labeled residual-documentation test (comment: tolerated gap, not
  approved output; may tighten later without breaking contract). Also rename
  the pending-ratification test to its ratified name and add the four
  immaterial-family strings to the News FAIL canary family. Zero gate-code
  changes.
  **RESIDUALS (verified, named, tolerated - no action):** (a) co-location in
  one sentence, incl. the natural-sounding "The company section and the events
  section disagree on dates, and the filing is highly material." (H5 - passes
  the full validator; third instance of the class alongside #7/#8); (b) copula
  or intensifier split across lines ("The filing is\nmaterial.") - requires a
  deliberate mid-clause hard wrap, unnatural for model output, and the \n
  split that admits it is the same mechanism that closes the far-likelier
  unpunctuated-merge laundering, so the trade is correct; (c) comma
  parenthetical ("The filing is, on balance, material."). All three fail
  toward PASS, all require constructed phrasing, and F-4.6 attribution + the
  PM trade-subject family + the P35 document scan remain as independent nets.
  Optional hardening (NOT required, record only): a raw-text
  copula-newline-material check could close (b) at the cost of re-plumbing the
  carve-out across glued lines; revisit only if an eval canary ever hits it.

  **T5B CLOSE-OUT CONFIRMATION (Claude G, 2026-07-14, commit 7fe736d): T5B is
  DUAL-PASS and ACCEPTED.** Verified in git, not from reports: (1) tree ==
  7fe736d for all of backend/ (zero-line diff), so every probe below ran
  against the committed bytes; (2) scope contained - gates +77 / tests +187 /
  design-doc Sec. 6 +6, nothing else; (3) the newline-aware splitter
  `(?<=[.!?])\s+|\n+` exists at exactly ONE site (v3_value_gates.py:777,
  _pm_materiality_flag) - the three other re.split sites are the pre-existing
  sentence splitters, untouched; role-only registry consumed at exactly one
  role-keyed site (:674), never via the union flattening; (4) all three F-B2
  conditions landed: approved family is exactly SIX phrases; residual-doc test
  1712 holds #7/#8 plus the third co-location instance with the
  tolerated-not-approved comment; ratification test renamed to
  test_p36_news_immateriality_tightening_is_ratified_by_ruling_t5b_3 (1522)
  and the four immaterial-family strings are News FAIL canaries; (5) bonus
  bounding canary 1734: wrapped NOMINAL materiality ("The materiality\nof the
  filing is high") still DROPS, fencing the wrap residual to the predicate
  form only; (6) re-ran the full probe suite against 7fe736d: News A/B 0
  loosenings / tightenings exactly the immaterial family, PM 15/15 DROP,
  8->6+residual phrase families behave, newline + cross-field merges hold,
  other roles zero drift; focused suites 178 passed, offline.
  TWO NOTES, neither reopens T5B:
  * DOC-LABEL COLLISION (docs-only correction, next docs commit): the Sec. 6
    addition in PHASE_36_T5B_PM_SYNTHESIS_DESIGN.md labels the
    predicate-severing WRAP residual as "RULING-T5B-3". RULING-T5B-3 is the
    News immateriality ratification (test 1522 cites it correctly). Two
    decisions now share one identifier across artifacts; a future reader
    resolving the cite gets two answers. Fix: relabel the Sec. 6 paragraph
    "F-B2 REVIEW RECORD (Claude G, 2026-07-14) - tolerated wrap residual" (no
    ruling number; residuals are review records, not rulings). Claude E owns
    the artifact.
  * SEQUENCING NOTE (process, no content risk): 7fe736d was committed AND
    pushed to origin/main before Claude G's close-out confirmation; the agreed
    order was dual-PASS then checkpoint. Content matches what both reviewers
    verified, so nothing to unwind - but the checkpoint-after-dual-PASS order
    exists so a BLOCKED finding never has to be unwound from the remote.
    Reaffirm for T6-era work: no push before both seats confirm.
  Phase 36 status: T5A-1/T5A-1b/T5A-2/T5B all accepted. All five roles plus PM
  synthesis are live-gated. Remaining: FINDING-1 (PM C6-C10 calc surface
  doc-truth in design Sec. 5), FINDING-2 (REPORT_PROSE_KEYS guard test),
  pre-activation checklist items (FMP/FRED dormant lanes), and P36-T6 - the
  five-live-role real-account acceptance run - FROZEN pending explicit founder
  per-run authorization.

  **T5B DOCS CLOSE-OUT ACK (Claude G, 2026-07-14): docs diff VERIFIED and
  ACKNOWLEDGED - clear for the founder to commit.** Verified in the working
  tree: (1) Sec. 6 now carries the TRUE RULING-T5B-3 (News immateriality
  ratification, citing the 1522 canary family) and the wrap residual is
  relabeled "F-B2 REVIEW RECORD ... tolerated wrap residual" with the
  relabel note - one identifier, one decision; (2) Sec. 5 records the PM calc
  surface as C1-C15 with the verify-not-recompute dependency stated and a
  doc-truth footnote.
  **FINDING-1 RESOLVED - with a correction TO MY OWN FINDING (Claude E is
  right).** The effective PM calc surface is C1-C15, not "C6-C10 in addition
  to C1-C5" as I wrote. Verified behaviorally: default_tool_registry() has 15
  calc entries and ALL FIFTEEN allow portfolio_manager_agent (zero denied);
  P36_PM_CALC_TOOL_IDS (tool_mediated_runner.py:582) maps exactly C1-C15. My
  under-read: the C11-C14 grants were in the very registry hunk I quoted for
  FINDING-1 - I flagged the technical lane (C6-C10) and stopped counting.
  Same lesson as the News direction check: enumerate, don't sample.
  SAFETY ASSESSMENT (no delta, three structural reasons, all verified): (a)
  _validate_p36_pm_calc_request is a closed map - id must be in
  P36_PM_CALC_TOOL_IDS, entry.allows_role checked, args are string-only with
  DIGITS BANNED in every value (no number smuggling via requests), and only
  C1 takes one enum arg; (b) every PM calc result is match-only via
  pm_calculation_matches_surfaced_values - never an independent F-5 source,
  C1-C5 and C6-C15 alike; (c) the C1-C5 public barring is intact - probe
  confirmed none of the three public analysts can reach any agent_safe calc.
  **NEW PRE-ACTIVATION CHECKLIST ITEM (from this finding):** when the FMP
  (C11/C12) or FRED (C13) lanes are approved and the WITH-variants wake, the
  PM's dormant grants to those tools wake SIMULTANEOUSLY. Activation canaries
  must therefore include PM-lane checks (PM requests C11/C12/C13 and the
  result is admitted ONLY on match to an analyst-surfaced figure), not just
  the fundamentals/news analyst lanes.
  Sequencing honored this time: the docs commit waited for this ack. Open
  after the docs commit: FINDING-2 guard test (Codex C, next touch) and the
  pre-activation checklist. T6 FROZEN pending explicit founder per-run
  authorization.
- `P36-T5B` - Live PM synthesis: typed PmSynthesis (four verdict-incapable
  fields), whole-block fail-closed, composer rendering, PM calc
  verification access. Owner: Codex C (implementation). Status: DESIGN PHASE
  started 2026-07-13 (T5A-2 dual-PASS accepted). Claude E produces the
  PM-synthesis role block + typed PmSynthesis contract + gate mechanics
  (mirroring PHASE_36_T5A2_PUBLIC_ROLE_BLOCKS.md); Claude G prompt/safety
  review BEFORE Codex C implements. This is the highest-stakes prompt of the
  five - the synthesis/verdict surface - so the no-recommendation boundary is
  the review crux. Codex C implementation gated on: (a) T5A-2 checkpoint
  landed, and (b) Claude G design-review PASS. T6 frozen.
  - `P36-T5B-DESIGN` - Claude E deliverable PHASE_36_T5B_PM_SYNTHESIS_DESIGN.md.
    Claude G prompt/safety review 2026-07-13: PASS with ONE binding condition.
    Verified in code: C1-C5 barred from public (_PUBLIC_CALC_TOOL_NAMES = C6-C15
    only, calculations.py); final_synthesis_authored_by flip enum exists
    (reports.py:86); p36-pm-synthesis-v1 in _P36_VALUE_BEARING_PROMPT_VERSIONS
    so PM prose stays document-scanned (F-12). Strong, honest design (§2 refuses
    to overclaim schema-magic on the two freeform fields). §4 gate map
    (F-1 typed-parse replaces F-8/F-9; F-11 originates-nothing) CONFIRMED. §5
    verify-not-recompute (PM calc values admitted to F-5 ONLY by match to an
    analyst-surfaced figure, never as an independent source) CONFIRMED - correct
    and elegant; a divergent re-run surfaces only as a verification imperative,
    cannot emit a new number.
    RULING-T5B-1 (§6.1) APPROVED: governed PM-only P36_PM_ATTRIBUTION_MARKERS
    superset (P36_ATTRIBUTION_MARKERS + section-attribution phrases), applied
    only on the PM surface, analyst set unchanged. Safe: F-4.6 markers gate
    interpretation-ATTRIBUTION, they do NOT bypass the 5 advice classes or F-11
    grounding, so this turns F-4.6 into a section-attribution REQUIREMENT that
    reinforces no-original-interpretation. Condition: §7.7 with/without-marker
    probe mandatory.
    BINDING CONDITION (the review crux, before Codex C's T5B is accepted): the
    freeform-field verdict-incapability in §2 rests on F-4's "subject-noun
    test", but that test is NOT implemented as described - F-4 has no
    reduce/cut/lighten/pare/increase and P35 only has add/trim/rebalance/buy/
    sell/hold/wait/spread, so §7.1/§7.3 mandatory phrasing "reduce the position"
    would drop in verification_priorities (via F-2 whitelist) but likely SURVIVE
    in evidence_weighting/trust_assessment. Fix: implement the subject-noun
    boundary as a real PM-specific F-4 pattern (subject = trade/position/setup/
    entry/idea + an evaluative/directional predicate -> whole-block drop) rather
    than vocabulary whack-a-mole, AND treat §7 as a LIVING mandatory set that
    includes soft/indirect verdicts ("the trade holds up well", "the setup looks
    solid", "the evidence points the right way", "the trade deserves confidence")
    not only canonical buy/sell/attractive. Verifiable by the §7.1/§7.3 evals
    actually dropping from the freeform fields. Reviewers on impl: Claude E
    (gate/eval) + Claude G (arch/safety). Doc-parity: commit
    PHASE_36_T5B_PM_SYNTHESIS_DESIGN.md + the still-uncommitted
    PHASE_36_T5A2_PUBLIC_ROLE_BLOCKS.md with the impl (T5A1 doc precedent).
  - `RULING-T5B-2` (PM accepted-section input collision) - APPROVED Option A,
    allowlist CORRECTED to the empirically-verified minimal set. The PM must
    receive accepted analyst prose (incl. Risk), which legitimately carries
    bare topic words that the dynamic value-token scan rejects. Verified by
    synthetic probe (find_forbidden_string_values): ONLY {cash, holdings,
    positions} actually collide - portfolio/exposure/nickname/account are
    already allowed (not in LLM_PROVIDER_FORBIDDEN_VALUE_TOKENS), so Codex C's
    proposed 7-token list is over-specified; exempt exactly {cash, holdings,
    positions}. Reuse the existing governed _STATIC_SYSTEM_PROMPT_PLAIN_TOPIC_
    TOKENS (this set is a subset) or a documented PM constant equal to it - do
    NOT add the four non-colliding words (esp. identifier-adjacent account/
    nickname). SAFETY BASIS (keeps the prior 'dynamic stays strict' ruling
    intact): the exemption applies ONLY to the projection of accepted sections
    that ALREADY passed the full v3 stack incl. F-6 and were frozen - it is
    re-ingestion of post-gate artifacts, not fresh dynamic input; the coarse
    bare-word check is redundant there while F-6 already cleared it. Conditions:
    (1) scoped to the p36-pm-synthesis-v1 accepted-section projection only - NOT
    other PM dynamic segments, NOT other roles; public-role dynamic messages
    stay strict; (2) all other scans retained over the projection (forbidden-
    key, compound-token, identifier, secret, path, raw-payload, phrase) -
    probe-confirmed compounds still reject under the exemption; (3) INPUT-only:
    widens what the PM receives, not what it emits - PM output still faces the
    full F-4..F-13 stack incl. F-6, so no output identifier hole; (4) a test
    asserts the PM allowlist is EXACTLY {cash, holdings, positions} (guards
    silent widening, same fail-open concern as T5A-2 FINDING-1). Rejected B:
    a prose-stripping projection breaks the PM's evidence-weighting job; a
    prose-preserving one hits the identical collision = A by another name.
    Required tests (Codex C list + mine): accepted Risk section reaches PM;
    cash_balance/account_id/identifiers/secrets/paths/raw-payloads still fail
    closed over the projection; public-role dynamic strict; PM readback reruns
    neither tools nor provider; allowlist-exactly-three guard.
    RATIFICATION 2026-07-13 (Claude E sharpened to a 7-token governed SSOT
    P36_F6_VOCABULARY_ONLY_TOKENS = {account,holdings,cash,positions,portfolio,
    exposure,nickname}, requesting safety ratification of the RULING-T5A1-1
    strict-dynamic relaxation): RATIFIED, reconciled. I withdraw the
    force-to-3: in the contracts value-token scan only {cash,holdings,
    positions} are non-inert (the other four aren't in
    LLM_PROVIDER_FORBIDDEN_VALUE_TOKENS), so the 7-token SSOT is behaviorally
    identical there and consistency has value - accept it. BINDING SAFETY
    CONDITION on the 'imported by F-6' half: F-6 today has NO bare-word
    allowlist and already passes all 7 bare words implicitly (probe:
    bare account/cash/holdings/positions/portfolio/exposure/nickname -> None),
    while account+5-digit -> identifier_privacy_blocked and cash_balance/
    account_id -> blocked. 'account' sits in BOTH the proposed constant AND
    _IDENTIFIER_CONTEXT_RE (the proximity trigger). So the constant must be
    behavior-PRESERVING in F-6: it may centralize/name what F-6 already passes
    implicitly, but must NOT become a new allowlist gate, must NOT remove any
    word from _IDENTIFIER_CONTEXT_RE, and must NOT short-circuit the ambiguous-
    proximity branch. Mandatory parity canary (baseline captured today): with
    the constant in place, 'the account 48213 was reviewed' STILL returns
    identifier_privacy_blocked, and each vocab word + a >=5-digit number still
    flags. If 'import into F-6' changes any F-6 decision on Risk or the 3
    public surfaces, that half is REJECTED for T5B (the exemption may still
    ship on the PM projection alone). Guard test asserts the constant's EXACT
    7-member set (blocks silent widening). All prior conditions stand
    (input-only; scoped to p36-pm-synthesis-v1 evidence payload; other scans
    retained; public/other dynamic strict).
- `P36-T6` - Live acceptance run (five live roles) under per-run founder
  authorization; founder judges the working version. Status: queued. No
  live acceptance runs before this per founder direction.
- `P35-R2` (parallel research) - Role-specialization incremental value.
  Owner: Codex G. Status: done 2026-07-10 (review PASS; ranks 1-4 adopted
  as the eval package, parameterized to the v3 section contract).
- `P36-BIZ` - Business case + Pre-Trade Check direction. Owner: Codex A.
  Reviewer: Claude G. Status: Codex A memo delivered
  (docs/codex-a-product/BUSINESS_CASE_2026H2.md - conditional GO for
  validation, Pre-Trade Check frame, check-level decisiveness, 12-15
  synthetic-stimulus interviews by 2026-08-15, alpha gate 2026-09-30).
  Claude G challenge review 2026-07-10: PASS on direction with five
  required revisions (recruiting channels named; policy-vs-mechanics
  check-state taxonomy split; all-green "misread as approval" mitigation
  as acceptance criterion; ICP options-cadence sharpened to monthly for
  the options cohort + multi-account weighting; T6 acceptance run gains a
  covered-call scenario with honest not-fully-modelled states). Key
  finding: the beachhead (CC/CSP) is the least-built engine area -
  covered_call/cash_secured_put flows exist but coverage is
  "not_fully_modelled"; C4/C5 calc tools are beachhead-critical. P35-T8
  (look-through source) must be decided before public alpha. Pre-Trade
  Check layer = separate P37 slice consuming deterministic outputs; no
  scope creep into P36-T4/T5.
  FOUNDER DECISION 2026-07-10: no startup attempt for now - the goal is
  to polish the product. The interview/validation plan is SHELVED (memo
  retained as reference; the five revisions moot until commercialization
  reopens). The Pre-Trade Check frame, check-state taxonomy split,
  all-green microcopy rule, and summary-first hierarchy are RETAINED as
  the product-voice direction for the post-T6 polish phase (P37).
  Q-R2/Q-R3 RESOLVED by founder: FMP fundamentals lane and FRED series
  lane both approved, FREE TIER ONLY - all external APIs run on free
  tiers; contracts and implementation must design for free-tier rate
  limits (freeze-once-per-report, caching, honest unavailable on
  rate-limit, WITHOUT-variant fallback).

### Phase 34A - Live Tool-Mediated Agent Team Prototype

- `P34A-T0` - Live prototype contract.
  - Owner: Codex B. Reviewers: Codex A/founder for product posture; Claude E for
    agentic design alignment.
  - Architecture reference:
    `docs/codex-b-architecture/PHASE_34A_LIVE_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md`.
  - Status: done 2026-06-29 by Codex B. Opens Phase 34A as the live-data/live-LLM
    successor to the P33A mock/offline scaffold. "Working prototype" now means a
    backend-owned, read-only Agent Team run that starts from a saved trade-review
    evidence package, uses live LLM role reasoning only when explicitly enabled,
    lets roles request reviewed backend tools through structured tool requests,
    gives LLMs only sanitized `ToolResult` envelopes, uses real reviewed data
    sources where approved, and freezes all used tool/model artifacts for saved
    report readback. P34A remains internal/non-production: no direct LLM access to
    broker/provider/news/EDGAR clients, no frontend LLM calls, no raw private data
    in prompts/results, no order/execution behavior, no web/MCP/TradingAgents
    runtime, and no LangGraph dependency as the safety boundary.

- `P34A-T1` - Live LLM runner gate for tool-mediated reports.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-29 by Codex C; Codex B contract/privacy review PASS.
    The existing backend `LLMProvider` / provider-factory seam now gates live
    role reasoning for tool-mediated reports. Live remains disabled by default,
    provider-factory `LLMProviderResolution` controls activation, prompts receive
    only sanitized `ToolResult` envelopes, provider failures degrade to skipped/
    unavailable role output while preserving deterministic tool evidence, unsafe
    provider output is rejected before persistence, and saved report readback
    remains frozen. Verification PASS: `test_tool_mediated_report.py` 36 passed;
    agent_eval + agent_team 295 passed, 2 deselected; report schema unit tests 90
    passed; `git diff --check` clean. No frontend, provider-live test, broker,
    EDGAR, MCP, TradingAgents, LangGraph, or new source scope drift.

- `P34A-T2` - Live role prompt and Evidence Auditor design.
  - Owner: Claude E. Reviewer: Codex B.
  - Design reference:
    `docs/claude-e-agentic/PHASE_34A_T2_LIVE_ROLE_PROMPT_AUDITOR_DESIGN.md`.
  - Status: done 2026-06-29 by Claude E; Codex B review PASS. Design keeps live
    prompts limited to sanitized `ToolResult` envelopes plus approved
    instructions; citations remain backend-owned and cannot be introduced by the
    LLM; the Evidence Auditor rejects advice/actionability, unsupported claims,
    invented numbers/levels/URLs, and private leaks fail-closed; exactly one
    bounded re-pass is allowed only for fixable unsupported/contradictory claims;
    hard blocks are never retried. Codex B decisions: Q1 approved an additive
    safe `provider_runs` metadata field on `SavedToolMediatedRunArtifactRead`;
    Q2 PM synthesis stays deterministic in M1; Q3 live failures fall back to the
    deterministic finding rather than skipping when a floor exists; Q4
    contradiction detection uses structured caveat/availability signals rather
    than LLM prose tokens; Q5 per-finding live prose is preferred with one-per-
    role fallback acceptable; Q6 implementation is split into T3A prompt/auditor/
    freeze changes and T3B real saved-evidence tool pack.

- `P34A-T3A` - Live prompt/auditor implementation and provider-run freeze metadata.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-30 by Codex C; Codex B contract/privacy/safety review
    PASS. Implemented the P34A-T2 prompt/auditor behavior without adding new
    tools or sources: live remains disabled by default; LLM/provider output never
    owns `evidence_refs` or `caveat_codes`; provider failures and unsafe output
    fail closed to the deterministic safe floor when available; hard blocks are
    not re-passed; contradiction detection uses structured caveat/availability
    signals; additive `provider_runs` freezes only approved safe metadata; frozen
    artifacts do not persist raw prompts, raw responses, payloads, traces,
    secrets, URLs, private account data, or unsafe trading/action wording; saved
    report readback/model validation does not re-run providers; blocked
    deterministic drafts still do not attach `tool_run_artifact`. Verification
    reported PASS: `test_tool_mediated_report.py` 37 passed;
    `test_tool_mediated_eval.py` 27 passed; agent_team + agent_eval 301 passed,
    2 deselected; report schema unit tests 90 passed; full backend pytest 1186
    passed, 138 skipped, 3 deselected; `git diff --check` clean.

- `P34A-T3B` - Real saved-evidence tool pack v1.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: next. Convert the approved M1 tools
    (`trade_intent_summary`, `portfolio_scope_context`,
    `deterministic_review_findings`, `broker_snapshot_freshness`,
    `market_quote_freshness`, `public_company_profile`,
    `evidence_gap_inspector`) from mock/offline placeholders to real saved-
    evidence-backed tools where needed. Tools must read frozen saved evidence, not
    current selectors, and must not expose raw private values.

- `P34A-T4` - Market/macro source-rights gate.
  - Owner: Codex B. Reviewer: Codex A/founder.
  - Status: pending T1. Decide whether existing Market Mood and Economic
    Awareness surfaces may be used as Agent Team tools. Record approved
    normalized fields, LLM use, saved-report persistence, display attribution,
    retention/cache limits, failure behavior, and implementation prompt.

- `P34A-T5` - Market/macro tool pack.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: pending T4. Implement only source-rights-approved market/macro tools
    as backend-only `ToolResult` producers. No raw URLs/payloads, no broad
    crawling, no market-data provider expansion beyond the approved contract.

- `P34A-T6` - Public news/event source-rights gate.
  - Owner: Codex B. Reviewer: Codex A/founder.
  - Source-rights reference:
    `docs/codex-b-architecture/PHASE_34A_T6_PUBLIC_NEWS_EVENT_SOURCE_RIGHTS_GATE.md`.
  - Status: done 2026-06-30 by Codex B. General public-news providers are not
    approved for Agent Team tools in P34A. NewsAPI/generic aggregators,
    Benzinga/Finnhub/Polygon/FMP news, and GDELT/web-scale news databases remain
    blocked pending provider-specific rights, excerpt/URL/raw-payload,
    retention, attribution, and commercial-use review. Conditionally approved
    one narrow event lane: SEC EDGAR recent filing metadata only, as normalized
    company-event metadata with source attribution, no SEC endorsement wording,
    no filing-body/exhibit/XBRL/news text, no raw URLs/payloads, no filing/event
    interpretation, and no trading-action language. Failures degrade to
    unavailable/gap states and must not fall back to news providers, web search,
    or scraping.

- `P34A-T6A` - SEC EDGAR recent filing metadata tool.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-07-01 by Codex C; Codex B-style review PASS after raw SEC
    path/file-name leakage risk was fixed and narrowly re-reviewed. Added the
    backend-only `sec_recent_filings_metadata` tool over frozen saved
    `public_evidence.public_events_calendar`, citing only approved
    `source_key="sec_edgar_recent_filings"` sections with `available`/`limited`
    availability. Tool output is normalized metadata only (`form_type`,
    `filing_date`, and opaque `filref_...` references), plus backend-owned
    attribution/caveat/non-endorsement/limitations. `public_news_snapshot`
    remains unavailable/not_reviewed unless separately approved. No NewsAPI,
    Benzinga, Finnhub, Polygon, FMP, GDELT, CNN, web search, scraping, MCP,
    TradingAgents, LangGraph, frontend work, or live provider tests. Verification
    PASS: `test_tools.py` 74 passed; tool-mediated report + eval tests 66
    passed; report schema unit tests 90 passed; `git diff --check` clean.

- `P34A-T6B` - SEC recent filing metadata role behavior design.
  - Owner: Claude E. Reviewer: Codex B.
  - Design reference:
    `docs/claude-e-agentic/PHASE_34A_T6B_SEC_FILING_METADATA_ROLE_DESIGN.md`.
  - Status: done 2026-07-01 by Claude E; Codex B review PASS with one binding
    implementation clarification. Decisions: Q1 confirmed neutral
    filing-metadata listing stays backend-deterministic and live prompt
    envelopes remain stripped of `summary_payload`; Q2 confirmed the SEC/event
    `news_analyst` finding is not live-overwritten in M1; Q3 confirmed extending
    generic metadata-available phrasing to a deterministic backend listing of
    `form_type`/`filing_date` is in scope for Codex C; Q4 confirmed no new
    schema/read-contract field and reuse of existing `claim_text` +
    `public_events_calendar`. Additive backend-only `SEC_INTERPRETATION_TOKENS`
    guard approved. Implementation must add an SEC-specific role/citation guard:
    only `news_analyst` and `portfolio_manager_agent` may cite SEC recent filing
    metadata even though older generic report allowlists may include
    `public_events_calendar` for other public roles.

- `P34A-T6C` - SEC recent filing metadata role behavior implementation.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-07-02 by Codex C; Codex B-style review PASS after
    SEC urgency-token false positives were narrowed to SEC/filing context and
    re-reviewed. Implemented deterministic backend rendering of SEC recent
    filing metadata for the news role (`form_type` and `filing_date` only),
    kept `filing_reference` opaque/audit-only, prevented live LLM overwrite of
    the SEC news finding in M1, kept live prompt envelopes stripped of filing
    facts, degraded unavailable/not-approved SEC metadata to a gap citing
    `trade_intent_summary` only, added SEC interpretation/source-leak hard
    blocks, and enforced that only `news_analyst` and
    `portfolio_manager_agent` may cite SEC recent filing metadata. Verification
    PASS: `test_tools.py` 74 passed; tool-mediated report + eval tests 73
    passed; report schema unit tests 91 passed; `git diff --check` clean.

- `P34A-T6D` - SEC EDGAR recent filing metadata replay/acquisition boundary.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-07-02 by Codex C; review-only Codex B subagent PASS.
    Implemented backend-only replay/acquisition boundary, disabled by default and
    requiring explicit policy/client. Normalizes only approved saved evidence
    into `public_evidence.public_events_calendar` with
    `source_key="sec_edgar_recent_filings"`, source label,
    availability/freshness/as-of/collected-at, `form_type`, `filing_date`,
    opaque `filref_...` reference, attribution, caveat, and non-endorsement. No
    schema/read-contract expansion, frontend work, live EDGAR call, provider/
    broker/private-data access, raw SEC URL/path/file/accession/body/payload
    persistence, or refetch on saved report readback. Verification PASS:
    `test_tools.py` 74 passed; tool-mediated report + eval tests 73 passed;
    report schema unit tests 104 passed; `git diff --check` clean.

- `P34A-T7A` - Live prototype readiness audit.
  - Owner: Codex B. Reviewer: Codex A/founder for go/no-go awareness.
  - Architecture reference:
    `docs/codex-b-architecture/PHASE_34A_T7A_LIVE_PROTOTYPE_READINESS_AUDIT.md`.
  - Status: done 2026-07-02 by Codex B. Verdict: no-go for a true end-to-end
    live saved-report smoke until the saved-report generation route is wired to
    the tool-mediated runner behind a backend-only disabled-by-default gate. The
    service-level live runner is ready enough for a backend-only smoke with
    explicit credential authorization, but the golden-path Reports endpoint still
    calls the deterministic-template generator. No secrets, `.env`, logs, DB
    contents, broker payloads, or real reports were inspected.

- `P34A-T7B` - Tool-mediated saved-report generation route wiring.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-07-02 by Codex C; Codex B review PASS. `POST
    /users/{user_id}/reports/{thread_id}/agent-team-report` can optionally use
    the reviewed tool-mediated summary builder through backend-only
    `POA_AGENT_TEAM_REPORT_GENERATION_MODE=tool_mediated`; deterministic-template
    generation remains default. Client request body cannot select mode/provider.
    Providers resolve only through `LLMProviderResolution`; `tool_run_artifact`
    persists; saved report readback stays frozen; no schema/read-contract,
    frontend, new-source, web/MCP, TradingAgents, LangGraph, or secret/log
    exposure was added.

- `P34A-T7C` - Disposable DB verification for route-backed tool-mediated reports.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-07-02 by Codex C; Codex B accepted. Verified Alembic
    upgrade head and DB-backed report/trade-review API suites against isolated
    disposable Postgres (`poa_t7c_test`), including the route-backed
    tool-mediated report-generation tests. No `.env`, secrets, real DB contents,
    broker data, raw provider payloads, live LLM, EDGAR/FRED, frontend paths, or
    schema/read-contract changes were used.

- `P34A-T7D` - Route-backed live LLM saved-report smoke harness.
  - Owner: Codex B. Reviewer: Codex B/founder for live-smoke acceptance.
  - Status: done 2026-07-02 by Codex B. Added and ran opt-in external/slow test
    `backend/tests/api/test_tool_mediated_route_live_smoke.py` covering the real
    route spine with synthetic saved evidence: selected review account
    portfolio-preview -> save evidence snapshot -> `agent-team-report` route with
    backend tool-mediated live Gemini config -> frozen `tool_run_artifact` +
    provider-run metadata -> list/detail readback without rerunning tools or
    provider resolution. Passed against isolated disposable Postgres
    (`poa_t7d_test`) with `POA_LLM_PROVIDER=google`,
    `POA_LLM_MODEL=gemini-2.5-flash-lite`, and the key supplied through a
    temporary launchctl bridge; `google-genai` was installed via the optional
    backend `live-llm` extra. The disposable DB container was stopped/removed and
    the launchctl key bridge was unset. No `.env`, secret value, real DB contents,
    broker data, raw provider payloads, prompt text, response text, or frontend
    route was inspected or printed.

- `P34A-T7` - Live end-to-end prototype smoke.
  - Owner: Codex B. Reviewers: Codex A/founder for usefulness; Claude B if UI
    changes.
  - Status: active. Provider-level Gemini live smoke passed in founder terminal
    on 2026-07-02 (`test_gemini_live_smoke.py`, synthetic data only). Route-backed
    live saved-report smoke passed in Codex on an explicitly authorized
    disposable stack via P34A-T7D. Initial proven scope is one stock/ETF saved
    report. Simple-options live route smoke remains a follow-up candidate.
    Approved tools only, frozen readback, no private leaks, and no
    advice/order/execution wording remain mandatory.

- `P34A-T8` - LangGraph architecture spike.
  - Owner: Claude E. Reviewer: Codex B.
  - Status: design PASS and implementation deferred 2026-07-03 by Codex B/founder.
    Reviewed Claude E T8 and T8R against the P34A live tool-mediated contract and
    current app-owned runner. ADR 0010 records the binding architecture decision:
    LangGraph may later wrap reviewed app-owned nodes as an orchestration shell,
    with LangGraph owning sequencing only while app-owned validators, tool
    execution, citation ownership, output safety, and freeze/readback remain the
    safety boundary. No LangGraph dependency or T8A implementation should start
    now; Phase 34A returns to the current app-owned runner, live Agent Team
    quality, and approved real-evidence/tool depth.

- `P34A-T9` - Current-runner live Agent Team quality and evidence-use design.
  - Owner: Claude E. Reviewer: Codex B.
  - Design reference:
    `docs/claude-e-agentic/PHASE_34A_T9_LIVE_QUALITY_EVIDENCE_USE_DESIGN.md`.
  - Status: design PASS 2026-07-03 by Codex B. Accepted the diagnosis that live
    reports feel shallow because role findings collapse into one generic sentence,
    deterministic floors often omit specific freshness/caveat/gap names, and PM
    synthesis is too static. Decisions: FRED release-name/date deterministic
    listing is approved inside the existing FRED metadata lane only when sourced
    from frozen approved metadata and still excludes values/forecasts/observations;
    compositional PM synthesis is still within the M1 deterministic-PM decision
    because it assembles audited backend-owned findings without LLM authorship;
    additive `fred_interpretation_blocked` eval flag is approved; P34A-T9B
    provider-seam/per-finding live prose changes require separate Codex B review.

- `P34A-T9A` - Deterministic specificity pack for tool-mediated reports.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-07-03 by Codex C; Codex B-style review PASS after a
    narrow FRED value-smuggling blocker was fixed and re-reviewed. Implemented
    Layer 1 from the T9 design: freshness category naming, readable scope caveat
    text, named evidence-gap sections, FRED metadata-only release/date listing
    from frozen approved metadata plus unavailable warning and interpretation
    hard block, and compositional deterministic PM synthesis with offline eval
    coverage. No provider-seam changes, no new sources, no frontend, no
    LangGraph/LangChain/MCP/TradingAgents, no live calls, and no schema/read
    contract expansion.

- `P34A-T9B` - Additive live connective overlay.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-07-03 by Codex C; review-only subagent PASS. Live provider
    success is now additive-only: deterministic T9A findings persist verbatim,
    provider output may append at most one validated `live_connective_context`
    finding per eligible role, hard-blocked/invalid provider output drops only
    the added live finding, provider failure/timeout keeps the deterministic
    floor plus `live_provider_*` warnings, prompt version is
    `p34a-tool-mediated-role-v2`, prompt envelopes remain unchanged, and PM
    synthesis digests the first deterministic finding rather than appended live
    connective prose. Verification PASS: `test_tools.py` 75 passed; tool-mediated
    report + eval tests 85 passed; report schema unit tests 104 passed;
    `git diff --check` clean.

- `P34A-T10` - Route-backed live smoke after T9A/T9B; live model-selection design.
  - Owner: Codex B (smoke); Claude E (model-selection design). Reviewer: Codex B.
  - Design reference:
    `docs/claude-e-agentic/PHASE_34A_T10_LIVE_MODEL_SELECTION_QUOTA_DESIGN.md`.
  - Status: done 2026-07-04. The T10 id ended up covering two related slices,
    both complete: (a) the opt-in route-backed live Gemini smoke ran on
    synthetic evidence against disposable Postgres and verified the post-T9B
    no-subtraction behavior through the real report-generation route (frozen
    provider runs, additive-only live findings, rerun-free readback, no private
    data or unsafe wording); (b) the live Gemini model-selection/quota-avoidance
    design was review PASS and produced the T10A implementation slice below.

- `P34A-T10A` - Ordered Gemini model-candidate fallback (chain).
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-07-04; review PASS. `POA_LLM_MODEL_CANDIDATES` (max 4,
    single provider, the configured list IS the chain) resolves a
    `ChainedLLMProvider` with a sticky forward-only candidate index; the chain
    advances only on quota_exceeded / rate_limited / provider_unavailable /
    provider_timeout / invalid_response, auth errors abort, and safety failures
    never advance. Additive frozen `provider_runs` metadata:
    `model_chain_position` + `attempted_models` (model ids only).
    `DEFAULT_LIVE_MODEL` refreshed to `gemini-2.5-flash-lite`. A real live
    chain advance was proven through the route-backed smoke; results:
    `reports/agent-team-test-results/20260704-p34a-t10a-model-chain-live-smoke.md`.

- `P34A-T11` - Agent Team package structure reorganization (T11A-T11F).
  - Owner: Claude E design; Codex C slices. Reviewer: Codex B (each slice PASS).
  - Design references:
    `docs/claude-e-agentic/PHASE_34A_T11_AGENT_TEAM_STRUCTURE_REVIEW.md`,
    `docs/claude-e-agentic/PHASE_34A_T11_FINAL_STRUCTURE.md`.
  - Status: done 2026-07-06; checkpointed at `e4675ae`. Behavior-preserving
    reorganization of `backend/app/services/agent_team/` into `llm_clients/`,
    `agents/`, `tools/`, `auditing/`, `orchestration/`, `safety/`, and
    quarantined `legacy_console/`, with retained `tools` /
    `tool_mediated_report` facades and no-flat-shim guard tests. No runtime
    behavior or validator change. Note: this plan previously used the T11 id
    for the integrated Trade Review Agent Console direction; that still-open
    direction is re-numbered to `P34A-T14` below to resolve the collision with
    the shipped T11 structure docs.

- `P34A-T12` - Readable saved-report export for the route-backed smoke.
  - Owner: Codex C. Reviewer: Claude G.
  - Status: done 2026-07-07; Claude G review PASS. The opt-in route-backed live
    smoke now writes a founder-readable Markdown + selected-JSON artifact pair
    to `reports/agent-team-test-results/`, rendered only from the frozen
    report-detail readback (saved summary + `tool_run_artifact`), with
    secret/forbidden-key/prohibited-phrase sweeps that raise before writing.
    Offline unit tests cover section presence, poison-field exclusion, and
    fail-closed unsafe content with nothing written. No schema, runner, prompt,
    validator, env, or frontend changes.

- `P34A-T13` - Forced-model live Agent Team report runs and usefulness read.
  - Owner: Claude G with explicit founder live-call authorization. Reviewer:
    founder for usefulness; Claude E consulted on the quality fork.
  - Status: runs complete 2026-07-07 by Claude G; founder usefulness acceptance
    pending. Both forced-model route-backed live runs passed against disposable
    Postgres (`poa_t13_test`, torn down): `gemini-3.1-flash-lite` (2.45s, both
    eligible live roles ok) and `gemini-3-flash-preview` (53.5s; technical role
    ok, risk role degraded honestly to `provider_unavailable` with the
    deterministic floor preserved — correct fail-safe, no fallback by design).
    Readable exports (model ids/statuses only, sweeps clean):
    `reports/agent-team-test-results/20260707T191812Z-*` (3.1-flash-lite) and
    `20260707T191918Z-*` (3-flash-preview). Claude G quality read: the
    deterministic T9A layer carries all real signal; both models' single live
    connective findings restate deterministic caveats or garble them (both
    asserted a "manual" freshness category the frozen evidence categorizes as
    "fresh"), so the pre-agreed "too generic" fork is triggered — recommend a
    Claude E role-behavior/prompt design task plus an accuracy gate checking
    live prose against envelope categories, and a richer synthetic evidence
    package so more than two roles exercise live. Blocker root cause resolved
    during the run: a stale inherited `GOOGLE_API_KEY` (leftover launchctl
    bridge) shadowed the root `.env` value because the loader fills missing
    keys only; runs use `env -u GOOGLE_API_KEY` until the founder clears the
    stale variable.
  - Key-sourcing policy (2026-07-07, founder decision): live smokes obtain named
    LLM API keys (`GOOGLE_API_KEY`/`OPENAI_API_KEY`) only through
    `backend/tests/live_llm_config.py` — root project `.env` named-key retrieval
    under explicit `RUN_LIVE_LLM_TESTS=true`, or a narrowly-scoped
    `POA_LIVE_LLM_TEST_CONFIG` file. The former
    `backend/config.local.live-llm.env` / `backend/secrets/live-llm.env` bridge
    files are retired and must not be reintroduced. Default pytest requires no
    keys, no `.env`, and no network; secrets stay backend-only and unprinted.

- `P34A-T15` - Market-data agent-tool source-rights gate.
  - Owner: Claude G. Decisions: founder.
  - Architecture reference:
    `docs/codex-b-architecture/PHASE_34A_T15_MARKET_DATA_AGENT_TOOL_SOURCE_RIGHTS_GATE.md`.
  - Status: done 2026-07-07. Founder-decided: FMP end-of-day historical OHLCV
    for the reviewed symbol only (existing key, injected-client pattern), all
    indicators computed by deterministic backend Python, values approved for
    LLM prompts (sanitized envelopes) and saved-report persistence, internal
    prototype only. Production/public display NOT approved (paid-license
    review required first). FMP news/fundamentals/intraday, Alpaca, and
    yfinance declined for this slice. Motivated by the P34A-T13 quality read:
    live prose is unusable because envelopes are metadata-starved and role
    output is capped at one sentence; this gate + T16/T17 are the working-
    version path (TradingAgents structured-report analysis, reference only).

- `P34A-T16` - Deterministic market-context tool pack.
  - Owner: Codex C. Reviewer: Claude G.
  - Status: done 2026-07-07 by Codex C; Claude G review PASS. FMP EOD boundary
    + deterministic indicator snapshots (golden-value tested, Decimal math, no
    new deps) behind default-off `POA_MARKET_CONTEXT_MODE`; symbol resolved
    only from frozen saved evidence; budget-capped (2 requests/run) injected
    client with sanitized errors; values freeze into `tool_run_artifact`;
    deterministic technical/risk/PM findings cite `public_market_context`;
    LLM prompts still receive metadata only (value exposure deferred to T17
    together with the numeric-consistency gate). Verification: focused suites
    413 passed; report schema 104; full offline 1318 passed; diff-check clean.
    Deferred polish: unused builders-dict entry; freshness-vocabulary
    alignment; `.env.example` placeholder for the new mode knob.

- `P34A-T17` - Role report contract v3 and numeric/category/structure gates.
  - Owner: Claude E (design), Codex C (implementation as T17A). Reviewer:
    Claude G.
  - Design reference:
    `docs/claude-e-agentic/PHASE_34A_T17_ROLE_REPORT_CONTRACT_V3_DESIGN.md`.
  - Status: design PASS as amended 2026-07-07 by Claude G (initial BLOCKED on
    two §3 gate-logic defects; amendments applied in place: honest-gap
    vocabulary excluded from the bare-enum trip set, and envelope string-value
    numerals added to the numeric allowed-set; regression eval cases C4/N8
    mandatory). Decisions D1-D5 recorded: fact-label prompt projection (no raw
    summary_payload); retiring the live-prose digit ban for v3 sections in
    favor of per-token envelope matching confirmed as an upgrade with all
    other validators byte-identical; additive schema fields/flag vocabulary
    approved; envelope values technical-role-only in v3; PM synthesis stays
    deterministic (live PM synthesis deferred to a future T17B design).

- `P34A-T17A` - Role report contract v3 implementation.
  - Owner: Codex C. Reviewer: Claude G.
  - Status: done 2026-07-07 by Codex C; Claude G review PASS after one
    category-gate blocker fix (P34A-T17A-F1: assertion-regex over-capture
    dropped correct natural prose; fixed with compound connectors, two-word
    progressive normalization, and membership-mechanism regression tests).
    Prompt v3 with structure contract and per-role budgets, additive
    live_report_markdown storage + deterministic PM embedding of audited
    surviving sections, fail-closed structure/numeric/category gates (never
    re-passed), symbol-free fact-label prompt projection (no raw
    summary_payload), LIVE_CONNECTIVE_DIGIT_RE retired for v3 sections only,
    exporter live-section rendering, amendment cases C4/N8 green.
    Verification: agent suites 417 passed; full offline 1329 passed;
    diff-check clean.

- `P34A-T18` - Forced-model live rerun over rich evidence and founder read.
  - Owner: Claude G with founder live-call authorization.
  - Status: first live run 2026-07-08 (gemini-3.1-flash-lite, prompt v3,
    POA_MARKET_CONTEXT_MODE=live, disposable DB, torn down). Proven live: the
    technical role produced a structured multi-section report with summary
    table that survived the gates, froze, embedded into PM synthesis, and
    exported; the risk role's live section was correctly dropped in
    production by the category gate (live_category_mismatch_dropped) with the
    deterministic floor intact. Two blockers to a value-carrying rerun found
    and diagnosed: (1) FMP legacy-endpoint 403 - the account requires the
    /stable/historical-price-eod/full endpoint, not /api/v3/ (key itself
    valid; the FMP economic-calendar lane likely shares this and should be
    checked separately) -> fix task T18-F1; (2) colon-form category
    assertions bypass the assertion regex ("Market quote freshness: manual"
    survived into the live table, contradicting the deterministic floor's
    "fresh") -> fix task T17A-F2. Rerun after both fixes.
  - Status update: pipeline milestone 2026-07-08 — the founder subsequently
    rejected this report as NOT the working version (not trade-centered, not
    account-aware, internal tokens in prose, weak formatting); see Phase 35
    for the accepted working-report definition. After T18-F1
    (FMP stable endpoint, Codex C, Claude G review PASS) and a Claude G-
    implemented field-fix series (T17A-F2 colon-form assertions; T17A-F3
    freshness vocabulary imported from the canonical FreshnessStatus enum;
    deterministic `_freshness_category` truthful manual/eod/delayed mapping
    delegated to a shared gate helper; SEC path regex letter-initial
    extension fix so decimals are not "filenames"; bare trip set reduced to
    {fresh, stale} with unknown joining the always-allowed ignorance
    vocabulary; token-class haystack selection; colon-form non-vocabulary
    captures treated as item labels; label-derived categories admitted to
    the allowed set; default-off POA_LIVE_GATE_DEBUG single-token
    diagnostic; POA_ROUTE_SMOKE_SYMBOL override), the route-backed live run
    (gemini-3.1-flash-lite, POA_MARKET_CONTEXT_MODE=live, symbol AAPL,
    disposable DB, torn down) produced BOTH live role reports surviving all
    gates with real frozen market values (close/SMA/EMA/RSI/MACD/Bollinger/
    ATR/52w range), structured headings + summary tables, honest gaps, no
    advice/verdict wording, rerun-free readback. Artifact:
    `reports/agent-team-test-results/20260708T133910Z-*`. Full offline suite
    1341 passed; every field fix carries a regression test. Founder
    usefulness read pending. Note: the Claude G-implemented fixes were
    self-reviewed under founder direction; an independent Codex B-style
    review of `live_report_gates.py` remains available as a hardening pass.

- `P34A-T14` - Integrated Trade Review Agent Console direction (re-numbered from T11).
  - Owner: Codex B. Reviewers: Claude E for agentic behavior; Claude A/Claude B
    for later frontend/product UX.
  - Status: open direction (2026-07-03), gated on the P34A-T13 usefulness read.
    Agent Console is no longer a parked separate surface. The intended product
    direction is a single Trade Review workspace where the user enters a
    potential trade, runs the Agent Team review, sees each agent's findings
    in-place, and then saves/freezes the final Agent Team report as the
    historical report artifact. The composer/chat remains out of scope for now;
    this slice is about an integrated read-only run surface, role findings,
    progress/state, provenance, and the frozen saved report handoff. No
    order/execution behavior, frontend financial computation, raw private data
    exposure, LangGraph dependency, or new source expansion.

### Closed Context - Phase 30B Golden Path Prototype Hardening And Demo Readiness

- `P30B-T0` - Open hardening contract and task sequence.
  - Owner: Codex B. Reviewer: Codex A/founder as needed.
  - Architecture reference:
    `docs/codex-b-architecture/PHASE_30B_GOLDEN_PATH_HARDENING_CONTRACT.md`.
  - Status: done 2026-06-22 by Codex B. P30B is PASS to open. The active goal is
    to make the accepted P30A golden path durable, reproducible, and
    founder-demo-ready through DB-backed integration tests, clear fixture
    boundaries, a stable synthetic demo seed, and a founder-demo script. No
    Dashboard, Account Details, new public evidence, provider, Agent Console
    composer, runtime-tool, broker/order, or broader product expansion should
    begin unless it directly unblocks the golden path.

- `P30B-T1` - DB-backed golden-path integration tests.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: add backend integration tests that exercise the real route spine for
    one stock/ETF flow and one simple options flow, preferably
    `cash_secured_put`: `POST /trade-reviews/portfolio-preview` ->
    `saved_review_source_reference` -> `POST /users/{uid}/reports/from-trade-review`
    -> saved artifact/evidence package -> explicit
    `POST /users/{uid}/reports/{thread_id}/agent-team-report` -> report
    list/detail readback -> regeneration/retry.
  - Required assertions: backend-owned saved source and scope are used; client-
    supplied mutable scope/summary fields are ignored after source resolution;
    saved reports do not silently recompute from current account selector state;
    regeneration preserves saved source, scope, deterministic summary, saved
    public evidence, and source timestamps; options-specific caveats remain
    visible and honest; cross-user/malformed source refs fail closed; forbidden
    private fields and unsafe trading/action wording cannot be persisted or
    generated.
  - Hard boundary: tests first. Do not add fields, endpoints, migrations, storage
    behavior, providers, public sources, frontend work, live calls, LLM/
    TradingAgents/runtime tools, broker/order flows, frontend math, raw private
    data, logs, screenshots, or advice/action wording unless a specific gap is
    documented and separately approved by Codex B.
  - Status: done 2026-06-23 by Codex C; Codex B review PASS after one narrow
    blocker fix. Added DB-backed golden-path integration coverage for
    `stock_buy` and `cash_secured_put` through portfolio-preview,
    saved-source reference, saved artifact/evidence package, explicit Agent
    Team generation, report list/detail readback, and regeneration. The test
    preserves reviewed opaque app-owned `account_reference` in saved scope while
    keeping raw provider/account identifiers, raw payloads, buying power, unsafe
    action wording, and forbidden keys out of saved/generated/readback payloads.
    Local DB-marked cases skipped under the disposable-DB safety gate; a
    disposable DB-enabled smoke later covered the route chain.

- `P30B-T2` - Stable synthetic demo seed.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-23 by Codex C; Codex B contract/privacy/safety review
    PASS. Added a backend-owned seed
    helper and manual local/internal script:
    `backend/app/services/golden_path_demo_seed.py` and
    `backend/scripts/manual/seed_golden_path_demo.py`. The seed is separate from
    the Skyframe fixture overlay, idempotently creates one synthetic demo user
    plus one synthetic broker-account row, and can soft-reset saved
    report/source rows for only that demo user. Invocation is dry-run by default;
    writes require `python3 scripts/manual/seed_golden_path_demo.py --apply`,
    with optional `--reset-saved-outputs`. Focused tests cover production-like
    environment rejection, idempotency, route usability for `stock_buy` and
    `cash_secured_put`, no raw synthetic provider identifiers in route payloads,
    and reset behavior. Local verification: focused P30B seed/report/trade-review
    suites passed with DB-backed cases skipped by the existing disposable-DB
    safety gate; service/script compile check and `git diff --check` passed.
    Disposable DB-enabled demo-readiness smoke later covered the seed path.

- `P30B-T3` - Fixture boundary cleanup.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-23 by Codex C; Codex B contract/privacy/safety review
    PASS. Added boundary docstrings to
    `backend/app/services/skyframe_fixtures.py`,
    `backend/app/services/golden_path_demo_seed.py`, and
    `backend/scripts/manual/seed_golden_path_demo.py`: Skyframe remains a
    stateless, header-gated private-safe smoke overlay, while the Golden Path
    demo seed is a local/internal synthetic DB seed that uses real routes and
    storage. Added static tests proving the Skyframe module does not import the
    demo seed and the demo seed does not depend on Skyframe fixture headers.
    Verification: focused fixture/seed suites passed with DB-backed seed tests
    skipped by the existing disposable-DB safety gate; related report/
    trade-review and agent suites remained green; `git diff --check` passed.

- `P30B-T4` - Founder demo script and narrow UX polish.
  - Owner: Claude A or Codex F. Reviewer: Claude B; Codex B if copy, privacy,
    report-state, or read-contract semantics change.
  - Status: done 2026-06-23 by Codex C for docs-only script; Codex B
    contract/privacy/safety review PASS. Added
    `docs/shared/PHASE_30B_FOUNDER_DEMO_SCRIPT.md`, covering setup with the
    stable synthetic seed, one stock/ETF flow, one `cash_secured_put` flow,
    explicit saved-report generation, historical readback, caveat talking
    points, forbidden wording, and the P30B-T5 smoke checklist. No frontend or
    production behavior changed. Any future UI polish remains owned by Claude
    A/Codex F and should stay limited to clarifying the read-only review-desk
    loop.

- `P30B-T5` - Demo readiness smoke.
  - Owner: Claude A or Codex F. Reviewers: Claude B and Codex B.
  - Status: done 2026-06-23 by Claude A; Claude B visual/safety review PASS
    2026-06-23 and Codex B contract/privacy/safety review PASS 2026-06-23.
    Demo-readiness smoke passed against the stable synthetic seed on disposable
    `gp-smoke` DB with no Skyframe fixtures for stock/ETF and
    `cash_secured_put` selected-account flows: preview -> save evidence snapshot
    -> Reports -> explicit Agent Team generation -> report detail/readback.
    Verified no auto-generation, historical saved evidence, honest scope/
    freshness/caveats/provenance/timestamps, no unsafe trading/action wording,
    no private/raw IDs/values/payloads/prompts/traces/secrets, no overflow at
    1024/1280/1440 light/dark, and console clean except known React Router v7
    future warnings. Preview-only raw scope-note codes accepted for demo;
    friendly labels deferred. `/portfolio-context` visible `ctx_` references
    are outside the demo flow and non-blocking.

- `P30B-T5A` - Backend fixes for Golden Path demo-readiness smoke blockers.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-23 by Codex C; Codex B contract/privacy/safety review
    PASS. Fixed two backend smoke
    blockers found by Claude A in a disposable DB run: the Golden Path seed email
    now uses `golden-path-demo@example.com` and repairs legacy `.test` seed rows
    so `GET /users` and `GET /users/{id}` serialize through `UserRead`; selected
    review-account portfolio-preview now sanitizes saved-source scope caveats
    before `SavedReviewArtifactCreateRequest`, keeping private liquidity tokens
    such as `buying_power` out of saved source/report payloads while preserving
    safe caveats like `liquidity_model_unverified` and
    `account_feasibility_not_evaluated`. Future unsafe saved-source validation
    failures return the workspace without a saved source reference instead of
    surfacing a 500. Focused seed/report/trade-review tests and agent suites
    passed locally, with DB-backed cases skipped by the disposable-DB safety gate;
    py_compile and `git diff --check` passed.

- `P30B-T6` - Founder demo acceptance and closeout.
  - Owner: Codex B and Codex A/founder.
  - Status: done 2026-06-23 by Codex A/founder. P30B is accepted for founder
    demo readiness and preserved as the internal MVP validation loop. All
    required hardening slices reviewed PASS: DB-backed route-spine tests, stable
    synthetic demo seed, fixture/demo boundary cleanup, founder demo script,
    backend smoke-blocker fixes, and disposable DB demo-readiness smoke for one
    stock/ETF flow and one `cash_secured_put` flow. Non-blocking future polish:
    replace preview-only raw scope-note codes with friendlier user labels, hide
    or soften visible `ctx_` references on `/portfolio-context` before that page
    enters a user demo, and continue tracking known React Router v7 future
    warnings.

### Closed Context - Phase 30A Golden Path Review Desk Prototype

- `P30A-T0` - Golden path contract and acceptance criteria.
  - Owner: Codex B. Reviewer: founder / Codex A for product direction.
  - Architecture reference:
    `docs/codex-b-architecture/PHASE_30A_GOLDEN_PATH_REVIEW_DESK_CONTRACT.md`.
  - Status: done 2026-06-22 by Codex B. Product direction is accepted as a
    read-only specialist review desk for busy self-directed investors. P30A
    should answer "What would I be ignoring if I acted manually now?", not
    whether a user should make a trade. The phase must use existing approved
    evidence, preserve manual decision-support posture, and avoid new providers,
    runtime tools, frontend math, auto-generation, Agent Console composer work,
    and broker/order flows.

- `P30A-T1` - Backend golden-path gap audit.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: verify one stock/ETF flow and one simple options flow travel end to
    end through portfolio-backed Trade Review, saved review source, saved
    artifact, `SavedEvidencePackageRead`, explicit Agent Team generation,
    report list/detail readback, and regeneration/retry behavior. Identify gaps
    before implementing new fields.
  - Hard boundary: audit first; no new backend fields, endpoints, migrations,
    storage writes, providers, public sources, frontend work, Agent runtime
    tools, broker/API calls, raw private data, or trading-action language unless
    a gap is documented and separately approved.
  - Acceptance criteria: exact endpoints and schemas are named; stock/ETF and
    options flow support is confirmed or gap-listed; saved scope immutability and
    no-hidden-recompute semantics are verified; privacy/safety risks are listed;
    Codex C recommends either "no backend contract change needed" or a smallest
    reviewed contract slice.
  - Next implementation owner: Codex C.

- `P30A-T2` - Agent Team briefing shape.
  - Owner: Claude E. Reviewer: Codex B.
  - Design: `docs/claude-e-agentic/PHASE_30A_T2_AGENT_TEAM_BRIEFING_SHAPE.md`.
  - Status: design PASS 2026-06-22 by Codex B (architecture/privacy/safety,
    review-only). Briefing reshapes the deterministic-template generation around
    "What would I be ignoring if I acted manually now?" using existing
    `SavedAgentTeamSummaryRead` fields only; no new field for P30A-T2. Two
    within-existing-field behavior notes are approved for the implementation
    slice and must be re-reviewed at implementation: (1) populate
    `final_synthesis_markdown` for the `blocked_*`/`deterministic_draft` case;
    (2) carry the manual verification checklist in synthesis prose. The future
    additive `manual_verification_checklist` field stays deferred and requires a
    separate Codex B contract/privacy review before any implementation.
  - Implementation status: P30A-T2A done 2026-06-22 by Codex C; Codex B
    contract/privacy/safety review PASS 2026-06-22. Backend
    deterministic-template wording now frames the saved Agent Team briefing
    around "What would I be ignoring if I acted manually now?", including the
    blocked `deterministic_draft` synthesis and manual verification checklist
    prose inside existing fields. No schema/endpoint/storage/frontend/provider/
    LLM/TradingAgents changes. Verification: focused report schema/API and
    agent suites passed; `git diff --check` clean.

- `P30A-T3` - Trade Review golden-path UX.
  - Owner: Claude A. Reviewer: Claude B; Codex B re-review only if contracts or
    privacy/safety semantics changed.
  - Status: done 2026-06-22 by Claude A; Claude B visual/safety review PASS
    2026-06-22. Frontend-only `SaveReviewSnapshot` handoff copy now frames
    saving as freezing a read-only evidence package for later explicit Reports
    briefing generation. No backend/API/schema/storage/read-field/calculation
    change, no report-generation semantic change, no inferred report id/status/
    scope/provenance, and no private-data exposure. Codex B contract/privacy
    re-review not required.

- `P30A-T4` - Saved Report briefing polish.
  - Owner: Claude A. Reviewers: Claude B and Codex B.
  - Status: done 2026-06-22 by Claude A; Claude B visual/safety review PASS and
    Codex B contract/privacy/report-state review PASS 2026-06-22. `ReportDetail`
    now presents backend-owned final synthesis as the flagship saved specialist
    briefing while keeping deterministic facts/provenance beneath it. The
    deterministic-draft banner is suppressed only when a saved
    `deterministic_draft` already carries backend-owned synthesis prose; report
    state remains visible in the header. No read-contract/status/schema/backend
    change.

- `P30A-T5A` - Private-safe Reports fixture fidelity.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-22 by Codex C; Codex B fixture contract/privacy/safety
    review PASS 2026-06-22. The read-only Skyframe fixture now includes a
    synthetic `deterministic_draft` report with incomplete-review briefing prose
    and updates the `full_agent_report` fixture to the P30A four-bucket briefing
    shape. GET/read-only boundary and activation gates remain intact.

- `P30A-T5B` - Private-safe interactive golden-path fixture coverage.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: done 2026-06-22 by Codex C; review-only subagent PASS and Codex B
    accepted PASS. Fixture-only POST coverage now exists for
    `POST /trade-reviews/portfolio-preview`,
    `POST /users/{uid}/reports/from-trade-review`, and
    `POST /users/{uid}/reports/{thread_id}/agent-team-report`. Fixtures are
    stateless, private-safe, synthetic-only, explicitly gated, and do not echo
    incoming user ids, report ids, account refs, context refs, unsupported
    source refs, or test symbols. No production route behavior, schema,
    endpoint definition, storage, migration, frontend, provider, DB, LLM,
    EDGAR, TradingAgents, web, or MCP change.

- `P30A-T5C` - Private-safe connected golden-path smoke.
  - Owner: Claude A. Reviewer: Claude B.
  - Status: done 2026-06-22 by Claude A; Claude B visual/safety review PASS.
    Connected private-safe smoke passed with reviewed fixtures for stock/ETF and
    `cash_secured_put` interactive flows. The smoke verified Trade Review
    portfolio-backed result, save snapshot idle/saved states, Reports manual
    generation, source snapshot, full Agent Team report, deterministic draft,
    agent unavailable, and validation failed states across 1024/1280/1440 in
    light and dark. No horizontal overflow, no console errors except known
    React Router future-flag warnings, no unsafe wording, no raw private refs or
    save refs (`trrev_`/`svrev_`) rendered, no auto-generation, and no frontend
    faking. Transient smoke files and the user-authorized `frontend/.env.local`
    were removed after teardown.

- `P30A-T6` - Founder acceptance and closeout.
  - Owner: Codex B and Codex A.
  - Status: done 2026-06-22 by Codex A/founder. P30A is accepted as the first
    coherent Golden Path Review Desk Prototype. The accepted loop covers one
    stock/ETF flow and one `cash_secured_put` flow from portfolio-backed Trade
    Review through saved evidence snapshot, explicit Agent Team briefing
    generation, and reopened saved report. Acceptance preserves the product
    framing "What would I be ignoring if I acted manually now?", no
    advice/execution posture, no new provider/source expansion, and frozen
    historical report evidence.

### Closed Context - Phase 29C Public Evidence

The EDGAR `public_company_profile` vertical slice is closed through P29C-T5.
The detailed entries below are retained as recent history only; do not treat
them as the next active handoff unless Codex A reopens public-evidence expansion.

- `P29C-T0` - Public evidence source governance and founder decision.
  - Owner: Codex B and founder.
  - Architecture draft:
    `docs/codex-b-architecture/PHASE_29C_PUBLIC_EVIDENCE_SOURCE_GOVERNANCE.md`.
  - Current gate: approve the architecture, choose exactly one initial public
    evidence section/source category, and record permitted LLM, persistence,
    display, attribution, retention, and environment uses.
  - Codex B preferred architecture path: `public_company_profile` from an
    official, low-volatility structured source category, with SEC EDGAR
    submissions as the initial architecture reference for U.S. public companies.
    Synthetic/replay data remains the test harness only, not the product source
    direction.
  - Status: architecture drafted 2026-06-19; EDGAR-backed company-profile
    scaffolding is proceeding through T1/T2 review gates. Live source activation
    and any saved-report generation with live EDGAR data remain pending
    source-rights/product owner approval and Codex B review.
  - Next implementation owner after PASS: Codex C for P29C-T1, beginning with an
    offline fail-closed source-policy and provider-neutral adapter interface for
    the approved source candidate. Fake/replay implementations are required for
    tests and local verification, but external calls remain disabled by default
    until a separate approved P29C-T2 source slice.

- `P29C-T1A` - EDGAR company-profile source policy and adapter boundary.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: backend-only source policy, adapter interface, symbol-to-CIK
    resolution boundary, EDGAR submissions normalization contract, replay/fake
    test harness, and validation into the existing `public_company_profile`
    section shape.
  - Hard boundary: no default external calls; no frontend work; no new API/read
    fields; no SEC filing bodies, XBRL facts, news, raw URLs, raw payload
    persistence, Agent Team runtime tools, or private account/portfolio data.
  - Status: done 2026-06-19 by Codex C; Codex B contract/privacy/safety review
    PASS 2026-06-19. Added an
    offline `sec_edgar_submissions` source policy, replay-only adapter boundary,
    exact symbol-to-CIK resolution, and normalization into
    `public_company_profile` without new frontend fields/endpoints/storage.
    Verification: `tests/unit/test_report_agent_schemas.py` (66 passed);
    `tests/api/test_reports.py tests/services/agent_team/
    tests/services/agent_eval` (213 passed, 14 DB-gated skips, 2 deselected).
    Stop before any live EDGAR smoke or P29C-T2 production-source slice until a
    separate Codex B contract/privacy/safety review PASS.

- `P29C-T1B` - EDGAR live-client readiness hardening.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: backend-only hardening for the EDGAR source boundary before any live
    smoke. Add explicit source-policy fields for user-agent, request timeout,
    response-size cap, rate-limit budget, allowed runtime environments, and
    disabled-by-default external access; add tests for duplicate ticker rows,
    invalid CIK values, rejected/absent user-agent policy, and fail-closed client
    errors.
  - Hard boundary: no default external calls; no live EDGAR smoke; no frontend
    work; no new API/read fields; no storage changes; no SEC filing bodies, XBRL
    facts, news, raw URLs, raw payload persistence, Agent Team runtime tools, or
    private account/portfolio data.
  - Status: done 2026-06-19 by Codex C; Codex B contract/privacy/safety review
    PASS 2026-06-19 after an overlong-CIK blocker fix. Added explicit
    live-client readiness policy fields for external access, runtime
    allowlisting, declared user-agent, timeout, response-size cap, and request
    budget while preserving replay-only default tests and no live client.
    Added fail-closed tests for duplicate ticker rows, invalid CIK, missing
    live user-agent policy, overlong numeric CIK, sanitized client exceptions, disabled-policy
    no-call behavior, and replay success/package validation. Verification:
    `tests/unit/test_report_agent_schemas.py` (72 passed);
    `tests/api/test_reports.py tests/services/agent_team/
    tests/services/agent_eval` (213 passed, 14 DB-gated skips, 2 deselected).
    Stop for Codex B review before any P29C-T2 live-source activation or saved
    report generation with live EDGAR data.

- `P29C-T2` - Approved EDGAR single-source acquisition slice.
  - Owner: Codex C. Reviewers: Codex B and source-rights/product owner.
  - Scope candidate: wire a disabled-by-default SEC EDGAR submissions HTTP
    client behind the reviewed P29C-T1A/T1B source policy, with injected
    transport tests only by default. Activation must require an approved
    declared user-agent, local/internal runtime gating, request timeout,
    response-size cap, request-budget/rate-limit controls, and explicit
    `external_access_enabled`.
  - Hard boundary: no default external calls; no frontend work; no new API/read
    fields; no storage changes; no filing bodies, XBRL facts, news, raw URLs,
    raw payload persistence, web search, scraping, Agent Team runtime tools,
    private account/portfolio data, or advice/execution wording.
  - Status: Codex B contract/privacy/safety review PASS 2026-06-20 after Codex C
    implementation of the disabled HTTP acquisition seam. Added
    `EdgarCompanyProfileHttpClient` and `UrllibEdgarHttpTransport` behind the
    reviewed live-readiness policy; default projection remains offline unless a
    caller explicitly supplies a live-ready policy and client. Tests use an
    injected fake transport only and cover policy rejection, successful
    synthetic transport read, request-budget enforcement, and existing
    replay/package validation. Verification:
    `tests/unit/test_report_agent_schemas.py` (75 passed);
    `tests/api/test_reports.py tests/services/agent_team/
    tests/services/agent_eval` (213 passed, 14 DB-gated skips, 2 deselected).
    Source-rights/product owner approval remains pending. Stop before any live
    EDGAR smoke or saved report generation with live EDGAR data.

- `P29C-T2A` - EDGAR source-rights/product approval gate.
  - Owner: founder / Codex A. Reviewer: Codex B for architecture consistency.
  - Scope: no code. Decide whether SEC EDGAR submissions metadata may be used
    for local/internal live smoke and later saved-report evidence as
    `public_company_profile`.
  - Required decision record: allowed environments, automated retrieval,
    LLM-use of normalized facts, saved-report persistence, display/attribution
    wording, retention/cache limits, refresh limits, screenshots/exports, and
    prohibited content.
  - Hard boundary: approval may cover only normalized company-profile identity
    facts from submissions metadata. It does not approve filing bodies, XBRL
    facts, news, raw URLs, raw payload persistence, frontend EDGAR calls,
    Agent Team runtime tools, broker/private data, or any trading-action
    language.
  - Status: approved with limits 2026-06-20 by Codex A; architecture boundary
    recorded by Codex B in
    `docs/codex-b-architecture/PHASE_29C_PUBLIC_EVIDENCE_SOURCE_GOVERNANCE.md`.
    Approved only for local developer live smoke, internal test/demo, and
    internal saved-report evidence generation. Production/public SaaS retrieval
    at scale, background crawling, bulk ingestion, filing-body extraction,
    frontend EDGAR calls, and Agent Team runtime EDGAR tools remain prohibited.

- `P29C-T2B` - Local/internal EDGAR live smoke for `public_company_profile`.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: backend-only local/internal live smoke through the disabled-by-default
    EDGAR seam. Use the reviewed `EdgarCompanyProfileHttpClient` with explicit
    `external_access_enabled`, approved local/internal runtime, declared
    SEC-compliant user-agent with contact email, request timeout, response-size
    cap, tiny per-run budget, and conservative process-wide request rate.
  - Required behavior: fetch only one company profile lookup for one approved
    test underlying; normalize only approved `public_company_profile` identity
    facts; persist no raw SEC payload; degrade failures to `not_available` /
    provider unavailable without breaking report generation; keep default tests
    fake/injected/offline.
  - Hard boundary: no production use; no frontend work; no new API/read fields;
    no schema/storage expansion beyond existing saved normalized evidence; no
    filing bodies, HTML filing text, accession document text, exhibits, long
    excerpts, XBRL facts, insider transactions, filing/event interpretation,
    news interpretation, raw URLs, raw payload persistence, frontend EDGAR
    calls, Agent Team runtime tools/web search, broker/account/portfolio/private
    data, trading-action language, buy/sell/hold conclusions, or SEC endorsement
    wording.
  - Status: done 2026-06-20 by Codex C; Codex B contract/privacy/safety review
    PASS 2026-06-20 after successful bounded local/internal live smoke. Added
    the explicit backend smoke helper, process-wide one-request-per-second
    EDGAR rate limit, short source label, and reviewed caveat/limitation copy.
    Offline verification:
    `tests/unit/test_report_agent_schemas.py` (76 passed);
    `tests/api/test_reports.py tests/services/agent_team/
    tests/services/agent_eval` (213 passed, 14 DB-gated skips, 2 deselected).
    Initial sandbox probe failed closed with `edgar_replay_unavailable`; the
    approved network smoke then returned `provider_reference`,
    `availability=available`, `freshness_category=fresh`, source label
    `SEC EDGAR metadata - company profile only`, two expected requests, and
    normalized facts only: `company_name`, `ticker`, `exchange`,
    `cik_reference`, `sic_label`, and `fiscal_year_end`. No raw SEC payload was
    printed or persisted. Stop before any Agent Team/public role behavior
    updates, saved-report generation with live EDGAR data, or broader source
    rollout; each requires a separate reviewed task.

- `P29C-T2C` - Classification semantics hardening for EDGAR
  `public_company_profile`.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: backend-only contract hardening for SEC EDGAR `sic_label`
    classification semantics. Keep `sic_label` inside `public_company_profile`
    as source-specific SEC SIC regulatory metadata; do not add GICS, ICB,
    NAICS, broker/vendor sector fields, new frontend fields, or a new evidence
    section.
  - Hard boundary: no live EDGAR calls; no frontend work; no new API/read
    fields; no filing-body extraction, XBRL facts, raw URLs, raw payload
    persistence, inferred sector/industry labels, classification-driven
    eligibility, portfolio rules, trade gating, broker/account/private data, or
    trading-action language.
  - Status: done 2026-06-21 by Codex C; Codex B contract/privacy/safety review
    PASS 2026-06-21. Added explicit caveat wording that SEC SIC
    metadata may be broad, legacy, and may lag company changes. Added
    regression coverage proving EDGAR `sic_label` remains source-specific and
    replayed `sector`, `industry`, `subindustry`, and `peer_group` fields are
    not normalized or surfaced. Verification:
    `tests/unit/test_report_agent_schemas.py` (77 passed);
    `tests/api/test_reports.py tests/services/agent_team/
    tests/services/agent_eval` (213 passed, 14 DB-gated skips, 2 deselected).

- `P29C-T3A` - Generation-time EDGAR `public_company_profile` integration for
  saved Agent Team reports.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: backend-only wiring so explicit local/internal Agent Team report
    generation can attach reviewed EDGAR `public_company_profile` evidence to
    the same `SavedEvidencePackageRead` instance used for role projection,
    package-aware validation, and persistence. The implementation must be
    disabled by default and must support injected/fake clients for tests.
  - Required behavior: acquire EDGAR only during an explicit backend report
    generation workflow; freeze the normalized profile in the saved artifact;
    opening or regenerating an existing saved report must read/reuse the saved
    normalized profile and must not re-fetch EDGAR; unavailable/failure states
    degrade honestly without breaking deterministic report generation.
  - Hard boundary: local/internal only; no production/public SaaS retrieval; no
    background refresh; no frontend work; no new API/read fields unless Codex B
    separately approves; no raw SEC payload persistence; no filing bodies, HTML,
    accession document text, exhibits, long excerpts, XBRL facts, insider
    transactions, filing/event interpretation, news interpretation, raw URLs,
    Agent Team runtime EDGAR tools/web search, broker/account/portfolio/private
    data, inferred sector/industry labels, classification-driven eligibility,
    portfolio rules, trade gating, trading-action language, buy/sell/hold
    conclusions, or SEC endorsement wording.
  - Status: done 2026-06-21 by Codex C; Codex B contract/privacy/safety review
    PASS 2026-06-21. Added optional injected EDGAR policy/client parameters to
    saved Agent Team report generation. When a saved artifact has no persisted
    public evidence yet, the same `SavedEvidencePackageRead` instance used for
    role projection and package-aware validation is updated with normalized
    public evidence and persisted back to `saved_artifact_json.public_evidence`.
    Regeneration reuses saved public evidence and does not refresh EDGAR. Added
    DB-backed regression coverage for injected EDGAR profile
    persistence/readback, report-detail no-refetch behavior, regeneration reuse,
    unavailable-provider degradation, raw payload/URL/private-token
    sanitization, and no sector/industry/subindustry/peer-group surfacing.
    Verification:
    `tests/unit/test_report_agent_schemas.py` (77 passed);
    `tests/api/test_reports.py tests/services/agent_team/
    tests/services/agent_eval` (213 passed, 16 DB-gated skips, 2 deselected).
    Stop before frontend display changes, broader EDGAR use, or any
    production/public-source activation.

- `P29C-T3B` - Public-role behavior design for saved EDGAR
  `public_company_profile` evidence.
  - Owner: Claude E. Reviewer: Codex B.
  - Scope: design-only update to define how public analyst roles may consume
    saved normalized EDGAR `public_company_profile` evidence that was frozen at
    report generation time. The design should cover role wording,
    citations/section keys, degradation when the profile is unavailable, and PM
    synthesis boundaries.
  - Required behavior: use EDGAR company identity/listing metadata as context
    only; allow source-specific SEC SIC wording only as broad regulatory
    classification metadata; explicitly caveat that SIC can be broad, legacy,
    and lag company changes; keep public roles secondary to portfolio-aware
    roles; preserve package-aware validation and saved-evidence reproducibility.
  - Hard boundary: no runtime EDGAR tools, no web search, no frontend fields, no
    new backend fields/endpoints/storage, no filing bodies/XBRL/news/insider
    interpretation, no raw URLs or raw payloads, no normalized sector/industry
    inference, no classification-driven eligibility/portfolio rules/trade
    gating, no broker/account/portfolio/private data, no SEC endorsement
    wording, and no advice/recommendation/buy/sell/hold/order/execution/safe- or
    ready-to-trade language.
  - Status: done 2026-06-21 by Claude E (design-only); Codex B
    architecture/privacy/safety review PASS 2026-06-21. Design defines
    fundamentals-analyst and PM-synthesis use of saved EDGAR
    `public_company_profile` as company identity/listing metadata context only;
    news/technical remain excluded by `ROLE_ALLOWED_EVIDENCE_KEYS` and
    `_PUBLIC_ROLE_SECTION_KEYS`. Confirms the full Codex-A attribution sentence
    ("...Not investment advice or a trading signal.") collides with both
    `_SAVED_REVIEW_PROHIBITED_PHRASES` and `REPORT_PROHIBITED_PHRASES` and is
    therefore routed to frontend display chrome (P29C-T4), not stored in
    validated fields; the backend/agent layer conveys substance via the short
    source label + SIC caveat. Keeps digit-bearing facts (`cik_reference`,
    `fiscal_year_end`) in structured facts out of generated prose to avoid
    `INVENTED_LEVEL_PATTERNS` false positives. Preserves package-aware validation
    and saved-evidence reproducibility (same `SavedEvidencePackageRead`, no
    refetch). No new backend fields/endpoints/storage; offline synthetic test
    matrix specified in
    `docs/claude-e-agentic/PHASE_29C_T3B_PUBLIC_ROLE_EDGAR_PROFILE_DESIGN.md`.
    Next: Codex C implements the deterministic fundamentals/PM narrative slice
    per this design (offline, synthetic); full attribution sentence deferred to
    the P29C-T4 frontend display task. Stop for Codex B review before that
    implementation.

- `P29C-T3C` - Deterministic public-role EDGAR company-profile narrative
  implementation.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: backend-only deterministic report-generation wording. Implement the
    reviewed P29C-T3B design without schema changes, endpoint changes, frontend
    work, storage expansion, runtime EDGAR tools, web search, or EDGAR refetch
    during regeneration/readback.
  - Required behavior: `fundamentals_analyst` may complete when saved
    `public_company_profile` is available/limited; narrative treats EDGAR
    metadata as company identity/listing context only; digit-bearing identity
    values such as CIK and fiscal year-end stay in structured facts, not prose;
    SEC SIC is described only as source-specific regulatory metadata with the
    broad/legacy/may-lag caveat; PM synthesis may reference identity context as
    background only; news and technical continue to ignore
    `public_company_profile`.
  - Hard boundary: no full attribution sentence containing "investment advice"
    in stored/generated backend fields; no raw SEC URLs, raw payloads, filing
    bodies, XBRL facts, insider data, news interpretation, broker/account/
    private data, inferred sector/industry/subindustry/peer-group/exposure/
    eligibility fields, classification-driven portfolio rules/trade gating,
    advice/recommendation/buy/sell/hold/order/execution/safe-to-trade/
    ready-to-trade/guaranteed-return/AI-stock-picker wording, or SEC
    endorsement wording.
  - Status: done 2026-06-21 by Codex C; Codex B contract/privacy/safety review
    PASS 2026-06-21. Added a deterministic fundamentals
    company-profile formatter that names present identity fact categories
    without inlining literal CIK/fiscal-year values or company/SIC values into
    generated prose. PM synthesis now references saved company identity/listing
    context only as analysis-only background when a saved profile is citable.
    Tightened public-role degradation so mixed `not_available` profile +
    `not_reviewed` sections returns `public_evidence_not_available`. Added
    offline tests for available profile completion, limited profile with and
    without SIC, unavailable profile degradation, news/technical boundary,
    PM background wording, full-attribution rejection, digit-free prose, and
    saved-evidence regeneration reuse. Verification:
    `tests/unit/test_report_agent_schemas.py` (82 passed);
    `tests/api/test_reports.py tests/services/agent_team/
    tests/services/agent_eval` (213 passed, 16 DB-gated skips, 2 deselected).
    Stop before frontend P29C-T4 implementation, broader EDGAR use, or any
    production/public-source activation.

- `P29C-T4A` - Read-only EDGAR public-evidence attribution projection for saved
  report reads.
  - Owner: Codex C. Reviewer: Codex B.
  - Scope: backend-only additive read projection so P29C-T4 frontend can render
    SEC EDGAR attribution chrome without inferring provenance from
    provider-neutral section keys. Add nullable `source_key` to frozen
    `SavedPublicEvidenceSectionRead`; populate EDGAR normalized
    `public_company_profile` with `source_key="sec_edgar_submissions"`; expose
    nullable `ReportThreadRead.public_evidence_attribution` inherited by report
    detail reads.
  - Projection contract: return `null` unless frozen
    `saved_artifact_json.public_evidence.public_company_profile` is
    `available`/`limited` and has reviewed EDGAR `source_key` +
    `source_label`. When present, expose only `section_key`,
    `source_key`, `source_label`, `availability`, and `has_sic_label`. Do not
    expose literal SIC value, CIK, fiscal year-end, company name, ticker,
    exchange, facts, raw URLs, raw payloads, limitations arrays, or the full
    public evidence package.
  - Hard boundary: no EDGAR fetch, recomputation, storage write, DB migration,
    endpoint change, frontend work, full attribution sentence containing
    "investment advice" in backend fields, provider calls, frontend EDGAR calls,
    Agent Team runtime tools/web search, broker/account/private data, or
    trading-action wording.
  - Status: done 2026-06-21 by Codex C; Codex B contract/privacy/safety review
    PASS 2026-06-21. Added the additive read model and frozen
    source-key provenance required to avoid frontend inference. Added unit
    coverage for available and limited EDGAR attribution, null behavior without
    stored source key, forbidden literal/private/source leakage, and schema
    sweeps; updated DB-gated report API assertions for list/detail projection
    when a saved EDGAR profile exists or is unavailable. Verification:
    `tests/unit/test_report_agent_schemas.py` (85 passed);
    `tests/api/test_reports.py` (16 DB-gated skips locally);
    `tests/unit/test_report_agent_schemas.py tests/services/agent_team/
    tests/services/agent_eval` (298 passed, 2 deselected).
    Claude A may resume P29C-T4 frontend chrome using
    `public_evidence_attribution` only.

- `P29C-T4` - Frontend EDGAR attribution display chrome for saved reports.
  - Owner: Claude A. Reviewers: Codex B for attribution/privacy/safety wording;
    Claude B for visual/Skyframe review.
  - Scope: frontend-only display chrome in Reports detail surfaces that can show
    the approved EDGAR attribution/caveat as UI copy derived from existing
    reviewed report/source state. The full attribution sentence containing
    "investment advice" is allowed only as non-persisted frontend display chrome;
    it must not be added to backend generated report fields, saved artifacts,
    Agent Team role summaries, evidence facts, or validators.
  - Required display wording: full attribution sentence "Source: SEC EDGAR
    submissions metadata. Company identity and listing metadata only. Not
    investment advice or a trading signal."; short label "SEC EDGAR metadata -
    company profile only"; caveat "EDGAR metadata may lag company changes and
    does not include financial analysis, filing text, or investment
    conclusions."; SIC caveat if SIC context is shown: "SEC SIC metadata may be
    broad, legacy, and may lag company changes."
  - Hard boundary: no backend/API/schema/storage changes; no new read fields
    unless Codex B separately approves; no fabricated EDGAR availability,
    provenance, freshness, or coverage; no raw SEC URLs, raw payloads, filing
    bodies, XBRL facts, insider data, news interpretation, broker/account/
    private data, inferred sector/industry/subindustry/peer-group/exposure/
    eligibility fields, classification-driven portfolio rules/trade gating,
    advice/recommendation/buy/sell/hold/order/execution/safe-to-trade/
    ready-to-trade/guaranteed-return/AI-stock-picker wording, or SEC endorsement
    wording.
  - Status: done 2026-06-21 by Claude A; Claude B visual/Skyframe review PASS
    2026-06-21; Codex B attribution/privacy/safety wording and contract-fidelity
    review PASS 2026-06-21. Added frontend-only SEC EDGAR attribution chrome in
    the saved-report provenance area, gated solely by backend-owned
    `public_evidence_attribution` with `source_key="sec_edgar_submissions"` and
    `availability` in `available`/`limited`. The full attribution sentence
    containing "investment advice" remains fixed frontend display boilerplate
    only and is not persisted, generated, or sent to backend/agent/saved fields.
    The component exposes no literal SIC value, CIK, fiscal year-end, company
    name, ticker, exchange, facts, raw URLs, payloads, or limitations arrays.
    Visual review confirmed the Skyframe treatment.

- `P29C-T5` - EDGAR `public_company_profile` vertical-slice closeout and next
  public-evidence source decision.
  - Owner: Codex B. Reviewer: founder / Codex A for product/source direction.
  - Scope: architecture/planning only. Summarize the completed EDGAR
    `public_company_profile` path from source governance through saved-report
    display; identify any docs/contract cleanup; decide whether to pause, commit
    checkpoint, or start the next reviewed public-evidence source/category.
  - Hard boundary: no code, no new provider/source task, no production/public
    activation, no background refresh, no filing-body/XBRL/news expansion, no
    frontend EDGAR calls, no Agent Team runtime EDGAR tools/web search, no raw
    payload persistence, no broker/account/private data, and no trading-action
    wording.
  - Status: done 2026-06-21 by Codex B. The EDGAR
    `public_company_profile` vertical slice is complete through saved-report
    display: source governance, disabled-by-default source seam, local/internal
    smoke boundary, classification semantics hardening, generation-time
    persistence, public-role behavior and deterministic narrative, read-contract
    attribution, and frontend provenance chrome all passed their required review
    gates. Worktree checkpoint contains only the accepted P29C code/docs files.
    Next decision belongs to founder/Codex A: pause public-evidence expansion or
    select the next reviewed source/category.

## Coordination Checkpoint

Checkpoint status: the accepted P29B public-evidence, Reports, Skyframe, and
private-safe fixture work was committed and pushed to `main` at `381183f` on
2026-06-19. The active plan was then compacted; its pre-compaction snapshot is
`docs/shared/implementation_plan_archive_2026-06-19.md`.

Resolved maintenance debt:

- `MAINT-BE-1` removed the seven previously known failures while preserving
  production behavior; the default backend suite is clean apart from legitimate
  DB-gated skips and configured deselections.

## Paused Or Deferred

- Phase 21A realtime Agent Console: paused; composer remains disabled.
- Market-data provider selection: parked until production/display licensing
  planning.
- Market Mood production/public display: blocked on source/rights review.
- Economic Awareness frontend expansion: paused unless PM reactivates.
- Account group/scope management: deferred until Codex A product decision.
- Runtime public-data tools, private/public MCP, live public web search,
  report export/share/version comparison, auto-generation after save, and any
  broker action or execution workflow are deferred.
- Full tax-lot/history reconstruction from transactions: deferred; do not infer
  tax lots from activity/order data without a new reviewed contract.

## Handoff Format

Every implementation/review handoff should use one fenced `text` block, not a
`markdown` block, and should avoid nested triple backticks. Follow
`docs/shared/AGENT_REPORT_FORMAT.md`.
