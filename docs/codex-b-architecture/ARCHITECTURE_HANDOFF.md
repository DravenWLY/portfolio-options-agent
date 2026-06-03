# Architecture Handoff for Codex B

## Current Architecture Summary

The app is layered around portfolio-aware trade review:

1. Portfolio system of record: users, accounts, broker/manual/CSV inputs, cash, stock/ETF positions, option positions, broker connections, broker accounts, sync runs, and freshness warnings.
2. Report/agent history: report threads, messages, agent runs, agent steps, snapshots, calculation versioning.
3. Frontend dashboard shell: portfolio dashboard, broker connection, market-data status, risk review, settings-like UI preferences.
4. Market data contracts: strategy-neutral quote, option contract, option quote, chain snapshot, freshness/actionability models, manual/mock provider.
5. TradeIntent foundation: stock/ETF/options proposed action models and validation.
6. Deterministic trade/risk engine: payoff, portfolio impact, risk rule integration, strategy wrappers, deterministic report.
7. Phase 16A deterministic agent components: actionability, portfolio context, trade review explanation, freshness/guardrail, and report composition.
8. Phase 16B portfolio-aware agent-team orchestrator: app-owned stage graph, role context envelopes, actionability enforcement, run/step persistence, and fallbacks.
9. Phase 18A/18B frontend-readiness contract and workspace expansion: sanitized deterministic trade-review read contract, first visible workspace boundary, frontend-read privacy guard unification, and deterministic report UI.
10. Phase 18C portfolio-backed workspace contract: backend-owned sanitized/manual portfolio context feeding the Trade Review Workspace without exposing raw private data.
11. Phase 17A TradingAgents/Public Research Evidence Adapter: async public ticker/company research evidence contracts only, optional and public-evidence-only.
12. Phase 19A Basic Portfolio-Aware LLM Agent Team + Analysis Console: app-owned orchestration boundary, mock LLM provider first, role-based analysis console, and sanitized portfolio evidence for portfolio-aware roles only.
13. Phase 19B Real LLM Provider Gate: backend-only, Google/Gemini-first candidate, mock-default provider resolver, prompt/output safety hardening, and safe rate-limit/quota fallback.
14. Phase 19C Agent-Team Evidence and Prompt Foundation: agent-safe deterministic evidence projection, role-specific prompt inputs, scenario coverage, and stricter prompt-boundary privacy controls.
15. Phase 20A Modern Portfolio Desk Frontend Integration: prototype-fidelity frontend shell/workspace direction using existing read-only backend contracts and clearly labeled placeholder surfaces.
16. Phase 20B/P20C Modern Portfolio Desk contracts and wiring: demo-labeled backend read contracts for dashboard/portfolio-context surfaces plus reviewed Dashboard, Agent Console, and Settings layout integration.
17. Phase 21A Realtime Agent Console contract draft: retained as a paused design reference after PM postponed further agentic/realtime expansion; no backend implementation or composer activation is authorized.
18. Phase 22A Market Data Evaluation Foundation: approved offline, provider-neutral, synthetic/replay-first market-data contract and scenario-test work; provider selection is reopened and commercial integration is not yet authorized.
19. Phase 20D Dashboard Information Architecture: docs-only planning gate completed; private account-detail display is approved in principle behind a backend display-label contract, privacy mode, and explicit freshness/provenance.
20. Phase 23A/23B Symbol Lookup / Instrument Reference Foundation: completed provider-neutral search/validation, broad Nasdaq-traded local refresh, uppercase autocomplete, browser-local recents, and offline fixture cleanup.
21. Phase 24A Economic Calendar Awareness Foundation: planned macro calendar path with synthetic contracts first, deterministic importance classification, opt-in FMP REST evaluation, last-good refresh, and Dashboard table; ticker/company news and agent ingestion remain separate later gates.

## Backend / Frontend Boundaries

Backend owns:

- Broker provider integration and secret handling.
- Database models/migrations.
- Portfolio normalization and summaries.
- Deterministic finance calculations.
- Market data contracts/provider interfaces.
- Trade review, risk, actionability, and agent-safe projections.

Frontend owns:

- User flows and rendering.
- Read-only dashboard cockpit.
- Loading/error/empty states.
- Accessibility and visual design.
- Clear labels separating broker snapshots, market quotes, deterministic calculations, and AI text.

Frontend must not:

- Call SnapTrade, brokers, market providers, LLM providers, or TradingAgents directly.
- Store brokerage/account/report/position data in localStorage/sessionStorage.
- Render order tickets, trade execution controls, broker disconnect/delete controls, or guaranteed-return language.

## Known Architectural Decisions

- `../TradingAgents` remains separate; this repo uses adapters and optional dependency boundaries only.
- SnapTrade is primary broker sync candidate; manual/CSV remains fallback.
- Broker portfolio freshness is distinct from market quote freshness.
- Market data contracts are provider-agnostic; real market providers are deferred.
- `TradeIntent` is the core abstraction; wheel/CSP/covered-call are not core schema foundations.
- Deterministic code calculates metrics; LLMs explain structured outputs.
- Agent-safe projection is required before LLM/agent paths receive trade-review report data.
- Portfolio Snapshot Actionability Policy is a backend-owned gate consumed by Phase 16 agent/orchestrator outputs. See `docs/codex-b-architecture/adr/0001-portfolio-snapshot-actionability-policy.md`.
- Portfolio Copilot is TradingAgents-inspired, not TradingAgents-centered. See `docs/codex-b-architecture/adr/0002-tradingagents-inspired-portfolio-agent-team.md`.
- Real market-data provider integration is not required for local MVP. Phase 22A replaces the Tradier-first production assumption with provider-neutral synthetic/replay evaluation and a bounded Alpaca Basic injected/mock-client mapping adapter for internal evaluation only. The commercial RFI/licensing track is parked until scale or external-display planning reopens it. Tradier is reference/prototyping-only unless later approved. REST snapshots remain preferred before any separately approved streaming work. See `docs/codex-b-architecture/adr/0003-market-data-timing-tradier-rest-snapshots.md`, `docs/codex-b-architecture/PHASE_22A_MARKET_DATA_EVALUATION_CONTRACT.md`, `docs/codex-b-architecture/PHASE_22A_EARLY_EVALUATION_PROVIDER_ASSESSMENT.md`, and `docs/codex-b-architecture/PHASE_22A_ALPACA_BASIC_EVALUATION_ADAPTER_CONTRACT.md`.
- Real LLM provider support is a backend-only explicit gate with Google/Gemini as the first candidate and mock provider as default. See `docs/codex-b-architecture/adr/0005-real-llm-provider-gate-google-first.md`.
- Live LLM/API smoke testing remains a separate future gate after Phase 19C. It must be backend-owned, explicit opt-in, synthetic-first, budget/rate-limit aware, and reviewed before any user-facing reliance.
- Realtime Agent Console HTTP/SSE is a paused proposed option only, pending future PM reactivation after founder agentic-AI study. See proposed, paused `docs/codex-b-architecture/adr/0007-agent-console-http-commands-sse-streaming.md`.
- Symbol lookup is implemented through the local personal-demo path. See `docs/codex-b-architecture/PHASE_23A_SYMBOL_LOOKUP_CONTRACT.md`.
- Economic calendar awareness is public macro context only and must not be treated as a trading signal. See `docs/codex-b-architecture/PHASE_24A_ECONOMIC_NEWS_AWARENESS_CONTRACT.md`.

## Missing ADRs

Recommended ADRs:

1. Agent-safe projection and LLM data minimization boundary.
2. Broker provider abstraction and SnapTrade-primary decision.
3. Market data provider abstraction and manual/mock-first decision.
4. TradeIntent as core schema/domain abstraction over strategy-specific tables.

## API and Data Model Uncertainties

- Portfolio snapshot actionability metadata now has an ADR and is implemented as the first Phase 16A contract/service slice before deterministic agent components produce polished account-specific outputs.
- Broker provider freshness may need fields such as provider plan mode, provider sync time, broker as-of time, endpoint source, and user confirmation state.
- Trade-review read schemas for frontend/API exposure are implemented through Phase 18C; future extensions should happen only through explicit backend contracts and tests.
- Covered-call/CSP coverage/collateral netting is not deeply modelled yet.
- Broker activities/transactions are future layer only.

## Current Phase 20B / 20C / 21A / 22A Sequence

Phases 16A, 16B, 17A, 18A, 18B, 18C, 19A, 19B, and 19C are complete and archived in `docs/shared/completed_phases_log.md`.

The active delivery focus is:

- **Phase 20B / 20C**: Phase 20C is the completed reviewed Modern Portfolio Desk frontend checkpoint; P20B-T5/T6 remain blocked on persistence/auth decisions.
- **Phase 20D**: `P20D-T0` through `P20D-T5` are complete: Dashboard content decision, private account-summary contract, cockpit cleanup, reviewed visual/content polish, Claude Design-derived refinements from existing contracts, and Stock Rover/Product B pressure-test cleanup. Portfolio Copilot complements serious research tools rather than replacing them, and the Dashboard remains a compact review-readiness cockpit. `P20D-T5` added no backend fields, endpoints, provider work, or new product surfaces.
- **Phase 22A**: `P22A-T1` synthetic/replay contracts, `P22A-T3` early-provider assessment, and `P22A-T4` backend-only Alpaca Basic injected/mock-client evaluation adapter are complete; no actual provider call, frontend display, agent ingestion, or production-provider decision is authorized.
- **Phase 23A / 23B / 24A**: symbol lookup is complete through local recents and offline fixture cleanup. Phase 24A remains macro-calendar-only and must preserve `is_trading_signal=false`; it must not become ticker/company news, a research feed, or an agent evidence path. Per-underlying earnings date is a separate narrow future review-context candidate for options flows, not part of generic Dashboard news.

**Phase 21A is paused**: Codex B's mock-first realtime Agent Console draft is
preserved for future discussion. If Codex A explicitly reactivates a scoped
agentic workflow slice, Claude E owns design/coding and Codex B reviews the
result. Codex C must not implement the agentic AI system workflow unless Codex A
later changes ownership explicitly, and Claude A must not enable the disabled
composer until a reviewed backend/frontend activation slice exists.

Phase 20A prototype-fidelity frontend work is complete. Phase 20B should now provide the missing sanitized backend reads behind its `demo · not yet connected` placeholder surfaces, one reviewed contract at a time.

Phase 22A is approved as a separate evaluation foundation:

- no real provider calls, credentials, live display, streaming, frontend
  changes, agent market-evidence ingestion, or TradingAgents work in the
  initial slice;
- preserve separate broker snapshot freshness, underlying quote freshness, and
  listed-option quote/chain freshness;
- require explicit data modes and IV/Greeks provenance;
- treat Alpaca Basic as the recommended first candidate only for a separately
  approved local/internal `limited_source`/`indicative`, analysis-only
  evaluation adapter; `P22A-T4` is now approved only for injected/mock-client
  mapping with no authorized external API call or credential path;
- retain the RFI template in
  `docs/codex-b-architecture/MARKET_DATA_PROVIDER_RFI.md` for later commercial
  selection; commercial outreach, licensing/pricing negotiation, and
  production-provider choice are parked.

Active frontend contract boundaries:

- `POST /trade-reviews/preview`
- `POST /trade-reviews/portfolio-preview`
- `POST /agent-team/trade-review-analysis/preview`

Completed Phase 20A surfaces and any Phase 20B frontend consumers must preserve:

- existing `TradeReviewWorkspaceRead` and `AgentTeamAnalysisConsoleRead` TypeScript/backend schema alignment;
- separate broker snapshot freshness and market quote freshness;
- deterministic facts vs agent commentary separation;
- no frontend financial calculations beyond rendering backend-provided values;
- no invented backend fields or fake connected data;
- no order-placement, cancellation, disconnect, execution, `safe to trade`, `ready to trade`, guaranteed-return, AI-picked, or `you should buy/sell` language;
- no raw holdings, raw positions, cash balances, buying power, account values, broker/provider ids, raw payloads, trade-journal entries, or account-specific thresholds in frontend contracts, fixtures, screenshots, or storage.

Phase 20B priorities:

1. Keep completed Phase 20A visual surfaces stable while replacing placeholder data through explicit typed backend contracts.
2. Keep every response display-ready, demo-labeled while synthetic, and recursively free of private brokerage/account/provider data.
3. Preserve separate broker snapshot freshness, market quote freshness, and agent-provider readiness concepts.
4. Let Claude A consume only reviewed endpoints and keep visible `demo · not yet connected` labels until data is truly persisted/real.
5. Keep completed demo-safe contracts for recent reviews, risk alerts, readiness, portfolio context, and dashboard account summary stable while the remaining blocked contracts are decided:

- reports list/detail read contracts require persistence ownership;
- profile/display-name contracts require auth/session and product decisions.

Phase 21A architecture draft:

- The Agent Console's approved five-zone visual layout is not a realtime chat system; its composer remains disabled during the PM pause.
- HTTP follow-up commands and SSE validated transcript progress are retained as an unapproved architecture option only.
- Keep the stateless `POST /agent-team/trade-review-analysis/preview` route unchanged for regression tests and demo output.
- Reuse existing safe projections and app-owned persistence primitives where semantics fit; do not store raw prompts, provider responses, traces, or private brokerage values.
- No Phase 21A or Phase 19D/live-provider work begins without explicit PM reactivation and review.

Phase 21A references:

- `docs/codex-b-architecture/PHASE_21A_REALTIME_AGENT_CONSOLE_CONTRACT.md`
- `docs/codex-b-architecture/adr/0007-agent-console-http-commands-sse-streaming.md`

Phase 19D / live LLM smoke testing remains future only:

- mock provider remains default;
- live Google/Gemini calls require explicit backend config, human-controlled local/deployment checks, budget/rate-limit handling, and a separate review gate;
- frontend requests must not choose provider, model, prompt text, credentials, freshness, actionability, or private portfolio metadata;
- deterministic trade review remains the source of financial metrics;
- provider failures must degrade to partial analysis, not block deterministic review.

Existing agent-team architecture references remain relevant:

- `docs/codex-b-architecture/PHASE_19A_LLM_AGENT_TEAM_CONTRACT.md`
- `docs/codex-b-architecture/adr/0004-basic-llm-agent-team-mock-provider-first.md`
- `docs/codex-b-architecture/PHASE_19B_REAL_LLM_PROVIDER_GATE_CONTRACT.md`
- `docs/codex-b-architecture/adr/0005-real-llm-provider-gate-google-first.md`

Recommended backend namespace remains `backend/app/services/agent_team/`. Keep `backend/app/services/agents/` for deterministic Phase 16 components. Phase 19+ consumes those components and safe projections instead of replacing them.

## Portfolio Snapshot Actionability Handoff

Detailed backend handoff: `docs/codex-c-backend/P16_T0_ACTIONABILITY_HANDOFF.md`.

Codex C should implement a narrow policy service and sanitized schema that accepts broker freshness, market quote freshness, source/provenance, provider status/error metadata, timestamp metadata, and optional confirmation state. It should emit top-level `review_actionability_status` values:

- `normal_review`
- `analysis_only`
- `manual_confirmation_required`
- `blocked_stale_broker_snapshot`
- `blocked_stale_market_quote`
- `blocked_unknown_freshness`
- `blocked_provider_error`

The response must preserve separate `broker_snapshot` and `market_quotes` metadata. It must not expose raw holdings, account values, cash balances, provider account ids, broker ids, raw provider payloads, secrets, trade journal entries, or account-specific thresholds.

Recommended first backend slice:

- Add policy enums/schemas.
- Add a pure service that evaluates status precedence with synthetic inputs.
- Add forbidden-field tests for the safe output shape.
- Add a preflight route only if existing routing patterns make it small; otherwise keep the first slice service/schema-only.
- Persist decision snapshots only when creating trade reviews, reports, agent runs, or agent steps; compute current preview status on demand.

## Security Assumptions

- SnapTrade userSecret is encrypted at rest and never returned to frontend.
- App-level SnapTrade credentials are backend-only.
- Provider ids and raw provider payloads should not appear in public schemas.
- Local dev access guard protects data routes.
- Real brokerage data must not be inspected by agents without explicit narrow permission.

## Where Implementation May Have Gotten Ahead of Architecture

- Backend phases have created substantial domain services before formal PM artifacts exist.
- Frontend shell exists before the full trade-review workspace and public research evidence contracts are finalized.
- Docs are large; context-efficient architecture briefs are now needed.

## Recommended First Tasks for Codex B

1. Preserve the completed `P22A-T4` evaluation boundary in `PHASE_22A_ALPACA_BASIC_EVALUATION_ADAPTER_CONTRACT.md`; do not authorize external smoke testing, frontend display, or agent consumption without a new PM decision.
2. Treat Phase 23A/23B symbol lookup as complete unless a new bug/follow-up is opened.
3. Treat the next Dashboard data-readiness priority as real-source account summary plus broker freshness mapping, if Codex A opens a backend task. This should precede persisted review history because fake-looking account aggregates undermine cockpit trust more than an empty history panel.
4. Treat `P20D-T5` as complete. Any further Dashboard visual work needs a new approved task and must keep unsupported panels classified as future-contract-needed or out of scope.
5. Plan display-rights-cleared REST quote snapshots for only the reviewed underlying and specific option before external-beta quote-current claims. Do not expose Alpaca `P22A-T4` evaluation output on the Dashboard.
6. Represent per-underlying earnings date as a future narrow review-context contract for options flows. Keep it separate from Phase 24A macro economic calendar work and do not broaden it into generic ticker/company news or research.
7. Keep Phase 20B/P20C frontend wiring behind Codex B-reviewed contracts and visible demo labels for synthetic responses.
8. Review P20B-T5 reports list/detail and P20B-T6 safe profile/display only after their persistence/auth decisions exist; they are lower priority than real-source account summary and broker freshness.
9. Keep Phase 21A realtime agent expansion and Phase 19D live LLM smoke testing paused or separately gated.
10. Retain vendor RFI comparison as parked reference material; do not expose a live/current UI claim or reopen commercial selection until Codex A approves it.

## Engineering Framework Sections To Apply First

Use `docs/shared/ENGINEERING_REVIEW_FRAMEWORK.md` sections on:

- System Design and Life of Request
- Architecture and Component Boundaries
- API Design
- Data Model and Persistence
- Data Format and Compatibility
- Reliability and Failure Handling
- Complexity Control
- Concurrency and Execution Model
- Documentation and Maintainability
- Evolution
