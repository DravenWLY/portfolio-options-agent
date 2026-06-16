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
