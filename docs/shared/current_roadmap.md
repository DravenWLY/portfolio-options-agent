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

### Phase 30A - Golden Path Review Desk Prototype

Codex A has shifted the product framing from a narrow "pre-trade review" surface
to a read-only specialist review desk for busy self-directed investors.

The product should not answer "Should I make this trade?" It should answer:

`What would I be ignoring if I acted manually now?`

P30A should stop horizontal expansion and make one complete loop feel real:

`select review account/scope -> enter proposed trade -> run deterministic review -> save evidence snapshot -> explicitly generate Agent Team briefing -> reopen the exact historical report`

What is already available:

- Trade Review supports stock/ETF and simple options review inputs.
- Portfolio-backed Trade Review records a backend-owned saved-source reference
  when reviewed scope metadata is available.
- Saved review artifacts persist immutable generation-time scope, caveats,
  freshness, and deterministic summary data.
- Agent Team report generation runs explicitly from a saved evidence package,
  not from current account state.
- Reports is the accepted analyst-memo surface, with saved scope, timestamps,
  deterministic provenance, Agent Team synthesis, and EDGAR company-profile
  attribution when reviewed evidence exists.
- Phase 29B Skyframe rollout and P29C EDGAR `public_company_profile` vertical
  slice are complete and reviewed.

What should happen next:

1. Use `docs/codex-b-architecture/PHASE_30A_GOLDEN_PATH_REVIEW_DESK_CONTRACT.md`
   as the P30A contract.
2. P30A is accepted as the first coherent Golden Path Review Desk Prototype.
   It is complete through connected private-safe smoke for one stock/ETF flow
   and one `cash_secured_put` flow. Backend spine, Agent Team briefing wording,
   Trade Review handoff, Report Detail briefing polish, read-only Reports
   fixtures, interactive fixture coverage, and browser smoke all passed their
   review gates.
3. The next recommended phase is P30B - Golden Path Prototype Hardening And
   Demo Readiness: DB-enabled integration tests for the saved-review/report
   generation path, fixture cleanup, stable demo seed path, and a founder-demo
   script for one stock/ETF flow plus one CSP/covered-call flow.
4. Dashboard expansion, new public evidence, new providers, Agent Console
   composer work, Account Details redesign, and broader Skyframe rollout should
   pause unless they directly unblock the golden path.

Architecture references:

- `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`
- `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_29C_PUBLIC_EVIDENCE_SOURCE_GOVERNANCE.md`
- `docs/codex-b-architecture/PHASE_30A_GOLDEN_PATH_REVIEW_DESK_CONTRACT.md`

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
