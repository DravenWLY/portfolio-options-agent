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

Reference docs:

- `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_28A_SAVED_REVIEW_ARTIFACT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`
- `docs/codex-b-architecture/PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29C_PUBLIC_EVIDENCE_SOURCE_GOVERNANCE.md`
- `docs/codex-b-architecture/PHASE_30A_GOLDEN_PATH_REVIEW_DESK_CONTRACT.md`
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

### Phase 30A - Golden Path Review Desk Prototype

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
