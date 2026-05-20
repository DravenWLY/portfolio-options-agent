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
9. Phase 17 TradingAgents/Public Research Evidence Adapter: async public ticker/company research evidence only.

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

## Missing ADRs

Recommended ADRs:

1. Agent-safe projection and LLM data minimization boundary.
2. Broker provider abstraction and SnapTrade-primary decision.
3. Market data provider abstraction and manual/mock-first decision.
4. TradeIntent as core schema/domain abstraction over strategy-specific tables.

## API and Data Model Uncertainties

- Portfolio snapshot actionability metadata now has an ADR and is implemented as the first Phase 16A contract/service slice before deterministic agent components produce polished account-specific outputs.
- Broker provider freshness may need fields such as provider plan mode, provider sync time, broker as-of time, endpoint source, and user confirmation state.
- Trade-review read schemas for frontend/API exposure remain deferred before the frontend trade-review workspace.
- Covered-call/CSP coverage/collateral netting is not deeply modelled yet.
- Broker activities/transactions are future layer only.

## Current Phase 17 / 18 Sequence

Phase 16A and Phase 16B are complete and archived in `docs/shared/completed_phases_log.md`.

Completed Phase 16 delivered:

- deterministic agent components for actionability, portfolio context, trade review explanation, freshness/guardrail, and report composition;
- the app-owned portfolio-aware agent-team orchestrator with stage order, actionability gate enforcement, context-envelope role compatibility, run/step mapping, and unavailable-state fallbacks;
- backend-only synthetic tests and no frontend route, DB persistence, TradingAgents import, real market provider call, LLM call, or broker action.

Phase 17 is now **TradingAgents/Public Research Evidence Adapter**. It remains optional, async, public ticker/company evidence only, and not the final portfolio-aware decision engine.

Phase 18 depends on:

- Phase 16 complete;
- typed sanitized trade-review read schema and forbidden-field tests;
- coverage/collateral caveat or modelling fix;
- real market data only before external paid beta or polished quote-current options review, not before local MVP demo.

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

1. Review Phase 17 TradingAgents/Public Research Evidence Adapter work for public-evidence-only boundaries.
2. Define minimum trade-review read schema requirements before Phase 18.
3. Keep public research/debate evidence visually and structurally subordinate to deterministic review and actionability.
4. Keep real market-data provider integration deferred until external paid beta or quote-current options review requires it.

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
