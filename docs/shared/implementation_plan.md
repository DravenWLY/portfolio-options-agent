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
- Phase 29B public evidence architecture is active. P29B-T0, P29B-T1, and
  P29B-T2 are complete and reviewed PASS.

Reference docs:

- `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_28A_SAVED_REVIEW_ARTIFACT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`
- `docs/codex-b-architecture/PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md`
- `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
- `docs/claude-e-agentic/PHASE_29A_T5_REPORT_GENERATION_UX_POLICY.md`
- `docs/claude-e-agentic/PHASE_29B_T2_PUBLIC_ROLE_AGENTIC_DESIGN.md`

Detailed verification history is archived in:

- `docs/shared/implementation_plan_archive_2026-06-15.md`
- `docs/shared/CHANGELOG.md`
- `docs/shared/completed_phases_log.md`

## Active Work

### Phase 29B - Reviewed Public Evidence For Public Analyst Roles

Goal:

- Enable currently skipped public analyst roles (`fundamentals_analyst`,
  `news_analyst`, `technical_analyst`) to contribute to saved Agent Team reports
  from reviewed public evidence without widening private brokerage/account data
  exposure.
- Keep reports reproducible from generation-time evidence.
- Preserve evidence-package-first architecture and defer runtime agent tools by
  default.

Completed:

- `P29B-T0` - Public agent evidence architecture contract: accepted.
- `P29B-T1` - Backend public evidence contract and projection design: done by
  Codex C; Codex B review PASS.
- `P29B-T2` - Public role agentic design: done by Claude E; Codex B review PASS.

Current next task:

- `P29B-T3A` - Backend public evidence persistence and projection seam.
  - Owner: Codex C.
  - Reviewer: Codex B.
  - Scope: implement the backend-owned generation-time `public_evidence`
    persistence/readback seam and role-scoped public-evidence projection
    contract. This comes first because Claude E needs a stable backend evidence
    shape and reproducibility path before wiring public-role behavior.
  - Acceptance:
    - generation-time `public_evidence` can be persisted in the saved artifact /
      readback path;
    - `SavedEvidencePackageRead.from_saved_review_artifact` reads saved public
      sections when present and defaults to `not_reviewed` only when absent;
    - role-scoped public evidence projections are backend-built from the same
      `SavedEvidencePackageRead` instance used for validation and persistence;
    - no real provider/source, frontend, LLM, TradingAgents, runtime tool, or
      external call is added;
    - default tests are offline, deterministic, and synthetic.
  - Verification:
    - `cd backend && ./.venv/bin/python -m pytest tests/unit/test_report_agent_schemas.py -q`
    - `cd backend && ./.venv/bin/python -m pytest tests/unit/test_report_agent_schemas.py tests/api/test_reports.py tests/api/test_trade_review_workspace.py tests/services/agent_team/ tests/services/agent_eval -q`
    - `git diff --check`
  - Review rule: after implementation and verification, request one Codex B
    review-only sub-agent. Do not mark done until Codex B PASS.
  - Status: done 2026-06-15 by Codex C; Codex B review PASS.
  - Implementation summary: added `public_evidence` to the saved artifact
    readback model and `ReportThread.saved_artifact_json` projection path. During
    explicit Agent Team generation, the backend now builds a generation-time
    public evidence package, uses that same `SavedEvidencePackageRead` for
    `validate_agent_team_report_output(..., evidence_package=evidence)`, and
    persists the same `public_evidence` JSON alongside `agent_summary`.
    `SavedEvidencePackageRead.from_saved_review_artifact` now reads saved public
    evidence when present and defaults to `not_reviewed` only for legacy/source
    artifacts without it. Added `SavedPublicRoleInstrumentContextRead` and
    `SavedPublicRoleEvidenceProjectionRead`, plus
    `build_public_role_evidence_projection(...)`, which narrows public evidence
    for `fundamentals_analyst`, `news_analyst`, and `technical_analyst` to
    role-allowed public sections and minimal instrument context.
  - Verification: `cd backend && ./.venv/bin/python -m pytest
    tests/unit/test_report_agent_schemas.py -q` -> 50 passed.
    `cd backend && ./.venv/bin/python -m pytest
    tests/unit/test_report_agent_schemas.py tests/api/test_reports.py
    tests/api/test_trade_review_workspace.py tests/services/agent_team/
    tests/services/agent_eval -q` -> 337 passed, 28 skipped, 2 deselected
    locally (DB destructive-test guard). `git diff --check` clean. Codex B
    review PASS. Non-blocking T3B handoff: wire public-role generation through
    `build_public_role_evidence_projection(...)` using the already-built
    `SavedEvidencePackageRead` instance, and keep
    `validate_agent_team_report_output(..., evidence_package=evidence)` before
    persistence so unavailable/not-reviewed public sections cannot be cited.

Follow-up tasks:

- `P29B-T3B` - Public role generation wiring and validation behavior.
  - Owner: Claude E.
  - Dependency: P29B-T3A reviewed and PASSed.
  - Reviewer: Codex B; Codex C cross-review if backend seams are touched.
  - Scope: wire public-role behavior from P29B-T2 onto the backend projection
    seam: role-scoped prompt/public-context inputs, skipped/unavailable/
    validation-failed role handling, PM synthesis use of validated public
    summaries, and synthetic positive/negative eval cases.
  - Critical seam: preserve
    `validate_agent_team_report_output(..., evidence_package=evidence)` before
    persistence; this is the package-aware validator call that enforces nested
    public-section availability.
  - Status: done 2026-06-15 by Claude E; Codex B review-only PASS. Public roles
    are wired through `build_public_role_evidence_projection` on the same
    `SavedEvidencePackageRead` instance used for package-aware validation and
    persistence; honest fail-closed degradation matching P29B-T2
    (not_reviewed/not_available/not_applicable -> skipped; assembly failure ->
    unavailable/`public_evidence_provider_unavailable`; limited/stale ->
    completed only with explicit caveat); run-level coverage code
    (`public_evidence_roles_skipped` / `_partial_coverage` / `_roles_included`)
    and dynamic `run_status`. Added `INVENTED_LEVEL_PATTERNS` and
    `SOURCE_LEAK_PATTERNS` guards to `report_output_safety.py` (bare-number
    support/resistance/pivot/target/level and source URLs). Files: backend/app/
    services/reports/agent_team_report.py, backend/app/services/agent_team/
    report_output_safety.py, backend/tests/unit/test_report_agent_schemas.py
    (+9 positive/negative tests). Default not_reviewed behavior and existing P29A
    behavior unchanged; offending generated text never persisted. Verification:
    `tests/unit/test_report_agent_schemas.py` -> 59 passed; the T3B suite
    (`test_report_agent_schemas.py test_reports.py test_trade_review_workspace.py
    tests/services/agent_team/ tests/services/agent_eval`) -> 346 passed, 28
    skipped, 2 deselected; `git diff --check` clean. (7 unrelated full-suite
    failures in cash_balance/option_position/stock_position model-column,
    economic_calendar, and snaptrade adapter tests are pre-existing — confirmed
    by stashing the T3B files and re-running — and out of scope for T3B.)
- `P29B-T3C` - Integrated closeout and docs checkpoint.
  - Owner: Codex B.
  - Scope: close P29B-T3 after T3A/T3B PASS, then update only this active plan,
    changelog, and any required architecture note.
  - Status: done 2026-06-15. T3A and T3B are reviewed PASS; active plan is
    concise; P29B-T4 is the next planned product/frontend step. Commit/push
    checkpoint for T3A/T3B should happen now before frontend/design work.
- `P29B-T4` - Frontend rich report optimization.
  - Owner: Claude A or Codex F.
  - Reviewers: Claude B and Codex B.
  - Dependency: P29B-T3 reviewed and accepted, with stable sample payloads.
  - Scope: optimize Reports UI for richer public + portfolio-aware role output.
    This is where Claude Design or Stitch may be introduced under the timing
    rules in the Phase 29B contract.
  - Planning status: discussion done 2026-06-15 by Claude A (no implementation).
    Founder direction locked: analyst-memo feel; public analysts as secondary
    "market context" beside primary portfolio-aware roles; compact provenance
    trust strip + audit disclosure; 2–3 Claude Design concept directions before
    implementation. Claude Design brief written:
    `docs/claude-a-frontend/PHASE_29B_T4_CLAUDE_DESIGN_BRIEF.md` (synthetic
    payload set for all six report states + role variants, Track A vs Track B
    field boundary, hard rails). Next: founder runs Claude Design with the
    codebase attached → Claude B + Codex B rail-check → pick one direction →
    implement (Stitch vs Claude A decided then). Founder directive: Claude Design
    (the divergent-concept stage) MAY expand beyond the current plan/contract and
    propose additive read fields/structures (the contract's "no new API fields"
    rule binds Stitch, not Claude Design); such expansions are labeled proposals
    routed to Codex C/Codex B before shipping, and the live UI never renders an
    unreviewed field or fabricated value. Open decision (at design review): which
    Track-B expansions to adopt — Track A ships frontend-only, accepted Track-B
    proposals become additive contract changes. Gate: no frontend implementation
    until the direction and sample payloads are agreed.
  - Implementation status: Direction A ("Synthesis Column") implemented 2026-06-16
    by Claude A (frontend only, Track A). Claude B visual/safety review PASS and
    founder acceptance confirmed 2026-06-18. No
    backend/contract change (consumes only existing read fields), so no Codex B
    re-review required. Founder ran Claude Design (handoff bundle extracted to
    `docs/claude-a-frontend/p29b-t4-concepts/bundle/`, directions A "Synthesis
    Column" + B "Desk & Margin"); Direction A chosen for the analyst-memo feel and
    current single-column pane. Built: a compact provenance trust strip (derived
    public coverage · snapshot-saved + report-generated times · saved scope —
    Track A only); roles split into a PRIMARY portfolio-aware band (full serif
    "memo" blocks with explicitly labeled, visually distinct "Agent narrative ·
    analysis only" vs "Deterministic evidence cited · backend-owned" zones) and a
    SECONDARY public "market context" band (compact cards + honest, derived
    coverage note); serif synthesis lede; honest skipped/unavailable copy per
    reason. Track B from the concept (per-section freshness/rights chips, the
    structured coverage meter) is intentionally NOT shipped — it needs an additive
    read field (`public_evidence_coverage` / per-section provenance) via
    Codex C/Codex B; deferred. Files: `frontend/src/components/reports/`
    ReportDetail.tsx, AgentRoleSection.tsx (primary/context variants),
    ReportTrustStrip.tsx (new), ReportProse.tsx (serif display option),
    reportStatus.ts (role split + derived coverage + helpers). No new deps, no
    localStorage, no provider/LLM calls, no frontend math; reviewed fields only.
    Verified: `cd frontend && npm run typecheck` clean; `npm run lint --
    --max-warnings 0` clean; `npm run build` succeeds; `git diff --check` clean.
    Connected-data smoke on `/reports`: primary/secondary bands and zone labels
    render; trust strip shows coverage + both times + scope; public analysts are
    secondary with the honest "not yet enabled" coverage note; no console errors
    (only pre-existing React Router warnings); 0px horizontal overflow at
    1024/1280/1440 in light and dark.
  - Codex A product decision 2026-06-17: Skyframe PASS, Reports-first PASS,
    Direction A product rationale PASS. Codex B routing check 2026-06-17: PASS
    for next review gate; implementation remains Track A only and does not
    require a Codex B contract/privacy re-review unless Claude B finds a new
    field assumption or Track-B element in the live UI. Final status 2026-06-18:
    Claude B PASS + founder acceptance; P29B-T4 Direction A is accepted as the
    Reports reference direction.
  - Rail scaling Phase 1 (floor) implemented 2026-06-16 by Claude A, from a
    Claude B ↔ Claude A design discussion on how the saved-analysis rail scales
    with history. Frontend only — no backend/contract change (consumes existing
    thread fields: `created_at`, `scope_metadata`, derived status). Built: the
    wide rail is now a sticky, independently scrolling container with a sticky
    "Saved analyses · N" header; the list is grouped into date buckets (Today /
    Earlier this week / Earlier this month / by month) with sticky group headers
    so it reads as a calm archive; each row gains a muted secondary scope line
    (`scope_summary_label`, truncated) so near-identical rows disambiguate; at
    ≤1100px (single-column) the rail collapses to a "Saved analyses (N) ·
    {selected title}" disclosure (default closed; picking a report auto-collapses
    it) so the reading pane leads instead of being buried. Newest-first by saved
    time preserved; status stays icon+text; selected/focus-visible intact. Files:
    `frontend/src/hooks/useMediaQuery.ts` (new), `components/reports/
    ReportLibraryList.tsx`, `pages/ReportsPage.tsx`. Volume note: designed for
    tens–low-hundreds; virtualization + server pagination deferred together until
    volume justifies. Phase 2 (search + status filter, client-side over loaded
    threads) is the next slice. Verified: typecheck / lint (--max-warnings 0) /
    build / `git diff --check` clean; connected `/reports` smoke — grouping +
    scope line render, wide rail sticky/scrolls, ≤1100px disclosure
    collapse/expand/auto-collapse works and the pane leads, wide rail restores
    >1100px, no console errors (only React Router warnings), 0px overflow at
    1024/1280/1440 in light and dark. Pending Claude B visual rail-check.
  - Rail scaling Phase 2 (search + status filter) implemented 2026-06-16 by
    Claude A. Frontend only — client-side over the already-loaded threads, no
    backend/contract change. Added a search field (matches saved `title` /
    `report_type` only — display-safe) and a status filter (All / Agent Team
    report / Source snapshot / Draft·unavailable) operating on the derived report
    status; rail count shows "{filtered} / {total}" when active; an honest
    empty-result state with a "Clear search & filter" affordance; controls appear
    in both the wide rail and the ≤1100px disclosure. Selection is independent of
    the filter (a selected report stays open in the pane even if filtered out of
    the rail). Status options stay text labels (never color-only); no advice/order
    wording; no "prompt" token. Files: `frontend/src/components/reports/`
    ReportLibraryControls.tsx (new), reportStatus.ts (filter options + matchers),
    `pages/ReportsPage.tsx`. Verified: typecheck / lint (--max-warnings 0) /
    build / `git diff --check` clean; connected `/reports` smoke — search narrows
    ("DELL" → 1/7), a no-match query shows the empty state + Clear restores the
    full list, the status filter narrows by derived status ("Source snapshot" →
    2/7, all rows source_snapshot), controls present in wide + narrow, no console
    errors, 0px overflow at 1024/1280/1440 in light and dark. Both rail phases
    pending one Claude B visual rail-check. Deferred (unchanged): virtualization +
    server pagination until volume justifies; optional saved-vs-generated sort
    control.
  - Rail search field system-match polish implemented 2026-06-16 by Claude A
    (from a Claude B implementation task; frontend only, Track A). The rail
    search input, its clear (×), and the status select previously fell through to
    the global `:focus-visible` (legacy `--color-accent` blue ring with a 2px
    offset outline). Added component-scoped classes (`.report-rail-search` /
    `.report-rail-select` / `.report-rail-clear`) in globals.css that match
    `.report-thread-button`: rest border `--mp-rule`, hover `--mp-rule-strong`,
    focus-visible `outline:none` + `border-color:var(--mp-accent)` +
    `box-shadow:0 0 0 3px var(--mp-accent-soft)`; `:focus:not(:focus-visible)`
    also clears the outline so no blue ring appears on pointer focus either. The
    global `--color-accent :focus-visible` rule was NOT changed (no app-wide
    ripple). Suppressed the native search clear
    (`::-webkit-search-cancel-button { appearance: none }`) so only the custom ×
    shows. Placeholder corrected to "Search title or type" (the matcher is a
    substring search over title + report_type, not a symbol lookup). Files:
    `frontend/src/styles/globals.css` (new scoped rules), `ReportLibraryControls.tsx`
    (classNames; border/color moved into the classes so hover/focus can
    override). Verified: typecheck / lint (--max-warnings 0) / build /
    `git diff --check` clean; connected `/reports` smoke — all seven scoped rules
    resolve to MP tokens, the legacy blue is gone on both focus paths
    (outline:none confirmed), placeholder + webkit reset correct, 0px overflow at
    1024/1280/1440, no new console warnings. Note: the live keyboard-focus teal
    ring could not be captured in headless preview (`:focus-visible` needs real
    keyboard modality) — rule correctness verified by stylesheet inspection +
    specificity; Claude B to confirm the live ring in the rail-check. Deferred
    (note only): the status `<select>` still has no custom caret/chevron — give it
    a chevron affordance (or a "Status ▾" trigger / small segmented control) with
    the same focus/hover system when picked up.
- `P29B-T5` - Skyframe token unification and Reports sky-surface prototype.
  - Owner: Claude A or Codex F.
  - Reviewer: Claude B visual/safety. Codex B only re-reviews if product safety,
    privacy, report semantics, evidence display rules, or frontend read-contract
    boundaries change.
  - Dependency: P29B-T4 Direction A accepted.
  - Scope: migrate legacy report-adjacent `--color-*` usage toward the canonical
    `--mp-*` token system, then prototype a light sky-blue surface tint on
    Reports only. Sky blue is a surface/atmosphere color, not an action color:
    buttons, links, focus rings, and status indicators must keep
    contrast-safe deeper teal/blue values.
  - Founder guardrail: obvious section/element contrast is mandatory. Pale
    sky-blue surfaces must not blur the page into one low-contrast wash; preserve
    clear section separation through surface steps, rules, spacing, and WCAG AA
    text contrast in light and dark modes.
  - Hard constraints: frontend visual/token work only; no backend contract
    changes, no new read fields, no fabricated report coverage/provenance values,
    no changed report state semantics, no private-data exposure, no advice/order
    wording.
  - Recommended sequence: unify tokens first, prototype the Reports sky-surface
    tint second, run Claude B contrast/visual review third, reconcile `STYLE.md`
    to the shipped token set after the prototype is accepted, then roll out
    per-surface with a conformance checklist. Add a lint guard only after the
    migration baseline is clean, or start with an allowlist warning during
    migration.
  - `P29B-T5A` docs alignment: done 2026-06-18 by Codex F. Root `STYLE.md`
    / Portfolio Copilot Skyframe is the accepted app-wide style source of truth;
    `current_roadmap.md`, `frontend_design_change_playbook.md`, and the
    historical P29B-T4 Claude Design brief now point future Reports styling to
    Skyframe/P29B-T5.
  - `P29B-T5B` implementation handoff: next. Frontend-only Reports pass to
    unify report-adjacent legacy `--color-*` usage toward `--mp-*`, prototype a
    light sky-blue Reports surface tint only, and preserve Skyframe's
    medium-high contrast standard. No new fields/contracts/report semantics,
    backend work, provider calls, storage writes, or frontend financial math.
    Claude B visual/safety review required; Codex B review only if
    contract/privacy/safety/report semantics change.
  - `P29B-T5B` implementation status: done 2026-06-18 by Codex F; Claude B
    visual/safety review PASS 2026-06-19. Added a Reports-only `.reports-skyframe`
    surface layer in `globals.css`, wired the Reports page/rail/reading pane,
    trust strip, synthesis, role cards, evidence/provenance/scope blocks, and
    generation affordance to scoped Reports surfaces while preserving deeper MP
    accent/focus/status values. Migrated the legacy report-history placeholder
    from `--color-*` to `--mp-*`. No new fields/contracts/report semantics,
    backend work, provider calls, storage writes, or frontend financial math.
    Verification: `cd frontend && npm run typecheck`, `npm run lint --
    --max-warnings 0`, `npm run build`, and `git diff --check` all passed.
    Browser smoke not run by default because `/reports` may expose generated or
    private saved-report content without explicit permission.
  - Status: done. P29B-T5A docs alignment complete; P29B-T5B accepted as the
    Reports sky-tint reference. Deferred polish: Reports sidebar/content top
    seam and source-snapshot trust-strip coverage copy.
- `P29B-T6` - Skyframe shared primitive and app-wide token migration.
  - Owner: Claude A or Codex F.
  - Reviewer: Claude B visual/safety. Codex B only re-reviews if product safety,
    privacy, report semantics, evidence display rules, frontend read-contract
    boundaries, or cross-surface product posture change.
  - Dependency: P29B-T5B accepted.
  - Scope: promote the accepted top-only Reports sky-header wash into a shared
    app-shell/page-header primitive, then continue app-wide token unification
    from legacy `--color-*` consumers toward canonical `--mp-*` / Skyframe token
    usage. The primitive should preserve the P29B-T5 restraint: top-anchored sky
    atmosphere that fades into the app surface, not a persistent full-page wash.
  - Sequencing:
    1. `P29B-T6A` - Create/reuse a shared Skyframe page-header/surface primitive
       and migrate Reports to consume it without changing report data, report
       semantics, or layout hierarchy. Apply to at most one additional low-risk
       route only if needed to prove reuse.
    2. `P29B-T6B` - Migrate shared legacy token consumers first, especially
       `SectionCard`, `StateViews`, `Timestamp`, and report-adjacent surfaces,
       keeping visual behavior equivalent or closer to Skyframe's medium-high
       contrast standard.
    3. `P29B-T6C` - Define the per-surface rollout checklist and add a guard
       against new raw hex / legacy `--color-*` usage after the migration
       baseline is clean, or start with a narrow allowlist warning during
       migration.
  - Hard constraints: frontend visual/token work only; no backend contract
    changes, no new read fields, no fabricated report coverage/provenance values,
    no changed report state semantics, no private-data exposure, no provider
    calls, no storage writes, no frontend financial math, no advice/order
    wording, and no broad app repaint in a single slice.
  - Status: `P29B-T6A` done 2026-06-19 by Claude A; Claude B visual/safety review
    PASS 2026-06-19 (independent connected `/reports` preview at 1024/1280/1440 in
    light + dark; computed wash/border/shadow/max-width identical to pre-migration,
    0px overflow, no console errors, no forbidden copy, sky stays surface-only).
    Codex B re-review not required (token/visual-only; no
    safety/privacy/semantics/read-contract/posture change) — informed for
    awareness; awaiting next-step confirmation. Deferred polish (non-blocking,
    carry to T6B): source the surface max-width from a `--skyframe-page-max` token
    instead of the JS literal default in `SkyframeSurface`. `P29B-T6B` is the next
    task.
  - `P29B-T6B` routing: assigned to Codex F for frontend token migration; Claude B
    visual/safety review required. Codex B review is not required unless the
    implementation changes product safety, privacy, report semantics,
    evidence-display rules, frontend read-contract boundaries, or cross-surface
    product posture.
  - `P29B-T6B` implementation status: done 2026-06-19 by Codex F; Claude B
    visual/safety review PASS 2026-06-19. Migrated shared/report-adjacent legacy token consumers
    (`SectionCard`, `StateViews`, `Timestamp`, plus the shared `SkyframeSurface`
    max-width default) from legacy `--color-*` / component literals toward
    canonical `--mp-*` / `--skyframe-*` tokens. Added `--skyframe-page-max` so
    the shared page frame width lives in the CSS token layer. Verified the
    requested shared/report-adjacent search area has no remaining
    `var(--color-*)` usage. No backend/read-field/report-state changes, no
    provider calls/storage writes, no frontend financial math, and no
    advice/order wording. Verification: `cd frontend && npm run typecheck`,
    `npm run lint -- --max-warnings 0`, `npm run build`, and `git diff --check`
    all passed. Browser preview not run because the slice is token/static and
    `/reports` may expose generated/private report content without explicit
    permission. Codex B re-review not required (visual/token-only; no
    product-safety/privacy/report-semantics/evidence-display/read-contract/
    cross-surface posture change). Deferred polish: consider `--mp-rule-2` for
    the `SectionCard` outer edge if light-mode contrast feels soft; migrate
    remaining retry-button font paths from `--font-family` to `--mp-font-sans`;
    optional connected-preview smoke when synthetic/private-safe conditions
    allow.
  - `P29B-T6C` routing: assigned to Codex F for the Skyframe per-surface rollout
    checklist and narrow raw-hex / legacy-token guard; Claude B visual/safety
    review required. Codex B review is not required unless the implementation
    changes product safety, privacy, report semantics, evidence-display rules,
    frontend read-contract boundaries, or cross-surface product posture.
  - `P29B-T6C` implementation status: done 2026-06-19 by Codex F; Claude B
    visual/safety/process review PASS 2026-06-19. Added the Skyframe per-surface rollout
    checklist to `docs/shared/frontend_design_change_playbook.md` and introduced
    the warning-only `cd frontend && npm run check:skyframe-tokens` guard. The
    guard tracks the current intentional legacy `var(--color-*)` baseline by
    file, warns if new files use legacy tokens or if legacy counts increase, and
    warns on raw hex outside `frontend/src/styles/globals.css`. No UI migration,
    backend/read-field/report-state changes, provider calls, storage writes,
    frontend financial math, or advice/order wording. Verification:
    `npm run check:skyframe-tokens` passed with no drift findings, and
    `git diff --check` passed. Claude B re-ran the guard and confirmed exit 0,
    warning-only behavior, and complete baseline/no drift. Codex B re-review not
    required (process/tooling-only; no product-safety/privacy/report-semantics/
    evidence-display/read-contract/cross-surface posture change). Deferred
    polish: scope the raw-hex regex to CSS-value contexts before promoting the
    guard to error; consider running the guard in CI as non-blocking during
    migration; add a one-line playbook note telling migrators to update the
    baseline map in the same PR that lowers a count.
  - Status: done. P29B-T6A, T6B, and T6C are reviewed PASS; P29B-T6 is closed.
  - `P29B-T6A` implementation: promoted the accepted P29B-T5B top-only Reports
    sky-header wash into a shared, route-agnostic `SkyframeSurface` primitive and
    migrated Reports to consume it — no report data, semantics, or layout
    hierarchy changed. Added `.skyframe-surface` rules to `globals.css` (the
    framed page surface + top-anchored `--skyframe-page-wash` that fades into the
    page by ~280px dark / ~360px light — atmosphere only, never a persistent
    full-page tint), with the dark/light wash, `--skyframe-page-rule`, and
    `--skyframe-section-shadow` values copied verbatim from the T5B Reports page
    frame so the result is visually identical. New
    `frontend/src/components/shared/SkyframeSurface.tsx` (typed React boundary +
    per-page max width; reads only `--skyframe-*` / `--mp-*`, imports nothing
    Reports-specific). `ReportsPage.tsx` now wraps content in
    `<SkyframeSurface className="mp-surface reports-skyframe">` and its local
    `styles.page` was removed; the existing `PageHeader` MP primitive is reused
    (not duplicated). Dropped the now-unused `--reports-page-wash` /
    `--reports-page-rule` from `.reports-skyframe`; kept `--reports-section-shadow`
    (still used by report components). Reuse boundary: the primitive owns only the
    page surface/wash; Reports-specific memo surfaces (rail/card/evidence/trust/
    action tokens) stay in `.reports-skyframe`. Did NOT migrate a second route or
    touch the sidebar/content top seam this slice (restraint — avoids broadening;
    the primitive is decoupled by construction and ready for T6B). Hard
    constraints honored: frontend/token-only, no backend/read-field/report-state
    changes, no fabricated values, no provider calls/storage/financial math, sky
    stays surface-only with contrast-safe accents. Verified: typecheck / lint
    (--max-warnings 0) / build / `git diff --check` clean; connected `/reports`
    smoke — the `.skyframe-surface` root computes the identical wash gradient,
    border color (`--mp-rule` dark / `#D6E1EC` light), shadow, 1320 max-width and
    space-5 padding as pre-migration in both themes; 0px horizontal overflow at
    1024/1280/1440 in light and dark; no console errors.
- `P29B-T7` - First non-Reports Skyframe rollout slice.
  - Owner: Codex F for frontend implementation; Claude B visual/safety review.
    Codex B only re-reviews if product safety, privacy, report semantics,
    evidence-display rules, frontend read-contract boundaries, or cross-surface
    product posture change.
  - Dependency: P29B-T6 closed.
  - Scope: apply the accepted Skyframe checklist and token guard to one
    non-Reports surface in a narrow, reversible slice. Start with a code-level
    route inventory and pick the lowest-risk useful surface before editing.
    Prefer a surface where the work is mostly shell/header/shared-token
    alignment; avoid Account Details private-data tables and any route that
    would require inspecting real account data.
  - Candidate priority: Trade Review or Dashboard route shell first, depending
    on which has the cleaner synthetic/demo-safe verification path. Do not touch
    Agent Console composer behavior, Account Details private data semantics,
    backend contracts, or provider/market/broker calls.
  - Acceptance criteria: route cites/uses Skyframe primitives or tokens where
    appropriate, preserves medium-high contrast in light/dark, keeps sky as
    atmosphere-only, passes the Skyframe token guard without new drift, and
    preserves all existing frontend read contracts and safety copy posture.
  - `P29B-T7A` implementation status: done 2026-06-19 by Codex F; Claude B
    visual/safety review PASS 2026-06-19. Route inventory selected `/trade-review` as the first
    non-Reports Skyframe rollout because it is a compact route shell, already
    uses MP primitives, has a safe idle state, and avoids private account tables,
    provider refresh behavior, and Agent Console composer behavior. Implemented
    the narrow shell-only change by wrapping `TradeReviewPage` in
    `SkyframeSurface` while preserving the existing 1280px max width, form/result
    behavior, request payloads, frontend read contracts, and safety copy. No
    backend/read-field/report-state changes, no provider/broker/market/LLM calls,
    no storage writes, no frontend financial math, and no broad repaint.
    Verification: `cd frontend && npm run check:skyframe-tokens`,
    `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, and
    `git diff --check` all passed. Browser smoke not run; no dev server was
    started and the implementation was a static route-shell wrapper change.
    Codex B re-review not required (visual/shell-only; no product-safety,
    privacy, report semantics, evidence-display, read-contract, or cross-surface
    posture change). Deferred polish: connected `/trade-review` smoke across
    success/loading/error/empty at 1024/1280/1440 light + dark when
    synthetic/private-safe conditions allow; keep phase commits scoped; consider
    sourcing the 1280 max width from a token in a later token-polish slice.
  - `P29B-T7B` routing: assigned to Codex F for the next route-shell rollout on
    `/dashboard`; Claude B visual/safety review required. Scope is route shell
    and shared Skyframe primitive/token alignment only. Do not change dashboard
    data panels, API calls, readiness semantics, Market Mood/economic-awareness
    semantics, provider/source labels, or private-data boundaries. Codex B review
    is not required unless product safety, privacy, read-contract boundaries,
    evidence/context semantics, or cross-surface product posture change.
  - `P29B-T7B` implementation status: done 2026-06-19 by Codex F; Claude B
    visual/safety review PASS 2026-06-19. Applied the accepted Skyframe
    route-shell treatment to `DashboardPage` by wrapping both the no-user and
    data-backed dashboard states in `SkyframeSurface` while preserving the
    existing 1280px max width and child ordering. No dashboard panel logic, API
    calls, readiness/source/freshness semantics, Market Mood/economic-awareness
    behavior, provider labels, safety copy, storage, or calculations changed. The
    top-level gap moves from `space-5` to `space-6` by shared primitive
    standardization. Verification:
    `cd frontend && npm run check:skyframe-tokens`, `npm run typecheck`,
    `npm run lint -- --max-warnings 0`, `npm run build`, and `git diff --check`
    all passed. Browser smoke not run because no synthetic/private-safe dashboard
    preview was available and the slice is a static route-shell wrapper change.
    Claude B re-ran the token guard and confirmed no new raw hex or legacy
    `--color-*` drift. Codex B re-review not required (visual/shell-only; no
    product-safety/privacy/read-contract/readiness-source-freshness semantics/
    cross-surface posture change). Deferred polish: connected `/dashboard` smoke
    across no-user/loading/success/error/synthetic-demo states at 1024/1280/1440
    light + dark when synthetic/private-safe conditions allow; confirm the
    `space-5` to `space-6` rhythm is right for the cockpit; consider sourcing the
    1280 max width from a token in a later token-polish slice.
  - `P29B-T7C` routing: assigned to Codex F for route-shell rollout on
    `/settings`; Claude B visual/safety review required. Scope is shell/primitive
    alignment only. Preserve all settings data behavior, user/session semantics,
    auth/security copy, forms, storage behavior, and route state. Do not touch
    broker connection, Account Details private data, Agent Console composer,
    provider calls, backend contracts, or other routes. Codex B review is not
    required unless product safety, privacy, auth/security semantics,
    read-contract boundaries, or cross-surface product posture change.
  - `P29B-T7C` implementation status: done 2026-06-19 by Codex F; Claude B
    visual/safety review PASS 2026-06-19. Applied the accepted Skyframe
    route-shell treatment to `SettingsPage` by replacing the outer `mp-surface`
    shell with `SkyframeSurface`, preserving the existing 1280px max width and
    `space-5` route rhythm via a shell style override. No settings section state,
    forms, `AppearanceControl`, user/session semantics, auth/security copy,
    storage behavior, provider/broker/market/LLM calls, backend/read fields, or
    frontend financial math changed. Verification:
    `cd frontend && npm run check:skyframe-tokens`, `npm run typecheck`,
    `npm run lint -- --max-warnings 0`, `npm run build`, and `git diff --check`
    all passed. Browser smoke not run because no synthetic/private-safe settings
    preview was needed for this static route-shell wrapper change. Claude B
    re-ran the token guard and confirmed no new raw hex or legacy `--color-*`
    drift. Codex B re-review not required (visual/shell-only; no product-safety,
    privacy, user/session or auth/security semantics, read-contract, or
    cross-surface posture change). Deferred polish: optional connected
    `/settings` smoke at 1024/1280/1440 light + dark; decide whether Settings
    preserving `space-5` while Dashboard standardizes to `space-6` needs a shared
    vertical rhythm token; consider sourcing the 1280 max width from a token.
  - `P29B-T7D` routing: assigned to Codex F for a consolidated synthetic/
    private-safe Skyframe smoke checkpoint across the accepted rollout routes:
    `/reports`, `/trade-review`, `/dashboard`, and `/settings`. Claude B
    visual/safety review required. Scope is verification/reporting only unless a
    tiny layout fix is needed and stays inside the existing shell treatment.
    Do not inspect real saved reports, real account data, generated private
    reports, logs, local DB contents, or provider payloads. If any route cannot
    be previewed with synthetic/private-safe data, record the blocker and do not
    force the smoke. Codex B review is not required unless product safety,
    privacy, read-contract boundaries, source/freshness semantics, evidence/
    report semantics, auth/security semantics, or cross-surface product posture
    change.
  - `P29B-T7D` checkpoint status: done 2026-06-19 by Codex F as a
    synthetic/private-safe frontend shell smoke. Checked `/reports`,
    `/trade-review`, Dashboard at the actual registered route `/`, and
    `/settings` at 1024/1280/1440 in light and dark via the app Appearance
    control. Findings: no horizontal overflow, each route rendered one
    `SkyframeSurface`, sky wash stayed surface/atmosphere-only, controls/status
    stayed outside sky-as-action use, medium-high shell separation held, and no
    unsafe advice/order/execution wording was detected in the shell states. The
    only browser console noise was the known React Router v7 future-flag warning.
    Verification: `cd frontend && npm run check:skyframe-tokens` and
    `git diff --check` passed. No code changed, so typecheck/lint/build and
    Claude B review were not required for this verification-only checkpoint.
    Connected/data-backed report and dashboard states were intentionally not
    forced because the current local preview path could expose real saved
    reports, account data, generated private reports, local DB contents, or
    provider payloads. Required next fixture: a reviewed synthetic/private-safe
    seed or mock layer that returns sanitized `/users`, dashboard panel, and
    report-thread payloads without real local DB/report/provider content.
  - `P29B-T7E` backend fixture status: blocker fixes implemented 2026-06-19 by
    Codex C; narrow Codex B contract/privacy re-review PASS. Added an explicitly
    gated `SkyframeFixtureMiddleware` overlay for connected Skyframe smoke runs. The
    overlay activates only when all gates are present: `POA_SKYFRAME_FIXTURES=1`,
    `APP_ENV` is local/dev/test-like, `X-Skyframe-Fixture: private-safe-v1`, and
    a valid `X-Local-Access-Token` checked with the same constant-time posture as
    the local access guard. Production-like `APP_ENV` values fail closed.
    Supported synthetic/private-safe paths are `/users`,
    `/users/{uid}/reports`, `/users/{uid}/reports/{threadId}`,
    `/users/{uid}/trade-reviews`, `/users/{uid}/risk-alerts`,
    `/users/{uid}/readiness`, `/users/{uid}/dashboard-account-summary`,
    `/users/{uid}/portfolio-contexts`, `/market-context/market-mood`,
    `/market-context/market-mood/detail`, and `/economic-calendar/events`.
    Fixture payloads use fixed obvious synthetic identifiers and do not echo
    incoming real-looking user/thread ids. Active smoke-owned unsupported GET
    requests under `/users/*`, `/market-context/*`, and `/economic-calendar/*`
    return a synthetic 404; active non-GET requests under those families return
    a synthetic 405. Neither path can fall through to real handlers, services,
    storage, or providers. Report fixtures use the canonical
    `portfolio_manager_agent` role, and focused tests validate every supported
    fixture payload against its canonical Pydantic response model. The overlay
    makes no DB, broker, provider, market-data, LLM, TradingAgents, or external
    calls and leaves normal endpoint behavior unchanged when any gate is absent.
    Verification: `cd backend && ./.venv/bin/python -m pytest
    tests/api/test_skyframe_fixtures.py -q` passed (`11 passed`); `cd backend &&
    ./.venv/bin/python -m pytest tests/api/test_skyframe_fixtures.py
    tests/api/test_reports.py tests/api/test_trade_review_workspace.py
    tests/api/test_market_context.py -q` passed (`94 passed`, `28` existing
    DB-gated skips).
    A broader run including `tests/api/test_economic_calendar.py` still showed
    the known local-cache sensitivity where provider-reference economic-calendar
    cache data can make older synthetic-only API assertions fail; this is
    unrelated to the fixture overlay and remains separate test debt.
  - `P29B-T7G` synthetic account-list fixture status: implemented 2026-06-19 by
    Codex C; Codex B contract/privacy review PASS 2026-06-19.
    Extended only the exact `GET /users/{uid}/accounts` fixture path with one
    fixed, obvious synthetic account conforming to canonical `AccountRead`. The
    response uses fixed synthetic account/user UUIDs, never echoes the incoming
    uid, and bypasses the real account service. Existing activation gates,
    production-like environment rejection, and fixture-owned synthetic 404/405
    boundaries remain unchanged. Account Details remains unsupported and fails
    closed through the existing fixture 404. Verification: focused fixture tests
    passed (`14 passed`); account API plus fixture tests passed (`14 passed`, `4`
    existing DB-gated skips); `git diff --check` passed.
  - `P29B-T7K-A` private-safe Dashboard fixture-state contract status:
    implemented 2026-06-19 by Codex C; Codex B contract/privacy review PASS
    2026-06-19.
    Added the fixture-only `X-Skyframe-Dashboard-State` selector with exact
    allowlisted values `unavailable`, `populated`, and `empty`. The selector is
    honored only after every existing `private-safe-v1` activation gate passes;
    a missing selector preserves the accepted unavailable/default payloads, and
    an unknown selector returns a synthetic 400 before any fixture-owned real
    route or service can run. The selected state is coordinated across trade
    reviews, risk alerts, readiness, Dashboard account summary, portfolio
    contexts, Market Mood, and economic-calendar reads. The account selector
    remains the same fixed synthetic `AccountRead` for every valid state.
    Populated payloads contain obvious synthetic labels, aggregate shape counts,
    analysis-only readiness, synthetic market context, and synthetic calendar
    rows without private financial values or real-looking provenance. Empty
    payloads are canonical successful responses with empty item collections and
    honest empty labels; Account Details remains unsupported. Tests validate all
    three states across every affected canonical Pydantic response model, fixed
    account behavior, default equivalence, no incoming-id echo, all activation
    gates, invalid-selector fail-closed behavior, real-service bypass, and the
    existing fixture 404/405 boundaries. Verification: focused fixture tests
    passed (`24 passed`); fixture plus trade-review workspace, Market Mood, and
    account API regressions passed (`107 passed`, `18` existing DB-gated skips);
    `git diff --check` passed. The broader run including economic-calendar API
    regressions reproduced the three previously documented local-cache-sensitive
    failures (`116 passed`, `18 skipped`, `3 failed`) where an existing
    provider-reference cache conflicts with older synthetic-only assertions;
    no fixture-state request failed. Connected browser smoke and all remaining
    T7K work remained explicitly out of scope until the recorded Codex B PASS.
  - `P29B-T7K-B` implementation status: complete 2026-06-19 by Codex F; Claude B
    visual/safety review PASS 2026-06-19. Added the dev-proxy-only
    `SKYFRAME_DASHBOARD_STATE` input in `frontend/vite.config.ts`; when present,
    Vite forwards it as `X-Skyframe-Dashboard-State` alongside the existing
    private-safe fixture and local-access headers. The input is not `VITE_`-
    prefixed, is never read by browser code, and preserves current behavior when
    absent. No Dashboard rendering, API type, response contract, calculation,
    copy, or state semantic changed. Connected fixture smoke covered Dashboard
    at `/` for `unavailable`, `populated`, and `empty`, each at
    1024/1280/1440 in light and dark. All 18 combinations rendered exactly one
    `SkyframeSurface`, had zero horizontal overflow, retained the fixed
    `Skyframe Demo User` and single synthetic account, showed honest state-
    specific content, exposed no currency values or opaque UUIDs, and introduced
    no unsafe wording. Visual checks confirmed the sky treatment remains
    atmospheric and controls/status/error states remain structurally distinct.
    Browser console output contained only the two known React Router future-flag
    warnings. The Skyframe token guard, typecheck, lint (`--max-warnings 0`),
    build, and `git diff --check` passed. No token, private data, provider
    payload, DB content, log, real report, broker/market/LLM service, or
    production fixture selector was exposed or used.
  - `P29B-T7K-C` hardening/documentation status: implemented 2026-06-19 by
    Codex B; contract/privacy review PASS 2026-06-19. Documented
    `SKYFRAME_FIXTURE_HEADER` and
    `SKYFRAME_DASHBOARD_STATE` as development-proxy-only, non-`VITE_` variables
    in `.env.example` and `frontend/README.md`. Confirmed the backend already
    enforces the exact `unavailable | populated | empty` allowlist after fixture
    activation, and extended focused tests so both an unknown value and an
    explicitly empty header fail closed with the synthetic 400 while an absent
    header retains the accepted unavailable default. Focused fixture tests passed
    (`25 passed`); frontend typecheck, lint, build, Skyframe token guard, and
    `git diff --check` passed. The production bundle contains none of the fixture
    variable or header names. The full backend suite reproduced only the seven
    previously documented unrelated failures (`1038 passed`, `122 skipped`,
    `3 deselected`, `7 failed`). P29B-T7K is closed.
  - `P29B-T7J` implementation status: done 2026-06-19 by Codex F; Claude B
    visual/safety review PASS 2026-06-19. Applied `SkyframeSurface` to
    `/market-context/market-mood`, preserving the 1320px maximum width,
    `space-5` rhythm, route hierarchy, hooks, source/freshness/availability
    semantics, and sentiment-context-only posture. Codex B re-review was not
    required because the slice was visual/shell-only; connected state smoke was
    deferred to the reviewed private-safe fixture path.
  - `P29B-T7H` implementation status: implemented 2026-06-19 by Codex F; Claude B
    visual/safety re-review PASS 2026-06-19. Replaced the `/market-data` page's outer
    flex-column wrapper with `SkyframeSurface`, preserving its 900px maximum
    width, `space-6` vertical rhythm, child order, controls, notices, and
    manual/mock source/freshness/availability semantics. Initial Claude B review
    BLOCKED dark-mode contrast for important source/freshness/limitation copy;
    Codex F fixed the route and directly used `MarketDataStatusPanel` text tones
    from legacy low-contrast `--color-text-muted`/secondary usage to
    contrast-safe MP text tokens. No API call, hook, state, response field,
    provider behavior, storage, or financial calculation changed. Verification:
    Skyframe token guard, typecheck, lint (`--max-warnings 0`), build, and
    `git diff --check` passed. Private-safe route smoke passed at
    1024/1280/1440 in dark mode after the fix: exactly one `SkyframeSurface`,
    900px computed max width, 24px (`space-6`) computed gap, zero horizontal
    overflow, contrast-safe semantic copy, and unchanged `manual/mock`,
    `market_quote`, provider-unavailable, and analysis-only messaging. Only the
    known React Router v7 future-flag warnings appeared. Codex B re-review not
    required (visual/token-only; no API/hook/state/provider/storage/calculation,
    source/freshness semantic, or safety-posture change). Status: accepted.
  - `P29B-T7I` implementation status: implemented 2026-06-19 by Codex F; Claude B
    visual/safety review PASS 2026-06-19. First ratcheted the accepted P29B-T7H
    Market Data token-guard baseline only (`MarketDataStatusPanel` 16 -> 8 and
    `MarketDataPage` 11 -> 8 legacy `--color-*` uses). Applied the shared
    Skyframe route shell to `/risk` with `SkyframeSurface`, preserving the
    existing 940px maximum width, `space-6` rhythm, route hierarchy, stub
    scenario controls, displayed states, deterministic/read-only/not-advice copy,
    and manual decision-support posture. Fixed route-local React border
    shorthand/longhand console warnings with visual-equivalent longhand styles
    and an inset stale-provenance edge; no risk semantics, copy meaning,
    hook/state-machine, backend/API, storage, provider/broker/market-data/LLM/
    TradingAgents call, or frontend financial calculation changed. Verification:
    Skyframe token guard, typecheck, lint (`--max-warnings 0`), build, and
    `git diff --check` passed. Private-safe `/risk` smoke in dark mode passed at
    1024/1280/1440: exactly one `SkyframeSurface`, 940px computed max width,
    24px (`space-6`) computed gap, zero horizontal overflow, scenario controls
    present, all eight scenario buttons clickable/selected via `aria-pressed`,
    deterministic/read-only/not-advice posture preserved, and no unsafe wording
    introduced. Only known React Router v7 future-flag warnings appeared; light
    mode smoke deferred to a future ephemeral-profile pass to avoid UI preference
    storage writes. Codex B re-review not required (visual/shell/style-stability
    only; no product-safety/privacy/contract/risk-semantics/posture change).
    Status: accepted.

## Coordination Checkpoint

Checkpoint status: P28A/P29A/P29B foundation was committed and pushed at
`800561c` before P29B-T3A. Current post-checkpoint worktree contains intentional
P29B-T3A/T3B changes only and should be committed/pushed before P29B-T4.

Known unrelated test debt:

- A full backend suite run by Claude E showed 7 failures in unrelated
  cash_balance / option_position / stock_position model-column tests,
  economic_calendar, and SnapTrade adapter short-call mapping tests.
- Claude E confirmed the same failures remain after stashing T3B files, so they
  are pre-existing and must not block P29B-T3 closeout.
- Recommended owner: Codex C, as a separate backend regression/maintenance task
  after the P29B-T3 checkpoint.

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
