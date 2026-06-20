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

Reference docs:

- `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_28A_SAVED_REVIEW_ARTIFACT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`
- `docs/codex-b-architecture/PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29C_PUBLIC_EVIDENCE_SOURCE_GOVERNANCE.md`
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

- `P29C-T0` - Public evidence source governance and founder decision.
  - Owner: Codex B and founder.
  - Architecture draft:
    `docs/codex-b-architecture/PHASE_29C_PUBLIC_EVIDENCE_SOURCE_GOVERNANCE.md`.
  - Current gate: approve the architecture, choose exactly one initial public
    evidence section/source category, and record permitted LLM, persistence,
    display, attribution, retention, and environment uses.
  - Status: architecture drafted 2026-06-19; founder/source-rights decision
    pending. No provider or backend implementation is authorized yet.
  - Next implementation owner after PASS: Codex C for P29C-T1, beginning with an
    offline fail-closed source-policy/fake-adapter contract. External calls remain
    out of scope until a separate approved P29C-T2 source slice.

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
