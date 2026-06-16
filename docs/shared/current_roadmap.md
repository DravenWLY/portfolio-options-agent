# Current Roadmap

Short context for routine Codex and Claude work. Prefer this file over the full
architecture document when a task only needs current direction.

## Product North Star

Portfolio Copilot is a broker-aware, portfolio-aware trade review workspace for
manual investors. It combines read-only broker state, market context,
deterministic trade-review/risk calculations, and bounded role-separated agent
commentary. It is TradingAgents-inspired, not TradingAgents-centered.

The product is manual decision support. It does not place orders, automate broker
actions, scrape brokers, bypass MFA, or present LLM output as financial advice.

## Current Product Posture

- Dashboard: compact cockpit for review readiness, account/market freshness, and
  approved context cards.
- Account Details: private broker-data readiness and selected-account detail,
  backed by opaque account refs and backend-owned display labels.
- Trade Review: deterministic review remains backend-owned; real-broker
  position-dependent feasibility is caveated unless the reviewed account/scope
  model explicitly supports it.
- Agent Console: read-only analysis report. Composer remains disabled. Agent
  evidence is sanitized and lossy by default.
- Market Mood / Economic Awareness: context only; not actionability, not risk
  rules, and not LLM evidence by default.

## Safety Boundary

- No automatic trading, order placement, cancellation, or execution UI.
- No broker scraping, credential storage, MFA bypass, or browser automation into
  broker sites.
- No guaranteed-return, "safe to trade", "ready to trade", or "you should
  buy/sell" wording.
- No raw holdings, raw positions, quantities, cash balances, buying power,
  account values, account/provider/broker IDs, raw provider payloads, prompts,
  provider traces, LLM traces, API keys, or access tokens in frontend contracts,
  prompts, docs, tests, reports, screenshots, or review summaries.
- Deterministic Python services own finance calculations. LLMs may explain
  approved structured outputs but must not invent metrics.

## Recently Completed

### Phase 27B - Account Details Stability

Completed through P27B-T22.

- Latest-sync membership is the boundary for current broker rows.
- Options now distinguish current/open, expired, closed, and missing-from-latest
  semantics.
- Account Details overview is a broker-readiness page, not an unreviewed
  holdings mirror.
- Selected-account detail can show private backend-owned display labels and
  optional opaque tax-lot display rows when available.
- Buying power, cash, and collateral labels are display-only and cannot drive CSP
  or covered-call feasibility yet.
- Agent Team evidence remains lossy and excludes account labels/refs, cash
  values, positions, option rows, tax lots, provider IDs, and raw payloads.
- Full-stack preview guidance for data-backed pages is documented in
  `docs/shared/agent_workflows.md`.

Architecture references:

- `docs/codex-b-architecture/PHASE_27A_ACCOUNT_DETAILS_SELECTED_ACCOUNT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`

### Phase 25A - Agentic Workflow Foundation

Active foundation, but gated and read-only.

- ADR 0008 accepted: app-owned safety spine, custom runner first, LangGraph/SSE/
  MCP/parallelism deferred and gated, OpenAI Agents SDK rejected, memory disabled.
- ADR 0009 accepted: machine role keys stay stable; user-facing display labels
  are backend-owned.
- Gemini and OpenAI provider adapters exist behind explicit backend opt-in; mock
  remains default.
- Agent Console route uses the reviewed `ReviewRunner` spine; composer remains
  disabled.

### Phase 26A - Market Mood Context

Functional internal-demo context.

- Backend/provider-reference Market Mood path works.
- Dashboard compact card and detail page consume reviewed backend contracts.
- Production/public display still requires source/rights review.

## Next Recommended Work

### Phase 29B - Public Agent Evidence

The Phase 29A saved-review foundation is now in place:

`select scope -> run review -> save source snapshot -> generate Agent Team report -> revisit the exact historical scope and analysis`

What is complete:

- Saved review snapshots persist immutable generation-time scope, caveats,
  freshness, and deterministic summary data.
- Agent Team report generation now runs on demand from a saved evidence package,
  not from current account state.
- Reports has been redesigned around saved analysis, with deterministic evidence
  and provenance moved into supporting sections.
- Guided-manual report generation is the accepted architecture recommendation:
  generation is an explicit user action, `generating` is frontend-only, and
  source snapshot time is distinct from Agent Team report-generation time.
- Backend report-generation timestamp and replace-only regeneration semantics
  are implemented; frontend P29A-T7 has passed visual/UX and
  contract/privacy/safety closeout.
- Phase 29B public-evidence backend and agentic wiring is complete through
  P29B-T3: generation-time public evidence is persisted/read back, public role
  projections are role-scoped, public analyst roles degrade honestly from
  unreviewed/unavailable evidence, and package-aware validation prevents citing
  unavailable public sections.

What should happen next:

- Commit and push the accepted P29B-T3A/T3B backend/agentic work.
- Start P29B-T4 frontend rich report optimization using stable synthetic public
  evidence sample payloads. Claude Design may be introduced for hierarchy and
  concept exploration; Stitch should wait until a direction is chosen and must
  consume reviewed mock data only.
- Track the 7 unrelated full-backend-suite failures as a separate Codex C
  backend maintenance/regression task; they are not blockers for P29B-T3.

Architecture references:

- `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`
- `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md`

### Deferred Scope Management

Account group/scope management from Phase 27C remains deferred until Codex A
makes a product decision. Do not build group CRUD or default review-account
preferences as part of Phase 29A.

## Paused / Deferred

- Realtime Agent Console and interactive composer: paused.
- Commercial market-data provider selection: parked.
- Economic Awareness frontend expansion: paused unless PM reactivates.
- Market Mood source/rights production review: required before public use.
- Full transaction/tax-lot reconstruction: deferred; do not infer tax lots from
  activities/orders without a new reviewed contract.

## Where History Lives

- Detailed completed work: `docs/shared/completed_phases_log.md`
- Prior active-plan snapshots:
  - `docs/shared/implementation_plan_archive_2026-06-03.md`
  - `docs/shared/implementation_plan_archive_2026-06-12.md`
- Human-readable recent changes: `docs/shared/CHANGELOG.md`
