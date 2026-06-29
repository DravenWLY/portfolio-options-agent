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
  - Status: next. Implement the in-process registry, safe structured tool-request
    shape, safe `ToolResult` envelope, initial mock/offline tool functions over
    existing saved evidence, and tests for tier enforcement/private-data
    rejection. No live providers, new sources, frontend changes, MCP,
    TradingAgents runtime, or LangGraph.

- `P33A-T2` - Planner, Evidence Auditor, and role behavior design.
  - Owner: Claude E. Reviewer: Codex B.
  - Status: pending P33A-T1 envelope. Define planner catalog scope, role
    projections, citation graph, one bounded critique/re-pass rule, and output
    expectations over the P33A-T1 tool envelopes.

- `P33A-T3` - First tool-mediated saved-report run.
  - Owner: Codex C + Claude E. Reviewer: Codex B.
  - Status: pending T1/T2. Wire a mock-first saved-report generation path that
    uses backend-executed tools over existing saved evidence only.

- `P33A-T4` - Reproducibility freeze contract.
  - Owner: Codex C. Reviewer: Codex B.
  - Status: pending T3. Persist used tool-result envelopes through an additive
    reviewed saved-report or saved-evidence contract; report readback must not
    re-fetch tools or recompute from current state.

- `P33A-T5` - Tool-mediated Agent Team evaluation harness.
  - Owner: Claude E. Reviewer: Codex B.
  - Status: pending T3/T4. Add synthetic/offline eval cases for useful
    ignored-risk discovery, honest missing-data handling, citation completeness,
    contradiction rejection, no private leaks, and no advice/order wording.

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
  - Status: review PASS 2026-06-29 by Claude B (visual/UX/accessibility/safety-
    copy). Additive collapsed supporting-provenance band rendered after
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
    `LOCAL_DEV_ACCESS_TOKEN`). Deferred polish: neutral icon for not_available
    gaps; optionally surface finding/source caveat codes; optionally strengthen
    the demo badge for the founder demo.

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
