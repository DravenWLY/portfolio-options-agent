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
- Real market-data provider integration is deferred for local MVP; Tradier REST snapshots are the preferred first real provider candidate before external paid beta. See `docs/codex-b-architecture/adr/0003-market-data-timing-tradier-rest-snapshots.md`.
- Real LLM provider support is a backend-only explicit gate with Google/Gemini as the first candidate and mock provider as default. See `docs/codex-b-architecture/adr/0005-real-llm-provider-gate-google-first.md`.
- Live LLM/API smoke testing remains a separate future gate after Phase 19C. It must be backend-owned, explicit opt-in, synthetic-first, budget/rate-limit aware, and reviewed before any user-facing reliance.

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

## Current Phase 20B Sequence

Phases 16A, 16B, 17A, 18A, 18B, 18C, 19A, 19B, and 19C are complete and archived in `docs/shared/completed_phases_log.md`.

The active delivery focus is **Phase 20B - Modern Portfolio Desk backend contracts**.

Phase 20A prototype-fidelity frontend work is complete. Phase 20B should now provide the missing sanitized backend reads behind its `demo · not yet connected` placeholder surfaces, one reviewed contract at a time.

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
5. Continue with the remaining backend-read contract candidates:

- persisted trade-review run list for Dashboard recent reviews;
- aggregate risk-alert/readiness summaries;
- standalone sanitized portfolio-context summary endpoint;
- reports list/detail read contracts;
- profile/display-name contract if the product wants personalized greeting/avatar surfaces.

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

1. Continue Phase 20B with P20B-T4 portfolio context enumeration/detail contracts.
2. Review P20B-T5 reports list/detail and P20B-T6 safe profile/display only after their backend contracts exist.
3. Keep Claude A frontend wiring behind Codex B-reviewed contracts and visible demo labels for synthetic responses.
4. Propose Phase 19D live LLM smoke testing only as a separate backend-owned, synthetic-only, explicit opt-in gate.
5. Keep real market-data provider integration, deep TradingAgents execution, and frontend research-evidence UI deferred until separately reactivated.

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
